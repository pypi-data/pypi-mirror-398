from collections.abc import Callable
from typing import Generic
from typing import TypeVar

TLazyObject = TypeVar('TLazyObject')
TLazyInstanceObject = TypeVar('TLazyInstanceObject')


class NoValue: ...


class LazyObject(Generic[TLazyObject]):
    r"""
    Helper class to lazily load an attribute.

    Args:
        resolver (Callable\[[], TLazyObject\]): A callable that resolves the value of the attribute.
    """

    def __init__(self, resolver: Callable[[], TLazyObject]) -> None:
        self._value: TLazyObject | NoValue = NoValue()
        self._resolver: Callable[[], TLazyObject] = resolver

    @property
    def value(self) -> TLazyObject:
        """
        Lazily loads and returns the value of the attribute for the given instance.

        Args:
            instance (TLazyInstanceObject): The instance for which the attribute value is to be loaded.

        Returns:
            TLazyObject: The lazily loaded attribute value.
        """
        if isinstance(self._value, NoValue):
            self._value = self._resolver()

        return self._value


class LazyInstanceObject(Generic[TLazyInstanceObject, TLazyObject]):
    r"""
    Helper class to lazily load an attribute of an instance.

    Args:
        resolver (Callable\[[TLazyInstanceObject\], TLazyObject\]): A callable that resolves the value of the attribute
            for the given instance.
    """

    def __init__(self, resolver: Callable[[TLazyInstanceObject], TLazyObject]) -> None:
        self._value: TLazyObject | NoValue = NoValue()
        self._resolver: Callable[[TLazyInstanceObject], TLazyObject] = resolver

    def value(self, instance: TLazyInstanceObject) -> TLazyObject:
        """
        Lazily loads and returns the value of the attribute for the given instance.

        Args:
            instance (TLazyInstanceObject): The instance for which the attribute value is to be loaded.

        Returns:
            TLazyObject: The lazily loaded attribute value.
        """
        if isinstance(self._value, NoValue):
            self._value = self._resolver(instance)

        return self._value
