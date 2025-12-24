import logging
from ttex.log.handler import ManualRotatingFileHandler
import os.path as osp
import pytest
from typing import Optional
import shutil
from uuid import uuid4


@pytest.fixture(autouse=True, scope="module")
def remove_test_files():
    shutil.rmtree("test_dir", ignore_errors=True)

    yield  # run the tests

    # Cleanup after tests
    shutil.rmtree("test_dir", ignore_errors=True)


class DummyRecord:
    def __init__(self, val: int):
        self.val = val

    def __str__(self):
        return f"DummyRecord(val={self.val})"


class DummyHeader(DummyRecord):
    def __init__(
        self, val: float, filepath: Optional[str] = None, uuid: Optional[str] = None
    ):
        self.val = val
        if filepath is not None:
            self._filepath = filepath
        else:
            # Default filepath for testing
            self._filepath = osp.join("test_dir", "header_file.txt")
        self._uuid = str(uuid4()) if uuid is None else uuid

    def __str__(self):
        return f"DummyHeader(val={self.val})"

    @property
    def filepath(self) -> str:
        return self._filepath

    @property
    def uuid(self) -> str:
        # Generate a unique UUID for testing purposes
        return self._uuid


def test_should_rollover():
    """
    Test the shouldRollover method of ManualRotatingFileHandler.
    It should return True when a Header record with a new filepath is logged.
    """
    handler = ManualRotatingFileHandler(
        filepath=osp.join("test_dir", "test_file.txt"), mode="a"
    )

    with pytest.raises(AssertionError):
        # Should raise an assertion error because the first message should be a Header
        record = logging.makeLogRecord({"msg": DummyRecord(42)})
        handler.shouldRollover(record)
    assert handler.current_filepath is None
    assert handler.next_filepath is None

    # First Header record, should not trigger rollover
    header1 = logging.makeLogRecord({"msg": DummyHeader(3.14)})
    assert not handler.shouldRollover(header1)
    assert handler.current_filepath is not None
    assert handler.next_filepath is None

    # Second Header record with the samefilepath, should not trigger rollover
    header2 = logging.makeLogRecord({"msg": DummyHeader(2.71)})
    assert not handler.shouldRollover(header2)
    assert handler.current_filepath is not None
    assert handler.next_filepath is None

    # Third Header record with a new filepath, should trigger rollover
    header3 = DummyHeader(1.41, filepath=osp.join("test_dir", "new_header_file.txt"))
    assert handler.shouldRollover(logging.makeLogRecord({"msg": header3}))
    assert handler.current_filepath is not None
    assert handler.next_filepath == header3.filepath

    assert not osp.exists(handler.baseFilename)
    handler.current_filepath = None
    handler.next_filepath = None

    handler.close()


def test_rollover_key():
    """
    Test the rollover key functionality of ManualRotatingFileHandler.
    It should correctly set the current and next filepaths based on the Header record.
    """
    handler = ManualRotatingFileHandler(
        filepath=osp.join("test_dir", "test_file.txt"), mode="a", key="test_key"
    )
    header1 = logging.makeLogRecord({"msg": "test", "test_key": DummyHeader(3.14)})
    assert not handler.shouldRollover(header1)
    assert handler.current_filepath is not None
    assert handler.next_filepath is None

    header2 = DummyHeader(2.71, filepath=osp.join("test_dir", "header_file2.txt"))
    assert handler.shouldRollover(
        logging.makeLogRecord({"msg": "header2", "test_key": header2})
    )
    assert handler.current_filepath is not None
    assert handler.next_filepath == header2.filepath

    assert not osp.exists(handler.baseFilename)
    handler.current_filepath = None
    handler.next_filepath = None

    handler.close()


def test_do_rollover():
    """
    Test the doRollover method of ManualRotatingFileHandler.
    It should rename the current file to the next filepath and reset the state.
    """
    handler = ManualRotatingFileHandler(
        filepath=osp.join("test_dir", "test_file.txt"), mode="a"
    )

    with pytest.raises(AssertionError):
        # Should raise an assertion error because there is no current filepath
        handler.doRollover()

    filepath = osp.join("test_dir", "current_file.txt")
    handler.current_filepath = filepath
    handler.doRollover()
    assert handler.current_filepath is None
    assert osp.isdir(osp.dirname(filepath))
    assert not osp.exists(filepath)


def test_emit():
    """
    Test the emit method of ManualRotatingFileHandler.
    It should write the log record to the current file and handle rollover if needed.
    """
    filepath = osp.join("test_dir", "test_file.txt")
    handler = ManualRotatingFileHandler(filepath=filepath, mode="a")
    logger = logging.getLogger("test_emit")
    logger.setLevel(logging.DEBUG)

    logger.addHandler(handler)

    # Log a test message
    filepath_1 = osp.join("test_dir", "header_file1.txt")
    logger.info(DummyHeader(3.14, filepath=filepath_1))
    logger.info(DummyRecord(42))
    assert osp.exists(filepath)
    assert handler.current_filepath == filepath_1
    assert not osp.exists(filepath_1)

    # Log another message that should trigger rollover
    filepath_2 = osp.join("test_dir", "header_file2.txt")
    logger.info(DummyHeader(2.71, filepath=filepath_2))
    assert osp.exists(filepath_1)
    assert handler.current_filepath == filepath_2
    assert handler.next_filepath is None
    logger.info(DummyRecord(100))
    assert not osp.exists(filepath_2)

    handler.close()
    assert handler.current_filepath is None
    assert osp.exists(filepath_2)

    assert not osp.exists(filepath)

    # Check if the message was written correctly
    with open(filepath_1, "r") as f:
        content = f.read()
        assert "DummyRecord(val=42)" in content
        assert "DummyHeader(val=3.14)" in content
    with open(filepath_2, "r") as f:
        content = f.read()
        assert "DummyRecord(val=100)" in content
        assert "DummyHeader(val=2.71)" in content
