from enum import Enum
from typing import Any

from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator

DEFAULT_NAME = 'default'


class ConnectionType(str, Enum):
    """
    Enumeration of connection types.

    - LAKEHOUSE: Lakehouse database connection with historical tracking
    - STATE: State database connection without historical tracking
    - EXTERNAL_SERVICE: Connection to an external service
    """

    LAKEHOUSE = 'lakehouse'
    STATE = 'state'
    EXTERNAL_SERVICE = 'external_service'


class ConnectionConfig(BaseModel):
    """
    Configuration model for a connection.

    Attributes:
        name (str): The name of the connection.
        backend (str): The backend implementation for the connection.
        credentials (dict[str, Any]): The credentials required for the connection.
        connection_type (ConnectionType): The type of connection (lakehouse, state, external_service).
        is_managed (bool): Whether the connection participates in AMSDAL lifecycle management.
    """

    name: str = DEFAULT_NAME
    backend: str = 'amsdal_data.connections.implementations.iceberg_history.IcebergHistoricalConnection'
    credentials: dict[str, Any] = Field(default_factory=dict)
    connection_type: ConnectionType = ConnectionType.LAKEHOUSE
    is_managed: bool = True

    @field_validator('credentials', mode='before')
    @classmethod
    def set_credentials(cls, value: list[dict[str, Any]] | dict[str, Any]) -> dict[str, Any]:
        """
        Validates and sets the credentials attribute.

        Args:
            cls (type): The class type.
            value (list[dict[str, Any]] | dict[str, Any]): The credentials to set,
                either as a dictionary or a list of dictionaries.

        Returns:
            dict[str, Any]: The validated credentials as a dictionary.
        """
        if isinstance(value, dict):
            return value

        credentials = {}

        for credential in value:
            credentials.update(credential)

        return credentials
