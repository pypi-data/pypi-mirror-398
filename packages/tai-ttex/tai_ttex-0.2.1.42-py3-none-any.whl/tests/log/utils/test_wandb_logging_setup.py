from ttex.log.utils.wandb_logging_setup import (
    setup_wandb_logger,
    _get_wandb_logger,
    teardown_wandb_logger,
    _get_wandb_handler,
    log_wandb_init,
    log_wandb_artifact,
    get_wandb_logger,
)
from ttex.log.handler import WandbHandler
import logging
import pytest
import os
import shutil
import wandb


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
    if wandb.run is not None:
        wandb.finish()
    shutil.rmtree("wandb", ignore_errors=True)


def test_get_wandb_logger():
    wandb_logger = _get_wandb_logger(name="wandb_logger0")
    assert wandb_logger is None
    wandb_logger = logging.getLogger("wandb_logger0")
    wandb_logger._wandb_setup = True  # type: ignore[attr-defined]
    assert _get_wandb_logger(name="wandb_logger0") is wandb_logger
    wandb_logger._wandb_setup = False  # type: ignore[attr-defined]


def test_get_wandb_handler():
    wandb_handler = _get_wandb_handler(name="wandb_logger0")
    assert wandb_handler is None
    wandb_logger = logging.getLogger("wandb_logger0")

    # Manually add multiple handlers including a WandbHandler
    console_handler = logging.StreamHandler()
    file_handler = logging.FileHandler("test.log")
    wandb_handler_instance = WandbHandler()
    wandb_logger.addHandler(console_handler)
    wandb_logger.addHandler(file_handler)
    wandb_logger.addHandler(wandb_handler_instance)

    wandb_logger._wandb_setup = True  # type: ignore[attr-defined]
    wandb_handler = _get_wandb_handler(name="wandb_logger0")
    assert wandb_handler is not None
    assert isinstance(wandb_handler, WandbHandler)
    wandb_logger._wandb_setup = False  # type: ignore[attr-defined]

    # remove handlers again to clean up
    wandb_logger.removeHandler(console_handler)
    wandb_logger.removeHandler(file_handler)
    wandb_logger.removeHandler(wandb_handler_instance)


def test_setup_teardown_wandb_logger():
    wandb_logger = setup_wandb_logger(name="wandb_logger1", snapshot=False)
    assert wandb_logger is not None
    assert wandb_logger.name == "wandb_logger1"
    assert getattr(wandb_logger, "_wandb_setup", None) is True

    # Calling setup again should not create a new handler
    wandb_logger_2 = setup_wandb_logger(name="wandb_logger1", snapshot=False)
    assert wandb_logger is wandb_logger_2

    assert len(wandb_logger.handlers) == 1  # Only one WandbHandler
    wandb_handler = wandb_logger.handlers[0]
    assert isinstance(wandb_handler, WandbHandler)

    # set a run to test logging
    wandb_handler.run = WandbHandler.wandb_init(
        run_config={"dummy": "test_setup_teardown_wandb_logger"}, project="ci-cd"
    )
    assert wandb_handler.run is not None
    assert wandb_handler.run.settings.run_mode == "offline-run"

    wandb_logger.info("This is a test log message.")

    teardown_wandb_logger(name="wandb_logger1")
    assert getattr(wandb_logger, "_wandb_setup", None) is False
    assert len(wandb_logger.handlers) == 0  # Handlers should be removded
    assert wandb_handler.run is None  # Run should be finished
    # Teardown again to ensure no errors occur
    teardown_wandb_logger(name="wandb_logger1")
    assert getattr(wandb_logger, "_wandb_setup", None) is False
    assert len(wandb_logger.handlers) == 0  # Still no handlers
    assert wandb_handler.run is None  # Still no run


def test_log_wandb_init():
    wandb_logger = setup_wandb_logger(
        name="wandb_logger2", project="ci-cd", group="test_group", snapshot=False
    )

    run_config = {"param1": 10, "param2": "value"}
    run = log_wandb_init(
        run_config=run_config,
        logger_name="wandb_logger2",
    )
    assert run is not None

    wandb_handler = _get_wandb_handler(name="wandb_logger2")
    assert wandb_handler is not None
    assert wandb_handler.run is run
    assert wandb_handler.project == "ci-cd"
    assert wandb_handler.group == "test_group"

    wandb_logger.info("This is a test log message after wandb init.")
    teardown_wandb_logger(name="wandb_logger2")


def test_log_wandb_artifact():
    setup_wandb_logger(
        name="wandb_logger3", project="ci-cd", group="test_group", snapshot=False
    )
    run_config = {"param1": 10, "param2": "value"}
    run = log_wandb_init(
        run_config=run_config,
        logger_name="wandb_logger3",
    )
    assert run is not None

    # Create a temporary file to log as an artifact
    temp_file_path = os.path.join("/tmp", "test_artifact.txt")
    with open(temp_file_path, "w") as f:
        f.write("This is a test artifact.")

    artifact = log_wandb_artifact(
        artifact_name="test_artifact",
        local_path=temp_file_path,
        artifact_type="test_type",
        description="Test artifact logging",
        logger_name="wandb_logger3",
    )
    assert artifact is not None
    assert artifact.name == f"test_artifact_{run.id}"

    teardown_wandb_logger(name="wandb_logger3")

    os.remove(temp_file_path)


def test_public_get_wandb_logger():
    assert get_wandb_logger(name="wandb_logger4") is None
    wandb_logger = setup_wandb_logger(
        name="wandb_logger4", project="ci-cd", group="test_group", snapshot=False
    )
    assert get_wandb_logger(name="wandb_logger4") is None  # No run yet

    run_config = {"param1": 10, "param2": "value"}
    run = log_wandb_init(
        run_config=run_config,
        logger_name="wandb_logger4",
    )
    assert run is not None

    retrieved_logger = get_wandb_logger(name="wandb_logger4")
    assert retrieved_logger is wandb_logger

    teardown_wandb_logger(name="wandb_logger4")
