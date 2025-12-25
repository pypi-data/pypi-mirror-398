"""
Base class for game scenes (states/screens).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List, Optional

from mini_arcade_core.backend import Backend, Event
from mini_arcade_core.entity import Entity
from mini_arcade_core.managers import EntityManager, OverlayManager
from mini_arcade_core.two_d import Size2D

if TYPE_CHECKING:
    from mini_arcade_core.game import Game


@dataclass
class SceneServices:
    """
    Container for scene services like entity and overlay managers.

    :ivar entities: EntityManager for managing scene entities.
    :ivar overlays: OverlayManager for managing scene overlays.
    """

    entities: EntityManager = field(default_factory=EntityManager)
    overlays: OverlayManager = field(default_factory=OverlayManager)


class Scene(ABC):
    """Base class for game scenes (states/screens)."""

    def __init__(
        self,
        game: Game,
        *,
        services: Optional[SceneServices] = None,
    ):
        """
        :param game: Reference to the main Game object.
        :type game: Game
        """
        self.game = game
        self.entities: List[Entity] = []
        self.size: Size2D = Size2D(game.config.width, game.config.height)

        self.services: SceneServices = (
            services if services is not None else SceneServices()
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

    def on_pause(self):
        """Called when the game is paused."""

    def on_resume(self):
        """Called when the game is resumed."""
