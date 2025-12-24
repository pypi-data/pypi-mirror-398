from ttex.log.formatter import JsonFormatter
from ...utils.dummy_log_handler import DummyLogHandler
import logging
import json


def test_json_formatter():
    json_formatter = JsonFormatter(
        {
            "level": "levelname",
            "message": "message",
            "loggerName": "name",
            "processName": "processName",
            "processID": "process",
            "threadName": "threadName",
            "threadID": "thread",
            "timestamp": "asctime",
        }
    )
    json_handler = DummyLogHandler()
    json_handler.setFormatter(json_formatter)

    logger = logging.getLogger("test_json_formatter")
    logger.setLevel(logging.DEBUG)

    logger.addHandler(json_handler)
    logger.info("test")
    msg = json_handler.last_record.format_msg
    msg_dict = json.loads(msg)
    assert msg_dict["message"] == "test"
