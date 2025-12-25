"""
2D geometry data structures.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Position2D:
    """
    Simple 2D position.

    :ivar x (float): X coordinate.
    :ivar y (float): Y coordinate.
    """

    x: float
    y: float


@dataclass
class Size2D:
    """
    Simple 2D size.

    :ivar width (int): Width.
    :ivar height (int): Height.
    """

    width: int
    height: int


@dataclass
class Bounds2D:
    """
    Axis-aligned rectangular bounds in world space.
    (left, top) .. (right, bottom)

    :ivar left (float): Left boundary.
    :ivar top (float): Top boundary.
    :ivar right (float): Right boundary.
    :ivar bottom (float): Bottom boundary.
    """

    left: float
    top: float
    right: float
    bottom: float

    @classmethod
    def from_size(cls, size: "Size2D") -> "Bounds2D":
        """
        Convenience factory for screen/world bounds starting at (0, 0).

        :param size: Size2D defining the bounds.
        :type size: Size2D

        :return: Bounds2D from (0,0) to (size.width, size.height).
        :rtype: Bounds2D
        """
        return cls(
            left=0.0,
            top=0.0,
            right=float(size.width),
            bottom=float(size.height),
        )
