"""
Core event types and structures.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional, Tuple

from mini_arcade_core.keymaps.keys import Key


class EventType(Enum):
    """
    High-level event types understood by the core.

    :cvar UNKNOWN: Unknown/unhandled event.
    :cvar QUIT: User requested to quit the game.
    :cvar KEYDOWN: A key was pressed.
    :cvar KEYUP: A key was released.
    :cvar MOUSEMOTION: The mouse was moved.
    :cvar MOUSEBUTTONDOWN: A mouse button was pressed.
    :cvar MOUSEBUTTONUP: A mouse button was released.
    :cvar MOUSEWHEEL: The mouse wheel was scrolled.
    :cvar WINDOWRESIZED: The window was resized.
    :cvar TEXTINPUT: Text input event (for IME support).
    """

    UNKNOWN = auto()
    QUIT = auto()

    KEYDOWN = auto()
    KEYUP = auto()

    # Mouse
    MOUSEMOTION = auto()
    MOUSEBUTTONDOWN = auto()
    MOUSEBUTTONUP = auto()
    MOUSEWHEEL = auto()

    # Window / text
    WINDOWRESIZED = auto()
    TEXTINPUT = auto()


# Justification: Simple data container for now
# pylint: disable=too-many-instance-attributes
@dataclass(frozen=True)
class Event:
    """
    Core event type.

    For now we only care about:
    - type: what happened
    - key: integer key code (e.g. ESC = 27), or None if not applicable

    :ivar type (EventType): The type of event.
    :ivar key (Key | None): The key associated with the event, if any.
    :ivar key_code (int | None): The key code associated with the event, if any.
    :ivar scancode (int | None): The hardware scancode of the key, if any.
    :ivar mod (int | None): Modifier keys bitmask, if any.
    :ivar repeat (bool | None): Whether this key event is a repeat, if any.
    :ivar x (int | None): Mouse X position, if any.
    :ivar y (int | None): Mouse Y position, if any.
    :ivar dx (int | None): Mouse delta X, if any.
    :ivar dy (int | None): Mouse delta Y, if any.
    :ivar button (int | None): Mouse button number, if any.
    :ivar wheel (Tuple[int, int] | None): Mouse wheel scroll (x, y), if any.
    :ivar size (Tuple[int, int] | None): New window size (width, height), if any.
    :ivar text (str | None): Text input, if any.
    """

    type: EventType
    key: Key | None = None  # Use Key enum for better clarity
    key_code: Optional[int] = None

    # Keyboard extras (optional)
    scancode: Optional[int] = None
    mod: Optional[int] = None
    repeat: Optional[bool] = None

    # Mouse (optional)
    x: Optional[int] = None
    y: Optional[int] = None
    dx: Optional[int] = None
    dy: Optional[int] = None
    button: Optional[int] = None
    wheel: Optional[Tuple[int, int]] = None  # (wheel_x, wheel_y)

    # Window (optional)
    size: Optional[Tuple[int, int]] = None  # (width, height)

    # Text input (optional)
    text: Optional[str] = None


# pylint: enable=too-many-instance-attributes
