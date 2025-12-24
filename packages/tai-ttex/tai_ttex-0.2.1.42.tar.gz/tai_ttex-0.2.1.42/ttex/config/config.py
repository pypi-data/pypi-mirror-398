"""Config class and ConfigFactory to create one from different sources"""

from abc import ABC
from typing import TypeVar, Type, Union, Dict, Optional, Protocol, Any
from inspect import signature, Parameter
import importlib
import json
import logging
import numpy as np
from ttex.log import LOGGER_NAME
from collections.abc import Iterable

logger = logging.getLogger(LOGGER_NAME)


class ContextProtocol(Protocol):
    """Protocol for context object used in config extraction"""

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the context object"""
        ...

    def setdefault(self, key: str, default: Any = None) -> Any:
        """Set a default value in the context object"""
        ...


# TODO config with separate levels for keys
class Config(ABC):  # pylint: disable=too-few-public-methods
    """Config to go with a configurable object

    Contains the necessary values required to initialise a configurable object
     as defined by that object's specific config
    """

    def __init__(self, *args, **kwargs):
        """Init a configuration
        Should be overriden by each Config object to specify
        exactly which values are required
        """
        # TODO could add something that auto-adds all the values to the dict
        # TODO consider if this should be a dictionary or a namedtuple or sth
        self._to_dict: Optional[Dict] = None

    def get(self, key: str, default=None):
        """Get a specific value from the config dict.
        This might need to be modified for nesting
        Ideally also shouldn't access the dict directly
        """
        return self.__dict__.get(key, default)

    def to_dict(self) -> Dict:
        """
        Convert the config to a dictionary
        """
        # TODO: implement a generic to_dict method. This is just a hack in case we already have a dict at creation
        if hasattr(self, "_to_dict") and self._to_dict is not None:
            return self._to_dict
        else:
            raise NotImplementedError

    def _setup(self, ctx: Optional[ContextProtocol] = None) -> bool:
        """
        Setup the config (private version for override)
        """
        return True

    def setup(self, ctx: Optional[ContextProtocol] = None) -> bool:
        """
        Setup the config and any sub-configs
        ctx: Optional[ContextProtocol]
            Context to use during setup
        Returns:
            success (bool): Whether setup was successful
        """
        success = True
        for v in self.__dict__.values():
            if isinstance(v, Config):
                success = v.setup(ctx=ctx) and success
        return self._setup(ctx=ctx) and success

    def _teardown(self, ctx: Optional[ContextProtocol] = None) -> bool:
        """
        Teardown the config (private version for override)
        """
        return True

    def teardown(self, ctx: Optional[ContextProtocol] = None) -> bool:
        """
        Teardown the config and any sub-configs
        ctx: Optional[ContextProtocol]
            Context to use during teardown
        Returns:
            success (bool): Whether teardown was successful
        """
        success = True
        for v in self.__dict__.values():
            if isinstance(v, Config):
                success = v.teardown(ctx=ctx) and success
        return self._teardown(ctx=ctx) and success


T = TypeVar("T", bound=Config)


class ConfigFactory(ABC):
    """Provides different convenience methods to create a Config Object"""

    @staticmethod
    def _extract_attr(
        full_name: str, context: Optional[Dict] = None, assume_enum: bool = False
    ) -> Type:
        """
        Extract attribute from a string

        Args:
            full_name (str): Full name of the attribute to extract
            context: A dictionary containing the globals() context from where the config is loaded
            assume_enum (bool): Whether to assume the last part of the string is an enum value

        Returns:
            c (Type): The extracted attribute
        """
        # Split the string, will throw value error if there is no .
        module_name = None  # type: Optional[str]
        enum_val = None
        try:
            if assume_enum:
                module_name, class_name, enum_val = full_name.rsplit(".", 2)
            else:
                module_name, class_name = full_name.rsplit(".", 1)
        except ValueError:
            # We do not enforce . - class could already be loaded
            pass
        if module_name:
            # load the module, will raise ImportError if module cannot be loaded
            try:
                m = importlib.import_module(module_name)
            except ImportError as e:
                raise ValueError(f"Did not recognise {full_name}: ImportError {e}")
            # get the class, will raise AttributeError if class cannot be found
            try:
                c = getattr(m, class_name)
            except AttributeError as e:
                raise ValueError(f"Did not recognise {full_name}: AttributeError {e}")
        else:
            # If no module, try loading from globals and context
            if "." in full_name:
                class_name, enum_val = full_name.rsplit(".", 1)
            else:
                class_name = full_name
            if context and class_name in context:
                c = context.get(class_name)
            elif class_name in globals():
                c = globals()[class_name]
            else:
                raise ValueError(
                    f"Did not recognise {class_name}: KeyError Not in context or globals()"
                )
        if enum_val:
            # We are dealing with an enum if this value exists and all imports worked
            c = c[enum_val]

        return c

    @staticmethod
    def _try_extract_attr(full_name: str, context: Optional[Dict] = None) -> Type:
        """Try to extract attribute from a string

        Args:
            full_name (str): Full name of the attribute to extract
            context: A dictionary containing the globals() context from where the config is loaded

        Returns:
            c (Type): The extracted attribute
        """
        try:
            return ConfigFactory._extract_attr(
                full_name, context=context, assume_enum=False
            )
        except ValueError:
            return ConfigFactory._extract_attr(
                full_name, context=context, assume_enum=True
            )

    @staticmethod
    def _extract_value(value: Any, context: Optional[Dict] = None) -> Any:
        logger.debug(f"Extracting value {value}")
        if isinstance(value, str):
            try:
                # For each string, see if it is an attribute
                v_attr = ConfigFactory._try_extract_attr(value, context)
                return v_attr
            except ValueError:
                return value
        elif isinstance(value, dict):
            if len(value.keys()) == 1:
                # 1-key dicts might be configs, try converting
                key_class = list(value.keys())[0]
                try:
                    v_attr = ConfigFactory._try_extract_attr(key_class, context)
                    if issubclass(v_attr, Config):
                        # found a config, process values recursively
                        return ConfigFactory.extract(v_attr, value[key_class], context)
                except ValueError:
                    pass
            return {
                k: ConfigFactory._extract_value(v, context=context)
                for k, v in value.items()
            }
        elif isinstance(value, Iterable) and not isinstance(value, np.ndarray):
            # If the value is iterable, we need to check each element
            # not for np arrays, those do not contain classes
            ret_val = [
                ConfigFactory._extract_value(v, context=context)
                for _, v in enumerate(value)
            ]
            # return as the type of iterable that was passed
            return type(value)(ret_val)  # type: ignore[call-arg]
        else:
            return value

    @staticmethod
    def extract(
        config_class: Type[T],
        config: Union[Dict, Config],
        context: Optional[Dict] = None,
    ) -> T:
        """Extract Config of config_class from config

        Creates an object of type config_class
         by extracting the relevant values from the config

        Args:
            config_class (Type[T: Config]): They type of config being created
            config (Config/Dict): The config containing the values to be extracted
            context: A dictionary containing the globals() context from where the config is loaded

        Returns:
            sub_config (T:Config): the extracted config of type config_class

        """
        signa = signature(config_class.__init__)
        values = {
            p.name: config.get(p.name, p.default)
            for _, p in signa.parameters.items()
            if p.name != "self"
        }
        logger.debug(values)

        # Make sure no non-default params are missing
        non_empty = [np.sum([v != Parameter.empty]) for _, v in values.items()]
        assert all(non_empty), f"Missing values for {config_class} in config {values}"
        if isinstance(config, dict):
            # If we have a dict, we have a potential mismatch of values
            # check that all passed values are in the signature
            assert all([k in values for k, _ in config.items()])

        for k, v in values.items():
            values[k] = ConfigFactory._extract_value(v, context=context)
        return_config = config_class(**values)  # type: ignore[call-arg]
        if isinstance(config, Dict):
            return_config._to_dict = config  # type: ignore[attr-defined]
        return return_config

    @staticmethod
    def from_dict(dict_config: Dict, context: Optional[Dict] = None) -> Config:
        """Create config from a dict

        Creates a config by reading the dict and extracting each sub-config.
        Excpected format:
        {
        "ConfigClass": {
            "param1": "param1value",
            "sub_config": {"ConfigClass2": {"param2": "param2value"}},
        }

        The config classes either need to be imported beforehand
        or the full path needs to be specified, i.e. "module.something.ConfigClass"

        Args:
            dict_config (dict): Dict containing the values to put into configs
            context: A dictionary containing the globals() context from where the config is loaded

        Returns:
            config (Config): the extracted Config

        """
        # Check the format is as expected
        # dictionary with 1 key which is config class name
        assert len(dict_config.keys()) == 1
        class_key = list(dict_config.keys())[0]
        try:
            config_class = ConfigFactory._extract_attr(class_key, context)
        except ValueError as e:
            raise ValueError(f"Unexpected config format {e}")

        # Now extract the config
        config = ConfigFactory.extract(config_class, dict_config[class_key], context)
        return config

    @staticmethod
    def from_file(path_to_json_file: str, context: Optional[Dict] = None) -> Config:
        """Create config from a json file

        Creates a config by reading the json file + extracting each sub-config.
        Excpected format:
        {
        "ConfigClass": {
            "param1": "param1value",
            "sub_config": {"ConfigClass2": {"param2": "param2value"}},
        }

        The config classes either need to be imported beforehand
        or the full path needs to be specified, i.e. "module.something.ConfigClass"

        Args:
            path_to_json_file (str): Path to json file containing
                                     the values to be put into the config

        Returns:
            config (Config): the extracted Config

        """
        with open(path_to_json_file, "r") as infile:
            dict_config = json.load(infile)
        return ConfigFactory.from_dict(dict_config, context)
