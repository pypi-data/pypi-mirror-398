from enum import Enum


class ResourceType(str, Enum):
    """
    Enumeration of resource types.

    Attributes:
        LAKEHOUSE (str): Represents a lakehouse resource.
        LOCK (str): Represents a lock resource.
        INTEGRATION (str): Represents an integration resource.
    """

    LAKEHOUSE = 'lakehouse'
    LOCK = 'lock'
    INTEGRATION = 'integration'
