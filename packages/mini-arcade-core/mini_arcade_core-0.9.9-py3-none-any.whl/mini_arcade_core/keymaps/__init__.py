"""
Keymaps for Mini Arcade Core.
Includes key definitions and default key mappings.
"""

from __future__ import annotations

from .keys import Key, keymap
from .sdl import SDL_KEYCODE_TO_KEY

__all__ = [
    "Key",
    "keymap",
    "SDL_KEYCODE_TO_KEY",
]
