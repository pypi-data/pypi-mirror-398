from ..handler.test_manual_rotating_file_handler import DummyHeader
from logging import makeLogRecord
from ttex.log.filter import KeyFilter


def test_filter_not_key():
    """
    Test that the filter does not allow records without the specified key.
    """
    filter = KeyFilter(key="test_key")
    record = makeLogRecord({"msg": "This is a test message"})
    assert not filter.filter(record)


def test_uuid():
    """
    Test that the filter allows records with the specified key and unique UUID.
    """
    filter = KeyFilter(key="test_key")
    dummy1 = DummyHeader(val=1, uuid="1234")
    record1 = makeLogRecord({"msg": "This is a test message", "test_key": dummy1})
    assert filter.filter(record1) is True

    # second time has same uuid, should be False
    record2 = makeLogRecord({"msg": "This is a test message", "test_key": dummy1})
    assert filter.filter(record2) is False

    dummy2 = DummyHeader(val=2, uuid="5678")
    record3 = makeLogRecord({"msg": "This is a test message", "test_key": dummy2})
    assert filter.filter(record3) is True  # Now it should be True again with new UUID
