"""
Managers module for Mini Arcade Core.
Provides various manager classes for handling game entities and resources.
"""

from __future__ import annotations

from mini_arcade_core.managers.entity_manager import EntityManager
from mini_arcade_core.managers.overlay_manager import OverlayManager

__all__ = [
    "EntityManager",
    "OverlayManager",
]
