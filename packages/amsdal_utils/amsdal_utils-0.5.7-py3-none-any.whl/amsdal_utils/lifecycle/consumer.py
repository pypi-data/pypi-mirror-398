from abc import ABC
from abc import abstractmethod
from typing import Any

from amsdal_utils.lifecycle.enum import LifecycleEvent


class LifecycleConsumer(ABC):
    def __init__(self, event: LifecycleEvent):
        self.event = event

    @abstractmethod
    def on_event(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover
        ...

    @abstractmethod
    async def on_event_async(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover
        ...

    def __hash__(self) -> int:
        return hash(self.__class__.__module__)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, LifecycleConsumer):
            return self.__class__.__module__ == other.__class__.__module__
        return False
