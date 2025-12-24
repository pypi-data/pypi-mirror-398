"""Convenient setup for python logging module"""

import logging
import logging.config
import copy
from typing import cast, Optional, Dict

LOGGER_NAME = "DefaultLogger"


def get_logging_config(
    logger_name: str, disable_existing: Optional[bool] = True
) -> Dict:
    """
    Get a default logging configuration dictionary

    Args:
        * logger_name: str
            The name of the logger to set up
        * disable_existing: bool (optional) default=True
            Whether to disable existing loggers

    Returns:
        * config_dict: dict
            A dictionary containing the logging configuration
    """
    config_dict = {
        "version": 1,
        "disable_existing_loggers": disable_existing,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(filename)s"
                + " - %(funcName)s - %(threadName)s - %(levelname)s - %(message)s"
            },
        },
        "handlers": {
            "console": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "formatter": "default",
            },
            "root_console": {
                "level": "WARNING",
                "class": "logging.StreamHandler",
                "formatter": "default",
            },
        },
        "loggers": {
            logger_name: {
                "level": "WARNING",
                "handlers": ["console"],
            }
        },
        "root": {
            "level": "WARNING",
            "handlers": ["root_console"],
        },
    }
    return config_dict


def initiate_logger(
    log_level: int,
    logger_name: Optional[str] = None,
    disable_existing: Optional[bool] = True,
    logging_config: Optional[Dict] = None,
):
    """
    Convenience function to set the logging level of a given logger

    Args:
        * log_level: int
            The log level to set to in [0,10, 20, 30, 40, 50]
        * logger_name: str (optional) default=None
            The name of the logger to set up
        * disable_existing: bool (optional) default=True
            Whether to disable existing loggers
        * logging_config: dict  (optional) default=None
            A dictionary containing the logging configuration

    For more information on log levels see
    https://docs.python.org/3/library/logging.html#logging-levels
    If given log level is not recognised, set to default
    """

    if not logger_name:
        logger_name = LOGGER_NAME
    if not logging_config:
        logging_config = get_logging_config(logger_name, disable_existing)
    config = cast(dict, copy.deepcopy(logging_config))

    assert logger_name in config["loggers"]

    chosen_level = logging.getLevelName(log_level)
    chosen_level_exists = chosen_level != f"Level {log_level}"
    if chosen_level_exists:  # Level exists - so change accordingly
        config["loggers"][logger_name]["level"] = chosen_level
        # TODO: potential debugging help for level issues
        # handler_names = config["loggers"][logger_name]["handlers"]
        # handler_levels = [
        #    handler["level"]
        #    for handler_name, handler in logging_config["handler"].items()
        #    if handler_name in handler_names
        # ]

    logging.config.dictConfig(config)

    logger = logging.getLogger(logger_name)
    logger.info(f"Set logging config to {config}")
    if chosen_level_exists:
        logger.debug(f"Set up log level for {log_level}")
    else:
        logger.error(
            f"Chosen log level {log_level} does not exist. "
            + "Logger level remains at "
            + f"{logger.getEffectiveLevel()}. Options are listed "
            + "here https://docs.python.org/3/library/logging.html#logging-levels"
        )
