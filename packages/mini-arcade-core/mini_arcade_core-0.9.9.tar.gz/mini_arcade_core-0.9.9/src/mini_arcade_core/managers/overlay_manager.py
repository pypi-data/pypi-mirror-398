"""
Overlay manager for handling a collection of overlays.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

from mini_arcade_core.backend import Backend
from mini_arcade_core.managers.base import ListManager

if TYPE_CHECKING:
    from mini_arcade_core.game import Game

OverlayFunc = Callable[[Backend], None]


@dataclass
class OverlayManager(ListManager[OverlayFunc]):
    """
    Manages a collection of overlays within a scene.
    """

    def draw(self, surface: "Backend"):
        """
        Call all overlays. Scenes should call this at the end of draw().

        :param surface: The backend surface to draw on.
        :type surface: Backend
        """
        for overlay in self.items:
            overlay(surface)
