from pydantic import BaseModel
from pydantic import Field


class QuerySpecifier(BaseModel):
    r"""
    Allows for specifying which fields to include in the query and which fields to mark as distinct.

    Attributes:
        only (list\[str\]): List of fields to include in the query.
        distinct (list\[str\]): List of fields to mark as distinct.
    """

    only: list[str] = Field(default_factory=list)
    distinct: list[str] = Field(default_factory=list)
