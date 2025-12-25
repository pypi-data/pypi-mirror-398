from enum import Enum
from enum import auto


class OrderDirection(Enum):
    """
    Enumeration for order direction.

    Attributes:
        ASC (auto): Ascending order.
        DESC (auto): Descending order.
    """

    ASC = auto()
    DESC = auto()


class Lookup(str, Enum):
    """
    Enumeration for different types of lookup operations.

    Attributes:
        EQ (str): Equal to.
        NEQ (str): Not equal to.
        GT (str): Greater than.
        GTE (str): Greater than or equal to.
        LT (str): Less than.
        LTE (str): Less than or equal to.
        IN (str): In.
        CONTAINS (str): Contains.
        ICONTAINS (str): Case-insensitive contains.
        STARTSWITH (str): Starts with.
        ISTARTSWITH (str): Case-insensitive starts with.
        ENDSWITH (str): Ends with.
        IENDSWITH (str): Case-insensitive ends with.
        ISNULL (str): Is null.
        REGEX (str): Regular expression match.
        IREGEX (str): Case-insensitive regular expression match.
    """

    EQ = 'eq'
    NEQ = 'neq'
    GT = 'gt'
    GTE = 'gte'
    LT = 'lt'
    LTE = 'lte'
    IN = 'in'
    CONTAINS = 'contains'
    ICONTAINS = 'icontains'
    STARTSWITH = 'startswith'
    ISTARTSWITH = 'istartswith'
    ENDSWITH = 'endswith'
    IENDSWITH = 'iendswith'
    ISNULL = 'isnull'
    REGEX = 'regex'
    IREGEX = 'iregex'
