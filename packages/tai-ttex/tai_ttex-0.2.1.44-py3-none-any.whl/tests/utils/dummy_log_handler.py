import logging
import logging.config
import copy
from ttex.log import initiate_logger


# This is a test handler so it is easy to capture what was logged
class DummyLogHandler(logging.Handler):
    def __init__(self, level=logging.NOTSET):
        self.record_log = []
        super().__init__(level)

    def emit(self, record):
        msg = self.format(record)
        self.last_record = record
        self.record_log.append(copy.copy(record))
        self.last_record.format_msg = msg


logging_config = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(filename)s - %(funcName)s - %(threadName)s - %(levelname)s - %(message)s"
        },
    },
    "handlers": {
        "console": {
            "()": DummyLogHandler,
            "level": "DEBUG",
            "formatter": "default",
        },
        "root_console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
    },
    "loggers": {
        "DefaultLogger": {
            "level": "DEBUG",
            "handlers": ["console"],
        },
    },
    "root": {
        "level": "DEBUG",
        "handlers": ["root_console"],
    },
}

initiate_logger(
    log_level=10, logger_name="DefaultLogger", logging_config=logging_config
)


logger = logging.getLogger("DefaultLogger")
dummy_log_handler = logger.handlers[0]
