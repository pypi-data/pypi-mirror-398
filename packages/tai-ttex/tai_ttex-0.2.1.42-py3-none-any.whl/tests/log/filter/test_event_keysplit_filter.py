from logging import makeLogRecord
import pytest
import os.path as osp
from ttex.log.filter import LogEvent, LoggingState, KeySplitter, EventKeysplitFilter
from uuid import uuid4
from ttex.log.formatter import StrRecord
from ..handler.test_manual_rotating_file_handler import DummyRecord
import sys

sys.modules["monkey_patch"] = sys.modules[__name__]


class DummyLogEventA(LogEvent):
    def __init__(self, a: int):
        self.a = a
        self.id = str(uuid4())


class DummyLogEventB(LogEvent):
    def __init__(self, b: int):
        self.b = b
        self.id = str(uuid4())


class DummyLogEventC(LogEvent):
    def __init__(self, c: int):
        self.c = c
        self.id = str(uuid4())


class DummyLoggingState(LoggingState):
    def __init__(self):
        self.counts_a = 0
        self.counts_b = 0

    def update(self, event: LogEvent) -> None:
        if isinstance(event, DummyLogEventA):
            self.counts_a += 1
        elif isinstance(event, DummyLogEventB):
            self.counts_b += 1


class DummyKeySplitter(KeySplitter):
    def __init__(self, offset_a: int = 0, offset_b: int = 0):
        self.offset_a = offset_a
        self.offset_b = offset_b

    def init_logging_state(self) -> DummyLoggingState:
        """
        Initialize the logging state for DummyKeySplitter.
        This method returns an instance of DummyLoggingState that tracks counts of events.
        """
        return DummyLoggingState()

    def process(
        self, state: DummyLoggingState, event: LogEvent
    ) -> dict[str, StrRecord]:
        records = {}
        if isinstance(event, DummyLogEventA):
            records["event_a"] = DummyRecord(state.counts_a + self.offset_a)
        elif isinstance(event, DummyLogEventB):
            records["event_a"] = DummyRecord(state.counts_a + self.offset_b)
            records["event_b"] = DummyRecord(state.counts_b + self.offset_b)
        return records


def test_log_event_a():
    """
    Test that the filter allows LogEventA and processes it correctly.
    """
    filter = EventKeysplitFilter(
        key_splitter_cls="monkey_patch.DummyKeySplitter",
        key_splitter_args={"offset_a": 7, "offset_b": 3},
    )
    event = DummyLogEventA(a=1)
    record = makeLogRecord({"msg": event})

    assert filter.filter(record) is True
    assert isinstance(filter.state, DummyLoggingState)
    assert filter.state.counts_a == 1
    assert filter.state.counts_b == 0
    assert hasattr(record, "event_a")
    assert isinstance(record.event_a, DummyRecord)
    assert record.event_a.val == 8  # 1 + 7 offset

    assert filter.filter(record) is True  # Should still be True for the same event
    assert filter.state.counts_a == 2  # Count should increment


def test_log_event_b():
    """
    Test that the filter allows LogEventB and processes it correctly.
    """
    filter = EventKeysplitFilter(
        key_splitter_cls="monkey_patch.DummyKeySplitter",
        key_splitter_args={"offset_a": 5, "offset_b": 2},
    )
    event = DummyLogEventB(b=2)
    record = makeLogRecord({"msg": event})

    assert filter.filter(record) is True
    assert isinstance(filter.state, DummyLoggingState)
    assert filter.state.counts_a == 0
    assert filter.state.counts_b == 1
    assert hasattr(record, "event_a")
    assert hasattr(record, "event_b")
    assert isinstance(record.event_a, DummyRecord)
    assert isinstance(record.event_b, DummyRecord)
    assert record.event_a.val == 2  # 0 + 2 offset
    assert record.event_b.val == 3  # 1 + 2 offset


def test_log_event_c():
    """
    Test that the filter does not allow LogEventC.
    """
    filter = EventKeysplitFilter(
        key_splitter_cls="monkey_patch.DummyKeySplitter",
    )
    event = DummyLogEventC(c=3)
    record = makeLogRecord({"msg": event})

    assert filter.filter(record) is False
    assert not hasattr(record, "event_a")
    assert not hasattr(record, "event_b")
    assert isinstance(filter.state, DummyLoggingState)
    assert filter.state.counts_a == 0
    assert filter.state.counts_b == 0
