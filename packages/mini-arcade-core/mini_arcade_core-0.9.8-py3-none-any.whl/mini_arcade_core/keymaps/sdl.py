"""
SDL keymap for mini arcade core.
Maps SDL keycodes to mini arcade core Key enums.

:cvar SDL_KEYCODE_TO_KEY: dict[int, Key]
    Mapping from SDL keycodes to Key enums.
"""

from __future__ import annotations

from mini_arcade_core.keymaps.keys import Key

# SDL keycodes you need (minimal set)
_SDLK_ESCAPE = 27
_SDLK_RETURN = 13
_SDLK_SPACE = 32
_SDLK_TAB = 9
_SDLK_BACKSPACE = 8

_SDLK_UP = 1073741906
_SDLK_DOWN = 1073741905
_SDLK_LEFT = 1073741904
_SDLK_RIGHT = 1073741903

_F1 = 1073741882
_F2 = 1073741883
_F3 = 1073741884
_F4 = 1073741885
_F5 = 1073741886
_F6 = 1073741887
_F7 = 1073741888
_F8 = 1073741889
_F9 = 1073741890
_F10 = 1073741891
_F11 = 1073741892
_F12 = 1073741893

SDL_KEYCODE_TO_KEY: dict[int, Key] = {
    # Letters
    ord("a"): Key.A,
    ord("b"): Key.B,
    ord("c"): Key.C,
    ord("d"): Key.D,
    ord("e"): Key.E,
    ord("f"): Key.F,
    ord("g"): Key.G,
    ord("h"): Key.H,
    ord("i"): Key.I,
    ord("j"): Key.J,
    ord("k"): Key.K,
    ord("l"): Key.L,
    ord("m"): Key.M,
    ord("n"): Key.N,
    ord("o"): Key.O,
    ord("p"): Key.P,
    ord("q"): Key.Q,
    ord("r"): Key.R,
    ord("s"): Key.S,
    ord("t"): Key.T,
    ord("u"): Key.U,
    ord("v"): Key.V,
    ord("w"): Key.W,
    ord("x"): Key.X,
    ord("y"): Key.Y,
    ord("z"): Key.Z,
    # Arrows
    _SDLK_UP: Key.UP,
    _SDLK_DOWN: Key.DOWN,
    _SDLK_LEFT: Key.LEFT,
    _SDLK_RIGHT: Key.RIGHT,
    # Common
    _SDLK_ESCAPE: Key.ESCAPE,
    _SDLK_SPACE: Key.SPACE,
    _SDLK_RETURN: Key.ENTER,
    _SDLK_TAB: Key.TAB,
    _SDLK_BACKSPACE: Key.BACKSPACE,
    # Numbers
    ord("0"): Key.NUM_0,
    ord("1"): Key.NUM_1,
    ord("2"): Key.NUM_2,
    ord("3"): Key.NUM_3,
    ord("4"): Key.NUM_4,
    ord("5"): Key.NUM_5,
    ord("6"): Key.NUM_6,
    ord("7"): Key.NUM_7,
    ord("8"): Key.NUM_8,
    ord("9"): Key.NUM_9,
    # Function keys
    _F1: Key.F1,
    _F2: Key.F2,
    _F3: Key.F3,
    _F4: Key.F4,
    _F5: Key.F5,
    _F6: Key.F6,
    _F7: Key.F7,
    _F8: Key.F8,
    _F9: Key.F9,
    _F10: Key.F10,
    _F11: Key.F11,
    _F12: Key.F12,
}
