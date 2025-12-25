"""
Mini Arcade Core key definitions.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class Key(Enum):
    """
    Enumeration of common keyboard keys.

    :ivar A-Z: Letter keys.
    :ivar arrow_up, arrow_down, arrow_left, arrow_right: Arrow keys.
    :ivar escape, space, enter, tab, backspace: Common control keys.
    :ivar num_0 - num_9: Number keys.
    :ivar f1 - f12: Function keys.
    """

    # Letters
    A = auto()
    B = auto()
    C = auto()
    D = auto()
    E = auto()
    F = auto()
    G = auto()
    H = auto()
    I = auto()
    J = auto()
    K = auto()
    L = auto()
    M = auto()
    N = auto()
    O = auto()
    P = auto()
    Q = auto()
    R = auto()
    S = auto()
    T = auto()
    U = auto()
    V = auto()
    W = auto()
    X = auto()
    Y = auto()
    Z = auto()

    # Arrows
    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()

    # Common
    ESCAPE = auto()
    SPACE = auto()
    ENTER = auto()
    TAB = auto()
    BACKSPACE = auto()

    # Numbers
    NUM_0 = auto()
    NUM_1 = auto()
    NUM_2 = auto()
    NUM_3 = auto()
    NUM_4 = auto()
    NUM_5 = auto()
    NUM_6 = auto()
    NUM_7 = auto()
    NUM_8 = auto()
    NUM_9 = auto()

    # Function keys
    F1 = auto()
    F2 = auto()
    F3 = auto()
    F4 = auto()
    F5 = auto()
    F6 = auto()
    F7 = auto()
    F8 = auto()
    F9 = auto()
    F10 = auto()
    F11 = auto()
    F12 = auto()


# Justification: Simple alias object for keys
# pylint: disable=too-many-instance-attributes
@dataclass(frozen=True)
class _Keys:
    # alias object so user code can do keys.w, keys.arrow_up, etc.
    a: Key = Key.A
    b: Key = Key.B
    c: Key = Key.C
    d: Key = Key.D
    e: Key = Key.E
    f: Key = Key.F
    g: Key = Key.G
    h: Key = Key.H
    i: Key = Key.I
    j: Key = Key.J
    k: Key = Key.K
    l: Key = Key.L
    m: Key = Key.M
    n: Key = Key.N
    o: Key = Key.O
    p: Key = Key.P
    q: Key = Key.Q
    r: Key = Key.R
    s: Key = Key.S
    t: Key = Key.T
    u: Key = Key.U
    v: Key = Key.V
    w: Key = Key.W
    x: Key = Key.X
    y: Key = Key.Y
    z: Key = Key.Z

    up: Key = Key.UP
    down: Key = Key.DOWN
    left: Key = Key.LEFT
    right: Key = Key.RIGHT

    escape: Key = Key.ESCAPE
    space: Key = Key.SPACE
    enter: Key = Key.ENTER
    tab: Key = Key.TAB
    backspace: Key = Key.BACKSPACE

    num_0: Key = Key.NUM_0
    num_1: Key = Key.NUM_1
    num_2: Key = Key.NUM_2
    num_3: Key = Key.NUM_3
    num_4: Key = Key.NUM_4
    num_5: Key = Key.NUM_5
    num_6: Key = Key.NUM_6
    num_7: Key = Key.NUM_7
    num_8: Key = Key.NUM_8
    num_9: Key = Key.NUM_9

    f1: Key = Key.F1
    f2: Key = Key.F2
    f3: Key = Key.F3
    f4: Key = Key.F4
    f5: Key = Key.F5
    f6: Key = Key.F6
    f7: Key = Key.F7
    f8: Key = Key.F8
    f9: Key = Key.F9
    f10: Key = Key.F10
    f11: Key = Key.F11
    f12: Key = Key.F12


# pylint: enable=too-many-instance-attributes

keymap = _Keys()
