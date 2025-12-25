"""
Backend module for rendering and input abstraction.
Defines the Backend interface and related types.
This is the only part of the code that talks to SDL/pygame directly.
"""

from __future__ import annotations

from .backend import Backend
from .events import Event, EventType
from .types import Color

__all__ = [
    "Backend",
    "Event",
    "EventType",
    "Color",
]
