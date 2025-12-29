"""
Scenes module for Mini Arcade Core.
Provides the base Scene class and related functionality.
"""

from __future__ import annotations

from .autoreg import register_scene
from .model import SceneModel
from .registry import SceneRegistry
from .runtime import SceneRuntime
from .scene import Scene
from .system import BaseSceneSystem

__all__ = [
    "Scene",
    "register_scene",
    "SceneRegistry",
    "SceneRuntime",
    "SceneModel",
    "BaseSceneSystem",
]
