"""
2D collision detection helpers.
"""

from __future__ import annotations

from dataclasses import dataclass

from .geometry2d import Position2D, Size2D


def _rects_intersect(
    pos_a: Position2D,
    size_a: Size2D,
    pos_b: Position2D,
    size_b: Size2D,
) -> bool:
    """
    Low-level AABB check. Internal helper.

    :param pos_a: Top-left position of rectangle A.
    :type pos_a: Position2D

    :param size_a: Size of rectangle A.
    :type size_a: Size2D

    :param pos_b: Top-left position of rectangle B.
    :type pos_b: Position2D

    :param size_b: Size of rectangle B.
    :type size_b: Size2D

    :return: True if the rectangles intersect.
    :rtype: bool
    """
    return not (
        pos_a.x + size_a.width < pos_b.x
        or pos_a.x > pos_b.x + size_b.width
        or pos_a.y + size_a.height < pos_b.y
        or pos_a.y > pos_b.y + size_b.height
    )


@dataclass
class RectCollider:
    """
    OOP collision helper that wraps a Position2D + Size2D pair.

    It does NOT own the data - it just points to them. If the
    entity moves (position changes), the collider “sees” it.

    :ivar position (Position2D): Top-left position of the rectangle.
    :ivar size (Size2D): Size of the rectangle.
    """

    position: Position2D
    size: Size2D

    def intersects(self, other: "RectCollider") -> bool:
        """
        High-level OOP method to check collision with another collider.

        ;param other: The other rectangle collider.
        :type other: RectCollider

        :return: True if the rectangles intersect.
        :rtype: bool
        """
        return _rects_intersect(
            self.position, self.size, other.position, other.size
        )
