"""
Protocol for scene systems.
A scene system is a modular component that can hook into the scene lifecycle
methods (on_enter, on_exit, handle_event, update, draw) to provide additional
functionality.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from mini_arcade_core.backend import Backend, Event

if TYPE_CHECKING:
    from mini_arcade_core.scenes.scene import Scene


@dataclass
class BaseSceneSystem:
    """
    Protocol for scene systems.

    :ivar enabled (bool): Whether the system is enabled.
    :ivar priority (int): Priority of the system (lower runs first).
    """

    enabled: bool = True
    priority: int = 0  # lower runs first

    def __init__(self, scene: "Scene"):
        self.scene = scene

    def on_enter(self):
        """
        Called when the scene is entered.
        """

    def on_exit(self):
        """
        Called when the scene is exited.
        """

    def handle_event(self, event: "Event") -> bool:
        """
        Handle an event.

        :param event: The event to handle.
        :type event: Event

        :return: True if the event was handled, False otherwise.
        :rtype: bool
        """

    def update(self, dt: float):
        """
        Update the system.

        :param dt: Delta time since last update.
        :type dt: float
        """

    def draw(self, surface: "Backend"):
        """
        Draw the system.

        :param surface: The backend surface to draw on.
        :type surface: Backend
        """
