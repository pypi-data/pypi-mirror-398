"""
Base class for game scenes (states/screens).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List, Optional

from mini_arcade_core.backend import Backend, Event
from mini_arcade_core.entity import Entity
from mini_arcade_core.scenes.model import SceneModel
from mini_arcade_core.spaces.d2 import Size2D

from .runtime import SceneRuntime

if TYPE_CHECKING:
    from mini_arcade_core.game import Game


class Scene(ABC):
    """Base class for game scenes (states/screens)."""

    model: SceneModel

    def __init__(
        self,
        game: Game,
        *,
        services: Optional[SceneRuntime] = None,
    ):
        """
        :param game: Reference to the main Game object.
        :type game: Game
        """
        self.game = game
        self.entities: List[Entity] = []
        self.size: Size2D = Size2D(game.config.width, game.config.height)

        self.services: SceneRuntime = (
            services if services is not None else SceneRuntime()
        )

    @abstractmethod
    def on_enter(self):
        """Called when the scene becomes active."""

    @abstractmethod
    def on_exit(self):
        """Called when the scene is replaced."""

    @abstractmethod
    def handle_event(self, event: Event):
        """
        Handle input / events (e.g. pygame.Event).

        :param event: The event to handle.
        :type event: Event
        """

    @abstractmethod
    def update(self, dt: float):
        """
        Update game logic. ``dt`` is the delta time in seconds.

        :param dt: Time delta in seconds.
        :type dt: float
        """

    @abstractmethod
    def draw(self, surface: Backend):
        """
        Render to the main surface.

        :param surface: The backend surface to draw on.
        :type surface: Backend
        """

    def _systems_on_enter(self):
        for sys in self.services.systems.sorted():
            if getattr(sys, "enabled", True):
                sys.on_enter()

    def _systems_on_exit(self):
        for sys in self.services.systems.sorted():
            if getattr(sys, "enabled", True):
                sys.on_exit()

    def _systems_handle_event(self, event: Event) -> bool:
        for sys in self.services.systems.sorted():
            if getattr(sys, "enabled", True) and sys.handle_event(event):
                return True
        return False

    def _systems_update(self, dt: float):
        for sys in self.services.systems.sorted():
            if getattr(sys, "enabled", True):
                sys.update(dt)

    def _systems_draw(self, surface: Backend):
        for sys in self.services.systems.sorted():
            if getattr(sys, "enabled", True):
                sys.draw(surface)

    def on_pause(self):
        """Called when the game is paused."""

    def on_resume(self):
        """Called when the game is resumed."""
