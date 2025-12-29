"""
Event bus module.
"""

from __future__ import annotations

from typing import Callable, ClassVar, Dict, List, Optional


class EventBus:
    """
    Simple event bus for managing event subscriptions and emissions.
    """

    _instance: ClassVar[Optional["EventBus"]] = None
    _subscribers: Dict[str, List[Callable]]

    def __new__(cls):
        if cls._instance is None:
            inst = super().__new__(cls)
            inst._subscribers = {}
            cls._instance = inst
        return cls._instance

    def on(self, event_type: str, handler: Callable):
        """
        Subscribe a handler to an event type.

        :param event_type: The type of event to subscribe to.
        :type event_type: str

        :param handler: The handler function to call when the event is emitted.
        :type handler: Callable
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    def emit(self, event_type: str, **kwargs):
        """
        Emit an event of a given type, calling all subscribed handlers.

        :param event_type: The type of event to emit.
        :type event_type: str

        :param kwargs: Additional keyword arguments to pass to handlers.
        """
        handlers = self._subscribers.get(event_type, [])
        for handler in handlers:
            handler(**kwargs)

    def clear(self):
        """Clear all subscribers from the event bus."""
        self._subscribers.clear()


event_bus = EventBus()
