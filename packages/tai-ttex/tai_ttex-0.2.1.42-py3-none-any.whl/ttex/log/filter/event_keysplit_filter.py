from logging import Filter
from ttex.log.formatter import StrRecord
from abc import ABC, abstractmethod
from typing import Optional, Dict


class LogEvent(ABC):
    pass


class LoggingState(ABC):
    def update(self, event: LogEvent) -> None:
        pass


class KeySplitter(ABC):
    @abstractmethod
    def init_logging_state(self) -> LoggingState:
        pass

    @abstractmethod
    def process(self, state: LoggingState, event: LogEvent) -> Dict[str, StrRecord]:
        pass


class EventKeysplitFilter(Filter):
    """
    Filter to allow only COCOHeader and COCORecord messages.
    """

    def __init__(
        self,
        key_splitter_cls: str,
        key_splitter_args: Optional[Dict] = None,
        name: str = "",
    ):
        """
        :param key_splitter_cls: Full dotted path to a KeySplitter class.
        :param key_splitter_args: Optional dict of arguments to pass to the KeySplitter constructor.
        :param name: Filter name.
        """
        super().__init__(name)

        key_splitter_args = key_splitter_args or {}

        # Dynamically import and instantiate KeySplitter
        self.key_splitter = self._resolve_class(key_splitter_cls)(**key_splitter_args)
        self.state = self.key_splitter.init_logging_state()

    def _resolve_class(self, dotted_path: str):
        """Dynamically import a class from a dotted module path."""
        module_path, class_name = dotted_path.rsplit(".", 1)
        module = __import__(module_path, fromlist=[class_name])
        return getattr(module, class_name)

    def filter(self, record) -> bool:
        """ """

        if not isinstance(record.msg, LogEvent):
            return False

        self.state.update(record.msg)
        records = self.key_splitter.process(self.state, record.msg)
        if not records:
            return False

        for key, recs in records.items():
            setattr(record, key, recs)
        return True
