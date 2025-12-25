from pydantic import BaseModel
from pydantic import Field


class RepositoryConfig(BaseModel):
    """
    Configuration model for a repository.

    Attributes:
        default (str): The default repository.
        models (dict[str, str]): A dictionary mapping model names to their configurations.
    """

    default: str
    models: dict[str, str] = Field(default_factory=dict)
