from enum import Enum


class Versions(str, Enum):
    """
    Enumeration for version types.

    Attributes:
        ALL (str): Represents all versions.
        LATEST (str): Represents the latest version.
    """

    ALL = 'ALL'
    LATEST = 'LATEST'

    def __repr__(self) -> str:
        return self.value

    def __str__(self) -> str:
        return self.value


class ModuleType(str, Enum):
    """
    Enumeration for module types.

    Attributes:
        TYPE (str): Represents the type module.
        CORE (str): Represents the core module.
        USER (str): Represents the user module.
        CONTRIB (str): Represents the contrib module.
    """

    TYPE = 'type'
    CORE = 'core'
    USER = 'user'
    CONTRIB = 'contrib'
