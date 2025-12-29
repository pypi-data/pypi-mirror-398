"""
Boundary behaviors for 2D rectangular objects.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .geometry2d import Bounds2D, Position2D, Size2D
from .physics2d import Velocity2D


class RectKinematic(Protocol):
    """
    Minimal contract for something that can bounce:
    - position: Position2D
    - size: Size2D
    - velocity: Velocity2D

    :ivar position (Position2D): Top-left position of the object.
    :ivar size (Size2D): Size of the object.
    :ivar velocity (Velocity2D): Velocity of the object.
    """

    position: Position2D
    size: Size2D
    velocity: Velocity2D


@dataclass
class VerticalBounce:
    """
    Bounce an object off the top/bottom bounds by inverting vy
    and clamping its position inside the bounds.

    :ivar bounds (Bounds2D): The boundary rectangle.
    """

    bounds: Bounds2D

    def apply(self, obj: RectKinematic):
        """
        Apply vertical bounce to the given object.

        :param obj: The object to apply the bounce to.
        :type obj: RectKinematic
        """
        top = self.bounds.top
        bottom = self.bounds.bottom

        # Top collision
        if obj.position.y <= top:
            obj.position.y = top
            obj.velocity.vy *= -1

        # Bottom collision
        if obj.position.y + obj.size.height >= bottom:
            obj.position.y = bottom - obj.size.height
            obj.velocity.vy *= -1


class RectSprite(Protocol):
    """
    Minimal contract for something that can wrap:
    - position: Position2D
    - size: Size2D
    (no velocity required)

    :ivar position (Position2D): Top-left position of the object.
    :ivar size (Size2D): Size of the object.
    """

    position: Position2D
    size: Size2D


@dataclass
class VerticalWrap:
    """
    Wrap an object top <-> bottom.

    If it leaves above the top, it reappears at the bottom.
    If it leaves below the bottom, it reappears at the top.

    :ivar bounds (Bounds2D): The boundary rectangle.
    """

    bounds: Bounds2D

    def apply(self, obj: RectSprite):
        """
        Apply vertical wrap to the given object.

        :param obj: The object to apply the wrap to.
        :type obj: RectSprite
        """
        top = self.bounds.top
        bottom = self.bounds.bottom

        # Completely above top → appear at bottom
        if obj.position.y + obj.size.height < top:
            obj.position.y = bottom

        # Completely below bottom → appear at top
        elif obj.position.y > bottom:
            obj.position.y = top - obj.size.height
