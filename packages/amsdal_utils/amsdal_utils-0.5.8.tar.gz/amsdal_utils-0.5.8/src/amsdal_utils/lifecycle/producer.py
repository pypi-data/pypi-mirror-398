from collections import defaultdict
from typing import Any
from typing import ClassVar

from amsdal_utils.lifecycle.consumer import LifecycleConsumer
from amsdal_utils.lifecycle.enum import LifecycleEvent


class LifecycleProducer:
    __listeners: ClassVar[dict[LifecycleEvent, list[type[LifecycleConsumer]]]] = defaultdict(list)

    @classmethod
    def add_listener(
        cls,
        event: LifecycleEvent,
        listener: type[LifecycleConsumer],
        *,
        insert_first: bool = False,
    ) -> None:
        """
        Adds a listener for a specific lifecycle event.

        Args:
            event (LifecycleEvent): The lifecycle event to listen for.
            listener (type[LifecycleConsumer]): The listener class to add.
            insert_first (bool, optional): Whether to insert the listener at the beginning of the list.
                Defaults to False.

        Returns:
            None
        """
        if listener in cls.__listeners[event]:
            return

        if insert_first:
            cls.__listeners[event].insert(0, listener)
        else:
            cls.__listeners[event].append(listener)

    @classmethod
    def publish(cls, event: LifecycleEvent, *args: Any, **kwargs: Any) -> None:
        """
        Publishes an event to all registered listeners.

        Args:
            event (LifecycleEvent): The lifecycle event to publish.
            *args (Any): Positional arguments to pass to the event listeners.
            **kwargs (Any): Keyword arguments to pass to the event listeners.

        Returns:
            None
        """
        for listener_class in cls.__listeners[event]:
            listener_class(event).on_event(*args, **kwargs)

    @classmethod
    async def publish_async(cls, event: LifecycleEvent, *args: Any, **kwargs: Any) -> None:
        """
        Publishes an event to all registered listeners.

        Args:
            event (LifecycleEvent): The lifecycle event to publish.
            *args (Any): Positional arguments to pass to the event listeners.
            **kwargs (Any): Keyword arguments to pass to the event listeners.

        Returns:
            None
        """
        for listener_class in cls.__listeners[event]:
            await listener_class(event).on_event_async(*args, **kwargs)

    @classmethod
    def reset(cls) -> None:
        cls.__listeners.clear()
