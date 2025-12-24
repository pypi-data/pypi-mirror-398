from ttex.config import ConfigurableObject, ConfigurableObjectFactory, ConfigFactory
from . import DummyConfig, EmptyConfig, dict_config
from .. import dummy_log_handler
import pytest
import json
import os
import copy


class DummyConfigurableObject(ConfigurableObject):
    config_class = DummyConfig

    def __init__(self, config: DummyConfig, args_test, kwargs_test=None):
        self.args_test = args_test
        self.kwargs_test = kwargs_test
        super().__init__(config)


def test_configurable_object():
    config = DummyConfig(a=1, b=2, c=3, d=5)
    conf_obj = DummyConfigurableObject(config, "test")

    # init
    assert conf_obj.config_class is type(config)

    # apply config
    for arg in ["a", "b", "c", "d"]:
        assert getattr(conf_obj, arg) == getattr(config, arg)


def test_wrong_config_class():
    config = EmptyConfig()
    dummy_log_handler.last_record = None
    conf_obj = DummyConfigurableObject(config, "test")
    # assert that the wrong type has been picked up
    assert dummy_log_handler.last_record is not None
    assert conf_obj.config_class == DummyConfig
    assert isinstance(conf_obj.config, EmptyConfig)


@pytest.mark.parametrize("mode", ["config", "dict", "json"])
def test_create(mode):
    if mode == "config":
        config = DummyConfig(a=1, b=2, c=3, d=5)
    elif mode == "dict":
        config = dict_config
    else:
        path = "sample_dict.json"
        with open(path, "w") as outfile:
            json.dump(dict_config, outfile)
        config = path

    conf_obj = ConfigurableObjectFactory.create(
        DummyConfigurableObject,
        config,
        "test",
        context=globals(),
        kwargs_test="kwargs_test",
    )

    assert isinstance(conf_obj, DummyConfigurableObject)
    # apply config
    for arg in ["a", "b", "c", "d"]:
        assert hasattr(conf_obj, arg)
    assert getattr(conf_obj, "args_test") == "test"
    assert getattr(conf_obj, "kwargs_test") == "kwargs_test"

    if mode == "json":
        os.remove(config)


def test_extra_param_in_config():
    config = copy.deepcopy(dict_config)
    config["DummyConfig"]["abc"] = "test"
    with pytest.raises(AssertionError):
        ConfigurableObjectFactory.create(
            DummyConfigurableObject,
            config,
            "test",
            context=globals(),
            kwargs_test="kwargs_test",
        )


def test_create_args_wrong():
    config = dict_config
    with pytest.raises(TypeError):
        ConfigurableObjectFactory.create(
            DummyConfigurableObject,
            config,
            "test",
            context=globals(),
            kwargs_test="kwargs_test",
            kwargs_test2="test2",
        )
