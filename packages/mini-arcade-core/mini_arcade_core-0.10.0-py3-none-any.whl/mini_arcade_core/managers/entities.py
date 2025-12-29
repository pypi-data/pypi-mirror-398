"""
Entity manager for handling a collection of entities.
"""

from __future__ import annotations

from dataclasses import dataclass

from mini_arcade_core.backend import Backend

from .base import EntityLike, ListManager


@dataclass
class EntityManager(ListManager[EntityLike]):
    """
    Manages a collection of entities within a scene.
    """

    def update(self, dt: float):
        """
        Update all managed entities.

        :param dt: Time delta in seconds.
        :type dt: float
        """
        for ent in list(self.items):
            ent.update(dt)

    def draw(self, surface: "Backend"):
        """
        Draw all managed entities.

        :param surface: The backend surface to draw on.
        :type surface: Backend
        """
        for ent in list(self.items):
            ent.draw(surface)
