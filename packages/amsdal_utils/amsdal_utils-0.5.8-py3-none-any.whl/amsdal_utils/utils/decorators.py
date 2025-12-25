from collections.abc import Callable
from functools import wraps
from typing import ParamSpec
from typing import TypeVar

from amsdal_utils.config.manager import AmsdalConfigManager
from amsdal_utils.errors import AmsdalAsyncModeError

P = ParamSpec('P')
R = TypeVar('R')


def async_mode_only(func: Callable[P, R]) -> Callable[P, R]:
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        if AmsdalConfigManager().get_config().async_mode:
            return func(*args, **kwargs)

        msg = 'This function is only available in async mode'
        raise AmsdalAsyncModeError(msg)

    return wrapper


def sync_mode_only(func: Callable[P, R]) -> Callable[P, R]:
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        if not AmsdalConfigManager().get_config().async_mode:
            return func(*args, **kwargs)

        msg = 'This function is only available in sync mode'
        raise AmsdalAsyncModeError(msg)

    return wrapper
