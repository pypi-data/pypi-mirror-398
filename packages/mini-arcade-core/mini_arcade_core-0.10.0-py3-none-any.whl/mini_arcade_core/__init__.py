"""
Entry point for the mini_arcade_core package.
Provides access to core classes and a convenience function to run a game.
"""

from __future__ import annotations

import logging
from importlib.metadata import PackageNotFoundError, version
from typing import Callable, Type, Union

from mini_arcade_core import backend  # noqa: F401
from mini_arcade_core import keymaps  # noqa: F401
from mini_arcade_core import managers  # noqa: F401
from mini_arcade_core import spaces  # noqa: F401
from mini_arcade_core import ui  # noqa: F401
from mini_arcade_core.bus import event_bus
from mini_arcade_core.commands import (
    BaseCommand,
    BaseGameCommand,
    BaseSceneCommand,
    QuitGameCommand,
)
from mini_arcade_core.entity import Entity, KinematicEntity, SpriteEntity
from mini_arcade_core.game import Game, GameConfig
from mini_arcade_core.scenes import Scene, SceneRegistry

SceneFactoryLike = Union[Type[Scene], Callable[[Game], Scene]]

logger = logging.getLogger(__name__)


def run_game(
    scene: SceneFactoryLike | None = None,
    config: GameConfig | None = None,
    registry: SceneRegistry | None = None,
    initial_scene: str = "main",
):
    """
    Convenience helper to bootstrap and run a game with a single scene.

    Supports both:
      - run_game(SceneClass, cfg)            # legacy
      - run_game(config=cfg, initial_scene="main", registry=...)  # registry-based
      - run_game(cfg)                       # config-only

    :param initial_scene: The Scene ID to start the game with.
    :type initial_scene: str

    :param config: Optional GameConfig to customize game settings.
    :type config: GameConfig | None

    :param registry: Optional SceneRegistry for scene management.
    :type registry: SceneRegistry | None

    :raises ValueError: If the provided config does not have a valid Backend.
    """
    # Handle run_game(cfg) where the first arg is actually a GameConfig
    if isinstance(scene, GameConfig) and config is None:
        config = scene
        scene = None

    cfg = config or GameConfig()
    if cfg.backend is None:
        raise ValueError(
            "GameConfig.backend must be set to a Backend instance"
        )

    # If user provided a Scene factory/class, ensure it's registered
    if scene is not None:
        if registry is None:
            registry = SceneRegistry(_factories={})
        registry.register(
            initial_scene, scene
        )  # Scene class is callable(game) -> Scene

    game = Game(cfg, registry=registry)
    game.run(initial_scene)


__all__ = [
    "Game",
    "GameConfig",
    "Entity",
    "SpriteEntity",
    "KinematicEntity",
    "BaseCommand",
    "BaseGameCommand",
    "BaseSceneCommand",
    "QuitGameCommand",
    "event_bus",
    "run_game",
    "backend",
    "keymaps",
    "managers",
    "spaces",
    "ui",
]

PACKAGE_NAME = "mini-arcade-core"  # or whatever is in your pyproject.toml


def get_version() -> str:
    """
    Return the installed package version.

    This is a thin helper around importlib.metadata.version so games can do:

        from mini_arcade_core import get_version
        print(get_version())

    :return: The version string of the installed package.
    :rtype: str

    :raises PackageNotFoundError: If the package is not installed.
    """
    try:
        return version(PACKAGE_NAME)
    except PackageNotFoundError:  # if running from source / editable
        logger.warning(
            f"Package '{PACKAGE_NAME}' not found. Returning default version '0.0.0'."
        )
        return "0.0.0"


__version__ = get_version()
