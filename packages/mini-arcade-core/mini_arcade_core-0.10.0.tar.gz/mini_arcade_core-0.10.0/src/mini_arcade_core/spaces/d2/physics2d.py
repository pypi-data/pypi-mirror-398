"""
Simple 2D physics utilities.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Velocity2D:
    """
    Simple 2D velocity vector.

    :ivar vx (float): Velocity in the X direction.
    :ivar vy (float): Velocity in the Y direction.
    """

    vx: float = 0.0
    vy: float = 0.0

    def advance(self, x: float, y: float, dt: float) -> tuple[float, float]:
        """Return new (x, y) after dt seconds."""
        return x + self.vx * dt, y + self.vy * dt

    def stop(self):
        """Stop movement in both axes."""
        self.vx = 0.0
        self.vy = 0.0

    def stop_x(self):
        """Stop horizontal movement."""
        self.vx = 0.0

    def stop_y(self):
        """Stop vertical movement."""
        self.vy = 0.0

    def move_up(self, speed: float):
        """
        Set vertical velocity upwards (negative Y).

        :param speed: Speed to set.
        :type speed: float
        """
        self.vy = -abs(speed)

    def move_down(self, speed: float):
        """
        Set vertical velocity downwards (positive Y).

        :param speed: Speed to set.
        :type speed: float
        """
        self.vy = abs(speed)

    def move_left(self, speed: float):
        """
        Set horizontal velocity to the left (negative X)."

        :param speed: Speed to set.
        :type speed: float
        """
        self.vx = -abs(speed)

    def move_right(self, speed: float):
        """
        Set horizontal velocity to the right (positive X).

        :param speed: Speed to set.
        :type speed: float
        """
        self.vx = abs(speed)
