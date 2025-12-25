from enum import Enum
from enum import auto


class LifecycleEvent(Enum):
    """
    Enumeration of lifecycle events.

    Attributes:
        ON_AUTHENTICATE: Event triggered on authentication.
        ON_PERMISSION_CHECK: Event triggered on permission check.
        ON_MIGRATE: Event triggered on migration.
        ON_SERVER_STARTUP: Event triggered on server startup.
    """

    ON_AUTHENTICATE = auto()
    ON_PERMISSION_CHECK = auto()
    ON_MIGRATE = auto()
    ON_SERVER_STARTUP = auto()
