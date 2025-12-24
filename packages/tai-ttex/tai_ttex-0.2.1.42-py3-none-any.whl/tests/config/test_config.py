from ttex.config import Config, ConfigFactory
from . import DummyConfig, dict_config, DummyEnum
import pytest
from logging import Handler
import os
import json
import copy
import numpy as np


def test_get_val():
    config = Config()
    config.test = 5

    assert config.get("test") == 5
    assert config.get("test2") is None

    # default values
    assert config.get("test", 3) == 5
    assert config.get("test2", 3) == 3


def test_extract_empty():
    config = {}
    with pytest.raises(AssertionError):
        ConfigFactory.extract(DummyConfig, config)
    config = {"a": (5, 2), "b": 2}
    test_config = ConfigFactory.extract(DummyConfig, config)
    assert test_config.a is not None
    assert test_config.b is not None
    assert test_config.c == [""]
    assert test_config.d == ("", 3)
    assert test_config.e == DummyEnum.A


def test_extract_value():
    assert ConfigFactory._extract_value(5) == 5
    assert ConfigFactory._extract_value("5") == "5"
    assert ConfigFactory._extract_value([5, 2]) == [5, 2]
    assert ConfigFactory._extract_value((5, 2)) == (5, 2)
    assert all(ConfigFactory._extract_value(np.array([5, 2])) == np.array([5, 2]))
    assert np.all(
        ConfigFactory._extract_value(np.array([[5, 2], [3, 4]]))
        == np.array([[5, 2], [3, 4]])
    )
    assert ConfigFactory._extract_value("DummyEnum.A", context=globals()) == DummyEnum.A
    assert isinstance(
        ConfigFactory._extract_value(
            {"DummyConfig": {"a": (5, 2), "b": 2}}, context=globals()
        ),
        DummyConfig,
    )
    assert ConfigFactory._extract_value(
        ["DummyEnum.A", DummyEnum.B], context=globals()
    ) == [DummyEnum.A, DummyEnum.B]
    assert ConfigFactory._extract_value((5, "DummyEnum.A"), context=globals()) == (
        5,
        DummyEnum.A,
    )
    assert ConfigFactory._extract_value(
        [(5, "DummyEnum.A"), (6, "DummyEnum.B")], context=globals()
    ) == [(5, DummyEnum.A), (6, DummyEnum.B)]

    assert ConfigFactory._extract_value({"a": True}) == {"a": True}
    assert ConfigFactory._extract_value(
        [("DummyEnum.A", {"a": "DummyEnum.B"})], context=globals()
    ) == [(DummyEnum.A, {"a": DummyEnum.B})]
    assert ConfigFactory._extract_value(
        {"a": "DummyEnum.A", "b": "DummyEnum.B"}, context=globals()
    ) == {"a": DummyEnum.A, "b": DummyEnum.B}
    assert ConfigFactory._extract_value(
        {"a": {"b": "DummyEnum.A"}}, context=globals()
    ) == {"a": {"b": DummyEnum.A}}


def test_extract():
    config = Config()
    config.a = [[1, 2, 3], [4, 5, 6]]
    config.b = np.array([np.array([1, 2, 3]), np.array([4, 5, 6])])
    config.c = "kwarg"
    config.d = 17

    test_config = ConfigFactory.extract(DummyConfig, config)

    for arg in ["a", "b"]:
        assert np.sum(getattr(test_config, arg)) == np.sum(getattr(config, arg))

    for arg in ["c", "d"]:
        assert getattr(test_config, arg) == getattr(config, arg)

    with pytest.raises(NotImplementedError):
        test_config.to_dict()  # Due to hack


def test_exctract_class():
    ex_class = ConfigFactory._extract_attr("ttex.log.handler.WandbHandler")
    assert issubclass(ex_class, Handler)

    with pytest.raises(ValueError) as e:
        # Splitting error
        ConfigFactory._extract_attr("DummyConfig")

    # Test error catching
    with pytest.raises(ValueError) as e:
        # Module import error
        ConfigFactory._extract_attr("WandbHandler")
    assert "Did not recognise" in str(e.value)
    assert "KeyError" in str(e.value)

    with pytest.raises(ValueError) as e:
        # Module import error
        ConfigFactory._extract_attr("tex.WandbHandler")
    assert "Did not recognise" in str(e.value)
    assert "No module named" in str(e.value)

    with pytest.raises(ValueError) as e:
        # class not found
        ConfigFactory._extract_attr("ttex.WandbHandler")
    assert "Did not recognise" in str(e.value)
    assert "has no attribute" in str(e.value)

    # Test Enum
    with pytest.raises(ValueError):
        ConfigFactory._extract_attr("DummyEnum.A")
    enum_local = ConfigFactory._extract_attr(
        "DummyEnum.A", context=globals(), assume_enum=True
    )
    assert enum_local == DummyEnum.A


@pytest.mark.parametrize("mode", ["extract", "dict", "json"])
def test_from_dict(mode):
    if mode == "extract":
        config = ConfigFactory.extract(
            DummyConfig, dict_config["DummyConfig"], context=globals()
        )
    elif mode == "dict":
        config = ConfigFactory.from_dict(dict_config, context=globals())
    else:
        path = "sample_dict.json"
        with open(path, "w") as outfile:
            json.dump(dict_config, outfile)
        config = ConfigFactory.from_file(path, context=globals())

    assert isinstance(config, DummyConfig)
    assert config.a == "a"
    assert isinstance(config.b, DummyConfig)
    assert config.b.a == "a2"
    assert config.c == ConfigFactory
    assert config.e == DummyEnum.B

    assert config.to_dict() == dict_config["DummyConfig"]
    if mode == "json":
        os.remove(path)


def test_config_dict_format():
    # more than 1 key in config
    with pytest.raises(AssertionError):
        ConfigFactory.from_dict(dict_config["DummyConfig"])
    # Missing definition (not passed in globals)
    with pytest.raises(ValueError):
        ConfigFactory.from_dict(dict_config)


def test_wrong_args():
    conf = copy.deepcopy(dict_config)
    conf["DummyConfig"]["abc"] = "Test"
    with pytest.raises(AssertionError):
        ConfigFactory.from_dict(conf, context=globals())


def test_setup_teardown():
    config = ConfigFactory.extract(
        DummyConfig, dict_config["DummyConfig"], context=globals()
    )
    assert not config._stp
    assert not config._tdwn

    assert config.setup()
    assert config._stp
    assert isinstance(config.b, DummyConfig)
    assert config.b._stp
    assert not config._tdwn

    assert config.teardown()
    assert config._stp
    assert config.b._stp
    assert config._tdwn
    assert config.b._tdwn
