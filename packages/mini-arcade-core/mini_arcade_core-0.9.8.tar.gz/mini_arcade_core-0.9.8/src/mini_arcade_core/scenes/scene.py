"""
Base class for game scenes (states/screens).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Callable, List

from mini_arcade_core.backend import Backend, Event
from mini_arcade_core.entity import Entity
from mini_arcade_core.two_d import Size2D

if TYPE_CHECKING:
    from mini_arcade_core.game import Game

OverlayFunc = Callable[[Backend], None]


class Scene(ABC):
    """Base class for game scenes (states/screens)."""

    def __init__(self, game: Game):
        """
        :param game: Reference to the main Game object.
        :type game: Game
        """
        self.game = game
        self.entities: List[Entity] = []
        self.size: Size2D = Size2D(game.config.width, game.config.height)
        # overlays drawn on top of the scene
        self._overlays: List[OverlayFunc] = []

    def add_entity(self, *entities: Entity):
        """
        Register one or more entities in this scene.

        :param entities: One or more Entity instances to add.
        :type entities: Entity
        """
        self.entities.extend(entities)

    def remove_entity(self, entity: Entity):
        """
        Unregister a single entity, if present.

        :param entity: The Entity instance to remove.
        :type entity: Entity
        """
        if entity in self.entities:
            self.entities.remove(entity)

    def clear_entities(self):
        """Remove all entities from the scene."""
        self.entities.clear()

    def update_entities(self, dt: float):
        """
        Default update loop for all entities.

        :param dt: Time delta in seconds.
        :type dt: float
        """
        for ent in self.entities:
            ent.update(dt)

    def draw_entities(self, surface: Backend):
        """
        Default draw loop for all entities.

        :param surface: The backend surface to draw on.
        :type surface: Backend
        """
        for ent in self.entities:
            ent.draw(surface)

    def add_overlay(self, overlay: OverlayFunc):
        """
        Register an overlay (drawn every frame, after entities).

        :param overlay: A callable that takes a Backend and draws on it.
        :type overlay: OverlayFunc
        """
        self._overlays.append(overlay)

    def remove_overlay(self, overlay: OverlayFunc):
        """
        Unregister a previously added overlay.

        :param overlay: The overlay to remove.
        :type overlay: OverlayFunc
        """
        if overlay in self._overlays:
            self._overlays.remove(overlay)

    def clear_overlays(self):
        """Clear all registered overlays."""
        self._overlays.clear()

    def draw_overlays(self, surface: Backend):
        """
        Call all overlays. Scenes should call this at the end of draw().

        :param surface: The backend surface to draw on.
        :type surface: Backend
        """
        for overlay in self._overlays:
            overlay(surface)

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
