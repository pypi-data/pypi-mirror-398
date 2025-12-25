"""
Scenes module for Mini Arcade Core.
Provides the base Scene class and related functionality.
"""

from __future__ import annotations

from .autoreg import register_scene
from .registry import SceneRegistry
from .scene import Scene

__all__ = ["Scene", "register_scene", "SceneRegistry"]
