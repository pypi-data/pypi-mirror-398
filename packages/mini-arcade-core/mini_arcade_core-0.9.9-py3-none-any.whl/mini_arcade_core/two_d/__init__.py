"""
Two-dimensional utilities and components for Mini Arcade Core.
Includes 2D entities, boundaries, and physics.
"""

from __future__ import annotations

from .boundaries2d import (
    RectKinematic,
    RectSprite,
    VerticalBounce,
    VerticalWrap,
)
from .collision2d import RectCollider
from .geometry2d import Bounds2D, Position2D, Size2D
from .kinematics2d import KinematicData
from .physics2d import Velocity2D

__all__ = [
    "Bounds2D",
    "Position2D",
    "Size2D",
    "KinematicData",
    "Velocity2D",
    "RectCollider",
    "RectKinematic",
    "RectSprite",
    "VerticalBounce",
    "VerticalWrap",
]
