"""
Overlay base classes.
"""

from __future__ import annotations

from mini_arcade_core.backend import Backend


class BaseOverlay:
    """
    Base class for overlays.

    :ivar enabled (bool): Whether the overlay is enabled.
    :ivar priority (int): Drawing priority; lower values draw first.
    """

    enabled: bool = True
    priority: int = 0  # lower draws first

    # Justification for unused argument: method is intended to be overridden.
    # pylint: disable=unused-argument
    def update(self, dt: float):
        """
        Update the overlay state.

        :param dt: Time delta in seconds.
        :type dt: float
        """
        return

    # pylint: enable=unused-argument

    def draw(self, surface: "Backend"):
        """
        Draw the overlay on the given surface.

        :param surface: The backend surface to draw on.
        :type surface: Backend
        """
        raise NotImplementedError("draw() must be implemented by subclasses.")
