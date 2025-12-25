from pydantic import BaseModel
from pydantic import ConfigDict

from amsdal_utils.query.enums import OrderDirection


class OrderBy(BaseModel):
    """
    Represents an order by clause for querying data.

    Attributes:
        field_name (str): The name of the field to order by.
        direction (OrderDirection): The direction to order by. Defaults to OrderDirection.ASC.
    """

    model_config = ConfigDict(frozen=True)

    field_name: str
    direction: OrderDirection = OrderDirection.ASC

    @classmethod
    def from_string(cls, value: str) -> 'OrderBy':
        """
        Creates an OrderBy object from a string.

        Args:
            value (str): The string representation of the order by clause.

        Returns:
            OrderBy: The constructed OrderBy object.
        """
        if value.startswith('-'):
            return cls(field_name=value[1:], direction=OrderDirection.DESC)

        return cls(field_name=value, direction=OrderDirection.ASC)
