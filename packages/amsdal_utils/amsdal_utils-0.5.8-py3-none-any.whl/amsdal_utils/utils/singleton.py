from typing import Any
from typing import ClassVar
from typing import Generic
from typing import TypeVar

T = TypeVar('T')


class Singleton(type, Generic[T]):
    __instances: ClassVar[dict[type[T], T]] = {}

    def __call__(
        cls: type[T],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        _instances = cls.__instances  # type: ignore[attr-defined]
        if cls not in _instances:
            _instances[cls] = super().__call__(*args, **kwargs)  # type: ignore[misc]
        return _instances[cls]

    def invalidate(cls) -> None:
        if cls is Singleton:
            cls.__instances.clear()
        elif cls in cls.__instances:
            del cls.__instances[cls]  # type: ignore[arg-type]
