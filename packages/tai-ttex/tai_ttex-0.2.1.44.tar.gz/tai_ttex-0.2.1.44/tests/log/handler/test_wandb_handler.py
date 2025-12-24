import logging
from ttex.log.handler import WandbHandler
import os
import shutil
from importlib.metadata import version
from typing import Dict, Optional
from wandb.sdk import launch
import wandb
import pytest
import os.path as osp


@pytest.fixture(autouse=True)
def online_mode_env_var():
    if not os.environ.get("WANDB_CONFIG", None):
        prev_mode = os.environ.get("WANDB_MODE", "online")
        os.environ["WANDB_MODE"] = "offline"
    yield
    if not os.environ.get("WANDB_CONFIG", None):
        os.environ["WANDB_MODE"] = prev_mode


@pytest.fixture(autouse=True, scope="module")
def cleanup_wandb_dirs():
    yield
    shutil.rmtree("wandb", ignore_errors=True)


def test_wandb_init():
    run = WandbHandler.wandb_init(
        run_config={"dummy": "test_wandb_init"}, project="ci-cd"
    )
    assert run.settings.run_mode == "offline-run"
    run.finish()


@pytest.mark.parametrize("art_is_file", [True, False])
def test_create_wandb_artifact(art_is_file):
    run = wandb.init(project="ci-cd", config={})

    folder = osp.join("/tmp", "art_test")
    os.makedirs(folder, exist_ok=True)
    if not art_is_file:
        # Create a directory as the artifact
        temp_art_path = os.path.join(folder, "test_artifact_dir")
        os.makedirs(temp_art_path, exist_ok=True)
        folder = temp_art_path
    # Create a file inside the directory
    temp_file_path = os.path.join(folder, "file_in_dir.txt")
    with open(temp_file_path, "w") as f:
        f.write("This is a file inside the artifact directory.")
    if art_is_file:
        temp_art_path = temp_file_path

    artifact = WandbHandler.create_wandb_artifact(
        run=run,
        artifact_name="test_artifact",
        local_path=temp_art_path,
        artifact_type="test_type",
        description="Test artifact creation",
    )
    assert artifact is not None
    assert artifact.name == f"test_artifact_{run.id}"

    # Check that the artifact contains the file
    files = [f.name for f in artifact.manifest.entries.values()]
    assert len(files) == 1
    if art_is_file:
        assert files[0] == f"test_artifact_{run.id}"
    else:
        assert files[0] == osp.join(f"test_artifact_{run.id}", "file_in_dir.txt")
    run.finish()
    shutil.rmtree(osp.join("/tmp", "art_test"), ignore_errors=True)


def test_log_snapshot():
    run = wandb.init(project="ci-cd", config={})

    artifact = WandbHandler.log_snapshot(
        run=run,
        extra_info={"test_key": "test_value"},
        extra_sensitive_keys=["HOSTNAME"],
    )
    assert artifact is not None
    assert artifact.name == f"system_snapshot_{run.id}"

    # Check that the artifact contains the snapshot file
    files = [f.name for f in artifact.manifest.entries.values()]
    assert len(files) > 0

    assert osp.exists(f"snapshot_{run.id}.json")

    run.finish()
    os.remove(f"snapshot_{run.id}.json")


@pytest.mark.parametrize("snapshot", [True, False])
def test_wandb_handler_init_close(snapshot, config: Optional[Dict] = None):
    # Update config
    ttex_version = version("tai_ttex")
    config_override = {"repo": "ttex", "version": ttex_version}

    # Iff there is a config, we are testing online
    if not config:
        wandb_args = {
            "project": "ci-cd",
            "config": config_override,
        }
    else:
        config.update(config_override)
        # No project here because that is determined at launch
        wandb_args = {"config": config}

    run = wandb.init(**wandb_args)

    handler = WandbHandler(snapshot=snapshot)

    logger = logging.getLogger(f"test_wandb_handler_{snapshot}")
    logger.setLevel(logging.DEBUG)

    logger.addHandler(handler)

    handler.run = run

    for i in range(3):
        logger.info({"test": i})
    handler.close()
    assert run._is_finished
    assert handler._run is None
    if snapshot:
        assert osp.exists(f"snapshot_{run.id}.json")
        os.remove(f"snapshot_{run.id}.json")


def test_log_without_run():
    handler = WandbHandler()
    logger = logging.getLogger("test_wandb_handler_no_run")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    for i in range(3):
        logger.info({"test": i})
    handler.close()


def test_metrics_setup():
    run = wandb.init(project="ci-cd", config={})

    custom_metrics = {"env/step": ["env/*"]}
    handler = WandbHandler(snapshot=False, custom_metrics=custom_metrics)
    handler.run = run
    logger = logging.getLogger("test_wandb_handler")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    for env in range(3):
        for step in range(10):
            logger.info({f"env/r/{env}": env * step, "env/step": step})
    handler.close()


def test_without_run():
    logger = logging.getLogger("test_wandb_handler")
    logger.info({"test": 5}, extra={"step": 10})


def test_with_non_dict():
    logger = logging.getLogger("test_wandb_handler")
    logger.warning("i encountered an error")


if __name__ == "__main__":
    # This is to test launch from wandb
    if not os.environ.get("WANDB_CONFIG", None):
        raise RuntimeError("Needs to be launched from wandb")
    run_config = launch.load_wandb_config()
    test_wandb_handler_init_close(run_config)
