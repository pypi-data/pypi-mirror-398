"""
Managers module for Mini Arcade Core.
Provides various manager classes for handling game entities and resources.
"""

from __future__ import annotations

from .cheats import BaseCheatCommand, CheatCode, CheatManager
from .entities import EntityManager
from .inputs import InputManager
from .overlays import OverlayManager
from .system import SystemManager

__all__ = [
    "EntityManager",
    "OverlayManager",
    "CheatCode",
    "CheatManager",
    "BaseCheatCommand",
    "InputManager",
    "SystemManager",
]
