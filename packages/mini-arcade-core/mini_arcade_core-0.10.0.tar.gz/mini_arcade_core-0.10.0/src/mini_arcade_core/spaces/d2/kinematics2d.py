"""
Kinematic helpers for mini_arcade_core (position + size + velocity).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from mini_arcade_core.backend import Color

from .geometry2d import Position2D, Size2D
from .physics2d import Velocity2D


@dataclass
class KinematicData:
    """
    Simple data structure to hold position, size, and velocity.

    :ivar position (Position2D): Top-left position of the object.
    :ivar size (Size2D): Size of the object.
    :ivar velocity (Velocity2D): Velocity of the object.
    :ivar color (Optional[Color]): Optional color for rendering.
    """

    position: Position2D
    size: Size2D
    velocity: Velocity2D
    time_scale: float = 1.0
    color: Optional[Color] = None  # future use

    # Justification: Convenience factory with many params.
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    @classmethod
    def rect(
        cls,
        x: float,
        y: float,
        width: int,
        height: int,
        vx: float = 0.0,
        vy: float = 0.0,
        time_scale: float = 1.0,
        color: Optional[Color] = None,
    ) -> "KinematicData":
        """
        Convenience factory for rectangular kinematic data.

        :param x: Top-left X position.
        :type x: float

        :param y: Top-left Y position.
        :type y: float

        :param width: Width of the object.
        :type width: int

        :param height: Height of the object.
        :type height: int

        :param vx: Velocity in the X direction.
        :type vx: float

        :param vy: Velocity in the Y direction.
        :type vy: float

        :param color: Optional color for rendering.
        :type color: Optional[Color]

        :return: KinematicData instance with the specified parameters.
        :rtype: KinematicData
        """
        return cls(
            position=Position2D(float(x), float(y)),
            size=Size2D(int(width), int(height)),
            velocity=Velocity2D(float(vx), float(vy)),
            time_scale=time_scale,
            color=color,
        )

    # pylint: enable=too-many-arguments,too-many-positional-arguments
