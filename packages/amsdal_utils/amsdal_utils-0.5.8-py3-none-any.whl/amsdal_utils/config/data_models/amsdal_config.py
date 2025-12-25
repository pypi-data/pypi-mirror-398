from pathlib import Path

from pydantic import BaseModel
from pydantic import field_validator

from amsdal_utils.config.data_models.connection_config import ConnectionConfig
from amsdal_utils.config.data_models.resources_config import ResourcesConfig


class AmsdalConfig(BaseModel):
    """
    Configuration model for Amsdal application.

    Attributes:
        application_name (str): The name of the application.
        connections (dict[str, ConnectionConfig]): A dictionary of connection configurations.
        resources_config (ResourcesConfig): The resources configuration.
        async_mode (bool): Whether to run the application in async mode.
    """

    application_name: str
    connections: dict[str, ConnectionConfig]
    resources_config: ResourcesConfig
    async_mode: bool = False
    config_dir: Path | None = None

    @property
    def is_lakehouse_only(self) -> bool:
        """
        Returns whether the application is lakehouse only.

        Returns:
            bool: True if the application is lakehouse only, False otherwise.
        """
        return (
            not self.resources_config.repository
            or self.resources_config.repository.default == self.resources_config.lakehouse
        )

    @field_validator('connections', mode='before')
    @classmethod
    def set_connections(
        cls,
        values: dict[str, ConnectionConfig] | list[ConnectionConfig],
    ) -> dict[str, ConnectionConfig]:
        """
        Validates and sets the connections attribute.

        Args:
            cls (type): The class type.
            values (dict[str, ConnectionConfig] | list[ConnectionConfig]): The connections to set,
                either as a dictionary or a list.

        Returns:
            dict[str, ConnectionConfig]: The validated connections as a dictionary.
        """
        if isinstance(values, list):
            return {connection.name: connection for connection in values}

        return values
