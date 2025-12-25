from pydantic import BaseModel
from pydantic import Field


class IntegrationConfig(BaseModel):
    """
    Configuration model for an integration.

    Attributes:
        default (str): The default integration.
        models (dict[str, str]): A dictionary mapping model names to their configurations.
    """

    default: str
    models: dict[str, str] = Field(default_factory=dict)
