from ttex.config import Config
from .. import dummy_log_handler
from typing import Union, List, Tuple, Any
from enum import Enum


class DummyContext:
    def __init__(self):
        self._data: dict[str, Any] = {}
        self._frozen = False

    def set(self, key: str, value: Any) -> None:
        if self._frozen:
            raise RuntimeError("Cannot modify frozen context")
        self._data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def freeze(self) -> None:
        self._frozen = True


class DummyEnum(Enum):
    A = 1
    B = 2


class DummyConfig(Config):
    def __init__(
        self,
        a: int,
        b: Union[Config, str],
        c: List[str] = [""],
        d: Tuple[str, int] = ("", 3),
        e: DummyEnum = DummyEnum.A,
    ):
        self.a = a
        self.b = b
        self.c = c
        self.d = d
        self.e = e
        self.test = "test"
        self._tdwn = False
        self._stp = False

    def _setup(self, ctx: DummyContext):
        self._stp = True
        return True

    def _teardown(self, ctx: DummyContext):
        self._tdwn = True
        return True


class EmptyConfig(Config):
    def __init__(self):
        pass


dict_config = {
    "DummyConfig": {
        "a": "a",
        "b": {
            "DummyConfig": {
                "a": "a2",
                "b": "b2",
            }
        },
        "c": "ConfigFactory",
        "d": ["d", 4],
        "e": "DummyEnum.B",
    }
}
