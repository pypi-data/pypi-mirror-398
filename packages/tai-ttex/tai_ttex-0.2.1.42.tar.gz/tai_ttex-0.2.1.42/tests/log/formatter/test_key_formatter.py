from ttex.log.formatter import KeyFormatter
from ...utils.dummy_log_handler import DummyLogHandler
import logging


def test_key_format():
    key_formatter = KeyFormatter(key="test_key")

    record = logging.makeLogRecord({"msg": "test", "test_key": 13})
    formatted_message = key_formatter.format(record)
    assert formatted_message == str(13)


def test_key_formatter():
    key_formatter = KeyFormatter(key="test_key")
    dummy_handler = DummyLogHandler()
    dummy_handler.setFormatter(key_formatter)

    logger = logging.getLogger("test_key_formatter")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(dummy_handler)

    logger.info("This is a test message", extra={"test_key": 13})
    # Check if the last record in the dummy handler matches the expected output
    # # The last record should have the formatted message as "13"
    assert dummy_handler.last_record.format_msg == "13"
