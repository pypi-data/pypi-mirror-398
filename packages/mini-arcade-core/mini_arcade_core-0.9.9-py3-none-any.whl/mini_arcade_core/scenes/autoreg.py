"""
Autoregistration utilities for mini arcade core.
Allows automatic registration of Scene classes via decorators.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Type

if TYPE_CHECKING:
    from . import Scene

_AUTO: Dict[str, Type["Scene"]] = {}


def register_scene(scene_id: str):
    """
    Decorator to mark and register a Scene class under an id.

    :param scene_id: The unique identifier for the Scene class.
    :type scene_id: str

    :raises ValueError: If the scene_id is already registered.
    """

    def deco(cls: Type["Scene"]):
        _AUTO[scene_id] = cls
        setattr(cls, "__scene_id__", scene_id)
        return cls

    return deco


def snapshot() -> Dict[str, Type["Scene"]]:
    """
    Copy of current catalog (useful for tests).

    :return: A copy of the current scene catalog.
    :rtype: Dict[str, Type["Scene"]]
    """
    return dict(_AUTO)


def clear():
    """Clear the current catalog (useful for tests)."""
    _AUTO.clear()
