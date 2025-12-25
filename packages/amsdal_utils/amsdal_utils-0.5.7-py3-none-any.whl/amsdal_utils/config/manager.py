from pathlib import Path
from typing import Any

import yaml

from amsdal_utils.config.data_models.amsdal_config import AmsdalConfig
from amsdal_utils.config.data_models.connection_config import ConnectionConfig
from amsdal_utils.config.data_models.repository_config import RepositoryConfig
from amsdal_utils.utils.singleton import Singleton


class AmsdalConfigManager(metaclass=Singleton):
    _config: AmsdalConfig

    def set_config(self, config: AmsdalConfig) -> None:
        """
        Sets the configuration for the AmsdalConfigManager.

        Args:
            config (AmsdalConfig): The configuration to set.

        Returns:
            None
        """
        self._config = config

    def get_config(self) -> AmsdalConfig:
        """
        Retrieves the current configuration of the AmsdalConfigManager.

        Returns:
            AmsdalConfig: The current configuration.
        """
        return self._config

    def get_connection_name_by_model_name(self, model_name: str) -> str:
        """
        Retrieves the connection name associated with a given model name.

        Args:
            model_name (str): The name of the model to look up.

        Returns:
            str: The connection name associated with the model name,
                 or the default connection name if the model name is not found.
        """
        repository_config: RepositoryConfig | None = self._config.resources_config.repository

        if repository_config is None:
            return self._config.resources_config.lakehouse

        if model_name in repository_config.models:
            return repository_config.models[model_name]
        return repository_config.default

    def load_config(self, config_path: Path) -> None:
        """
        Loads the configuration from a YAML file.

        Args:
            config_path (Path): The path to the YAML configuration file.

        Returns:
            None
        """
        with config_path.open() as config_file:
            self.set_config(self.read_yaml_config(config_file))

    @staticmethod
    def read_yaml_config(config: Any) -> AmsdalConfig:
        """
        Reads and parses a YAML configuration.

        Args:
            config (Any): The YAML configuration to read.

        Returns:
            AmsdalConfig: The parsed configuration as an AmsdalConfig object.
        """
        config = yaml.safe_load(config)

        if 'connections' not in config:
            config['connections'] = []

        if isinstance(config['connections'], list):
            config['connections'] = [ConnectionConfig(**connection) for connection in config['connections']]

        return AmsdalConfig.model_validate(config)
