"""
Overlay manager for handling a collection of overlays.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Union

from mini_arcade_core.backend import Backend
from mini_arcade_core.managers.base import ListManager, Overlay, OverlayFunc

OverlayType = Union[Overlay, OverlayFunc]


@dataclass
class OverlayManager(ListManager[OverlayType]):
    """
    Manages a collection of overlays within a scene.
    """

    def update(self, dt: float):
        """
        Update all managed overlays.

        :param dt: Time delta in seconds.
        :type dt: float
        """
        for ov in list(self.items):
            # class overlays only
            if hasattr(ov, "update") and hasattr(ov, "draw"):
                if getattr(ov, "enabled", True):
                    ov.update(dt)

    def draw(self, surface: "Backend"):
        """
        Call all overlays. Scenes should call this at the end of draw().

        :param surface: The backend surface to draw on.
        :type surface: Backend
        """

        def prio(o: OverlayType) -> int:
            """Priority for sorting overlays."""
            return getattr(o, "priority", 0)

        for ov in sorted(list(self.items), key=prio):
            if hasattr(ov, "draw"):
                if getattr(ov, "enabled", True):
                    ov.draw(surface)
            else:
                # function overlay
                ov(surface)
