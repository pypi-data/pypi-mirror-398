"""
Scene registry for mini arcade core.
Allows registering and creating scenes by string IDs.
"""

from __future__ import annotations

import importlib
import pkgutil
from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, Protocol

from .autoreg import snapshot

if TYPE_CHECKING:
    from mini_arcade_core.game import Game
    from mini_arcade_core.scenes import Scene


class SceneFactory(Protocol):
    """
    Protocol for scene factory callables.
    """

    def __call__(self, game: "Game") -> "Scene": ...


@dataclass
class SceneRegistry:
    """
    Registry for scene factories, allowing registration and creation of scenes by string IDs.
    """

    _factories: Dict[str, SceneFactory]

    def register(self, scene_id: str, factory: SceneFactory):
        """
        Register a scene factory under a given scene ID.

        :param scene_id: The string ID for the scene.
        :type scene_id: str

        :param factory: A callable that creates a Scene instance.
        :type factory: SceneFactory
        """
        self._factories[scene_id] = factory

    def register_cls(self, scene_id: str, scene_cls: type["Scene"]):
        """
        Register a Scene class under a given scene ID.

        :param scene_id: The string ID for the scene.
        :type scene_id: str

        :param scene_cls: The Scene class to register.
        :type scene_cls: type["Scene"]
        """

        def return_factory(game: "Game") -> "Scene":
            return scene_cls(game)

        self.register(scene_id, return_factory)

    def create(self, scene_id: str, game: "Game") -> "Scene":
        """
        Create a scene instance using the registered factory for the given scene ID.

        :param scene_id: The string ID of the scene to create.
        :type scene_id: str

        :param game: The Game instance to pass to the scene factory.
        :type game: Game

        :return: A new Scene instance.
        :rtype: Scene

        :raises KeyError: If no factory is registered for the given scene ID.
        """
        try:
            return self._factories[scene_id](game)
        except KeyError as e:
            raise KeyError(f"Unknown scene_id={scene_id!r}") from e

    def load_catalog(self, catalog: Dict[str, type["Scene"]]):
        """
        Load a catalog of Scene classes into the registry.

        :param catalog: A dictionary mapping scene IDs to Scene classes.
        :type catalog: Dict[str, type["Scene"]]
        """
        for scene_id, cls in catalog.items():
            self.register_cls(scene_id, cls)

    def discover(self, package: str) -> "SceneRegistry":
        """
        Import all modules in a package so @scene decorators run.

        :param package: The package name to scan for scene modules.
        :type package: str

        :return: The SceneRegistry instance (for chaining).
        :rtype: SceneRegistry
        """
        pkg = importlib.import_module(package)
        if not hasattr(pkg, "__path__"):
            return self  # not a package

        for mod in pkgutil.walk_packages(pkg.__path__, pkg.__name__ + "."):
            importlib.import_module(mod.name)

        self.load_catalog(snapshot())
        return self
