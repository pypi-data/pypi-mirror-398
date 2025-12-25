from pydantic import BaseModel
from pydantic import Field

from amsdal_utils.config.data_models.repository_config import RepositoryConfig


class ResourcesConfig(BaseModel):
    """
    Configuration model for resources.

    Attributes:
        lakehouse (str): The lakehouse configuration.
        lock (str): The lock configuration.
        repository (RepositoryConfig): The repository configuration.
        worker (str): The worker configuration.
        external_services (dict[str, str]): Mapping of service names to connection names for external services.
            Example: {"email": "smtp_connection", "storage": "s3_connection"}
    """

    lakehouse: str
    lock: str | None = None
    repository: RepositoryConfig | None = None
    worker: str | None = None
    external_services: dict[str, str] = Field(default_factory=dict)
