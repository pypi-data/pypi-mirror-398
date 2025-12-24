from abc import ABC
from typing import TypeVar, Type, Union, Dict, Optional
import logging
import os

from ttex.config.config import Config, ConfigFactory
from ttex.log import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)


class ConfigurableObject(ABC):  # pylint: disable=too-few-public-methods
    config_class = Config

    def __init__(self, config: Config, *args, **kwargs):
        self.config = config
        if not isinstance(config, self.config_class):
            logger.warning(
                "Config type does not align. Given config was %s"
                + " but given config_class was %s",
                type(config),
                self.config_class,
            )
        self.apply_config(self.config)

    def apply_config(self, config):
        self.__dict__.update(config.__dict__)


T = TypeVar("T", bound=ConfigurableObject)


class ConfigurableObjectFactory(ABC):  # pylint: disable=too-few-public-methods
    """Utility to create a Configurable Object"""

    @staticmethod
    def create(
        configurable_object_class: Type[T],
        config: Union[Dict, Config, str],
        *args,
        context: Optional[Dict] = None,
        **kwargs,
    ) -> T:
        """Create configurable object with the given config

         Args:
            configurable_object_class (Type[T: ConfigurableObject]):
                 They type of configurable object being created
            config (Config/Dict/str): The config for the object
                 Can be passed directly as a config object,
                 its dict representation or as a file path
                 to a json containing the dict

        Returns:
            configurable object (T:Configurable object):
                the configured configurable object
        """
        if isinstance(config, str):
            # Assuming this is a file path, load from file
            assert ".json" in config
            assert os.path.exists(config)
            config = ConfigFactory.from_file(config, context=context)

        if isinstance(config, dict):
            config = ConfigFactory.from_dict(config, context=context)

        # TODO should try force-casting
        if not isinstance(config, configurable_object_class.config_class):
            logger.warning(
                "Config type does not align. Given config was %s"
                + " but given config_class was %s",
                type(config),
                configurable_object_class.config_class,
            )
        typed_config = ConfigFactory.extract(
            configurable_object_class.config_class, config
        )
        logger.debug(f"Passed args {args} and kwargs {kwargs}")
        return configurable_object_class(typed_config, *args, **kwargs)
