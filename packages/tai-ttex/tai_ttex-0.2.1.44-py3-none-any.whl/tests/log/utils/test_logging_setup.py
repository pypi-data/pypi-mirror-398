from ttex.log import LOGGER_NAME, get_logging_config, initiate_logger
import pytest


def test_default_name():
    assert LOGGER_NAME


@pytest.mark.parametrize("disable_existing", [True, False])
def test_get_logging_config(disable_existing):
    name = "dummy_name"
    config = get_logging_config(name, disable_existing=disable_existing)
    assert name in config["loggers"]
    assert config["disable_existing_loggers"] == disable_existing


def test_initiate_logger():
    initiate_logger(log_level=10, logger_name="test_logger", disable_existing=False)
