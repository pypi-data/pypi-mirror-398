import os
import sys
import json
import platform
import subprocess
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, List
import shlex


def run_cmd(cmd: str, parse: str = "raw", split_char=":", filter_fn=None) -> dict:
    try:
        # shlex is for input sanitation
        output = subprocess.check_output(shlex.split(cmd), text=True).strip()

        if parse == "lines":
            lines = output.splitlines()
            if filter_fn:
                lines = [line for line in lines if filter_fn(line)]
            return {"success": True, "lines": lines}
        elif parse == "kv":
            result = {}
            for line in output.splitlines():
                if split_char in line:
                    k, v = line.split(split_char, 1)
                    result[k.strip()] = v.strip()
            return {"success": True, "data": result}

        else:  # raw
            return {"success": True, "output": output}

    except subprocess.CalledProcessError as e:
        return {"success": False, "error": str(e), "returncode": e.returncode}


def get_python_info():
    return {
        "python_version": sys.version,
        "executable": sys.executable,
        "packages": run_cmd("pip freeze", parse="kv", split_char="=="),
    }


def get_os_info():
    return {
        "os": platform.system(),
        "os_release": platform.release(),
        "os_version": platform.version(),
        "platform": platform.platform(),
        "kernel": run_cmd("uname -a"),
        "distro": run_cmd("cat /etc/os-release", parse="kv", split_char="="),
    }


def get_cpu_info():
    return {"cpu": run_cmd("lscpu", parse="kv"), "num_cores": os.cpu_count()}


def get_memory_info():
    return {"memory": run_cmd("free -h", parse="lines")}


def get_gpu_info():
    if shutil.which("nvidia-smi"):
        return {"gpu": run_cmd("nvidia-smi", parse="lines")}
    elif shutil.which("rocm-smi"):
        return {"gpu": run_cmd("rocm-smi", parse="lines")}
    elif shutil.which("lspci"):
        return {
            "gpu": run_cmd(
                "lspci",
                parse="lines",
                filter_fn=lambda line: any(
                    s in line.lower() for s in ("vga", "3d", "2d")
                ),
            )
        }
    else:
        return {"gpu": "No GPU information available"}


def get_compiler_info():
    return_dict = {}
    if shutil.which("gcc"):
        return_dict["gcc"] = run_cmd("gcc --version", parse="lines")
    if shutil.which("g++"):
        return_dict["g++"] = run_cmd("g++ --version", parse="lines")
    if shutil.which("clang"):
        return_dict["clang"] = run_cmd("clang --version", parse="lines")
    return return_dict


def get_env_vars(sensitive_keys=None):
    env_vars = dict(os.environ)
    if sensitive_keys:
        for key in sensitive_keys:
            if key in env_vars:
                env_vars[key] = "<REDACTED>"
    return env_vars


def check_git():
    if not shutil.which("git"):
        return False
    try:
        subprocess.check_output(
            ["git", "rev-parse", "--is-inside-work-tree"],
            text=True,
            stderr=subprocess.DEVNULL,  # Suppress error output
        )
        return True
    except subprocess.CalledProcessError:
        return False


def get_git_info():
    if check_git():
        return {
            "in_repo": run_cmd("git rev-parse --is-inside-work-tree"),
            "branch": run_cmd("git rev-parse --abbrev-ref HEAD"),
            "commit": run_cmd("git rev-parse HEAD"),
            "remote": run_cmd("git remote -v"),
        }
    else:
        return {"in_repo": False}


def get_conda_info():
    if os.environ.get("CONDA_DEFAULT_ENV"):
        return {
            "conda_env": os.environ["CONDA_DEFAULT_ENV"],
            "conda_info": run_cmd("conda info --json"),
            "conda_list": run_cmd("conda list --export"),
        }
    return {}


def get_virtualenv_info():
    return {"virtualenv": os.environ.get("VIRTUAL_ENV", None)}


def get_installed_apt_packages():
    if shutil.which("dpkg"):
        return run_cmd("dpkg -l", parse="lines")
    return "<dpkg not available>"


def capture_snapshot(
    output_path: Optional[str] = None,
    extra_info: Optional[Dict] = None,
    extra_sensitive_keys: Optional[List[str]] = None,
):
    sensitive_keys = [
        "DOCKER_USER_NAME",
        "DOCKER_PWD",
        "GPG_KEY",
        "WANDBOX_API_KEY",
        "DOCKERHUB_TOKEN",
        "DOCKERHUB_USERNAME",
        "CID_PAT",
    ]
    if extra_sensitive_keys:
        sensitive_keys.extend(extra_sensitive_keys)
        sensitive_keys = list(set(sensitive_keys))

    snapshot = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "python": get_python_info(),
        "os": get_os_info(),
        "cpu": get_cpu_info(),
        "memory": get_memory_info(),
        "gpu": get_gpu_info(),
        "compilers": get_compiler_info(),
        "env_vars": get_env_vars(sensitive_keys),
        "git": get_git_info(),
        "conda": get_conda_info(),
        "virtualenv": get_virtualenv_info(),
        "apt_packages": get_installed_apt_packages(),
        "custom_info": extra_info or {},
    }
    if output_path:
        output_file = Path(output_path)
        output_file.write_text(json.dumps(snapshot, indent=2))
    return snapshot
