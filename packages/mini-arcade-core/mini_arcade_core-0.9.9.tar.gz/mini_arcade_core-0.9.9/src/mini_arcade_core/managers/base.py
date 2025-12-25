"""
Base manager classes for handling collections of items.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Generic, Iterable, List, Protocol, TypeVar

from mini_arcade_core.backend.backend import Backend

# ---- shared types ----
T = TypeVar("T")
OverlayFunc = Callable[[Backend], None]


class Drawable(Protocol):
    """Defines a drawable entity."""

    def draw(self, surface: Backend):
        """
        Draw the entity on the given surface.

        :param surface: The backend surface to draw on.
        :type surface: Backend
        """


class Updatable(Protocol):
    """Defines an updatable entity."""

    def update(self, dt: float):
        """
        Update the entity state.

        :param dt: Time delta in seconds.
        :type dt: float
        """


class EntityLike(Drawable, Updatable, Protocol):
    """Defines a game entity."""


@dataclass
class ListManager(Generic[T]):
    """
    Generic manager for a list of items.

    :ivar items (List[T]): List of managed items.
    """

    items: List[T] = field(default_factory=list)

    def add(self, *items: T):
        """
        Add one or more items to the manager.

        :param items: One or more items to add.
        :type items: T
        """
        self.items.extend(items)

    def add_many(self, items: Iterable[T]):
        """
        Add multiple items to the manager.

        :param items: An iterable of items to add.
        :type items: Iterable[T]
        """
        self.items.extend(items)

    def remove(self, item: T):
        """
        Remove a single item from the manager, if present.

        :param item: The item to remove.
        :type item: T
        """
        if item in self.items:
            self.items.remove(item)

    def clear(self):
        """Clear all items from the manager."""
        self.items.clear()

    def __iter__(self):
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)
