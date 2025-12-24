import logging
from typing import Optional


class KeyFormatter(logging.Formatter):
    """
    Custom formatter that formats log records based on a specified key.
    This is useful for logging records that contain different types of data.
    """

    def __init__(
        self, key: str, fmt: str = "%(message)s", datefmt: Optional[str] = None
    ):
        """
        Initialize the KeyFormatter with a specific key and format.

        :param key: The key to format the log record.
        :param fmt: The format string for the log message.
        :param datefmt: Optional date format string.
        """
        super().__init__(fmt=fmt, datefmt=datefmt)
        self.key = key

    def format(self, record):
        """
        Format the log record using the specified key.

        :param record: The log record to format.
        :return: Formatted log message as a string.
        """
        if hasattr(record, self.key):
            record.msg = getattr(record, self.key)
        return super().format(record)
