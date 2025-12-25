"""
Entity base classes for mini_arcade_core.
"""

from __future__ import annotations

from typing import Any

from mini_arcade_core.two_d import (
    KinematicData,
    Position2D,
    RectCollider,
    Size2D,
)


class Entity:
    """Entity base class for game objects."""

    def update(self, dt: float):
        """
        Advance the entity state by ``dt`` seconds.

        :param dt: Time delta in seconds.
        :type dt: float
        """

    def draw(self, surface: Any):
        """
        Render the entity to the given surface.

        :param surface: The surface to draw on.
        :type surface: Any
        """


class SpriteEntity(Entity):
    """Entity with position and size."""

    def __init__(self, position: Position2D, size: Size2D):
        """
        :param position: Top-left position of the entity.
        :type position: Position2D

        :param size: Size of the entity.
        :type size: Size2D
        """
        self.position = Position2D(float(position.x), float(position.y))
        self.size = Size2D(int(size.width), int(size.height))
        self.collider = RectCollider(self.position, self.size)


class KinematicEntity(SpriteEntity):
    """SpriteEntity with velocity-based movement."""

    def __init__(self, kinematic_data: KinematicData):
        """
        :param kinematic_data: Kinematic data for the entity.
        :type kinematic_data: KinematicData
        """
        super().__init__(
            position=kinematic_data.position,
            size=kinematic_data.size,
        )

        self.velocity = kinematic_data.velocity

    def update(self, dt: float):
        self.position.x, self.position.y = self.velocity.advance(
            self.position.x, self.position.y, dt
        )
