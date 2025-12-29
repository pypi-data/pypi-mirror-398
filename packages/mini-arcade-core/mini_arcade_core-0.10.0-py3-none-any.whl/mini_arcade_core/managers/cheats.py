"""
Cheats module for Mini Arcade Core.
Provides cheat codes and related functionality.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import (
    TYPE_CHECKING,
    Callable,
    Deque,
    Dict,
    Generic,
    Optional,
    Protocol,
    Sequence,
    TypeVar,
)

from mini_arcade_core.backend import Event, EventType
from mini_arcade_core.scenes.system import BaseSceneSystem

if TYPE_CHECKING:
    from mini_arcade_core.scenes import Scene

# Justification: We want to keep the type variable name simple here.
# pylint: disable=invalid-name
TContext = TypeVar("TContext")
TScene = TypeVar("TScene", bound="Scene")
# pylint: enable=invalid-name


@dataclass
class BaseCheatCommand(ABC, Generic[TContext]):
    """
    Base class for cheat codes.

    :ivar enabled (bool): Whether the cheat code is enabled.
    """

    enabled: bool = True

    def __call__(self, context: TContext) -> None:
        """
        Execute the cheat code with the given context.

        :param context: Context object for cheat execution.
        :type context: TContext
        """
        if not self.enabled:
            return False
        self.execute(context)
        return True

    @abstractmethod
    def execute(self, context: TContext):
        """
        Execute the cheat code with the given context.

        :param context: Context object for cheat execution.
        :type context: TContext
        """
        raise NotImplementedError("CheatCommand.execute must be overridden.")


class CheatAction(Protocol[TContext]):
    """
    Protocol for cheat code actions.

    :ivar enabled: Whether the cheat action is enabled.
    """

    enabled: bool

    def __call__(self, ctx: TContext) -> bool: ...


@dataclass(frozen=True)
class CheatCode:
    """
    Represents a registered cheat code.

    :ivar name (str): Unique name of the cheat code.
    :ivar sequence (tuple[str, ...]): Sequence of key strings that trigger the cheat.
    :ivar action (CheatAction): BaseCheatCommand to call when the cheat is activated.
    :ivar clear_buffer_on_match (bool): Whether to clear the input buffer after a match.
    :ivar enabled (bool): Whether the cheat code is enabled.
    """

    name: str
    sequence: tuple[str, ...]
    action: CheatAction[TContext]
    clear_buffer_on_match: bool = False
    enabled: bool = True


class CheatManager:
    """
    Reusable cheat code matcher.
    Keeps a rolling buffer of recent keys and triggers callbacks on sequence match.
    """

    def __init__(
        self,
        buffer_size: int = 16,
        *,
        enabled: bool = True,
        normalize: Optional[Callable[[str], str]] = None,
        key_getter: Optional[Callable[[object], Optional[str]]] = None,
    ):
        """
        :param buffer_size: Maximum size of the input buffer.
        :type buffer_size: int

        :param enabled: Whether the cheat manager is enabled.
        :type enabled: bool

        :param normalize: Optional function to normalize key strings.
        :type normalize: Callable[[str], str] | None

        :param key_getter: Optional function to extract key string from event object.
        :type key_getter: Callable[[object], Optional[str]] | None
        """
        self.enabled = enabled
        self._buffer: Deque[str] = deque(maxlen=buffer_size)
        self._codes: Dict[str, CheatCode] = {}

        self._normalize = normalize or (lambda s: s.strip().upper())
        # key_getter: how to extract a key from an engine/backend event object
        self._key_getter = key_getter or self._default_key_getter

    # Justification: We want to keep the number of arguments manageable here.
    # pylint: disable=too-many-arguments
    def register_command(
        self,
        name: str,
        sequence: Sequence[str],
        command: BaseCheatCommand[TContext],
        *,
        clear_buffer_on_match: bool = False,
        enabled: bool = True,
    ):
        """
        Register a new cheat code that triggers a BaseCheatCommand.

        :param name: Unique name for the cheat code.
        :type name: str

        :param sequence: Sequence of key strings that trigger the cheat.
        :type sequence: Sequence[str]

        :param command: BaseCheatCommand to execute when the cheat is activated.
        :type command: BaseCheatCommand[TContext]

        :param clear_buffer_on_match: Whether to clear the input buffer after a match.
        :type clear_buffer_on_match: bool

        :param enabled: Whether the cheat code is enabled.
        :type enabled: bool
        """
        if not name:
            raise ValueError("Cheat code name must be non-empty.")
        if not sequence:
            raise ValueError(
                f"Cheat code '{name}' sequence must be non-empty."
            )

        norm_seq = tuple(self._normalize(k) for k in sequence)
        self._codes[name] = CheatCode(
            name=name,
            sequence=norm_seq,
            action=command,
            clear_buffer_on_match=clear_buffer_on_match,
            enabled=enabled,
        )

    # pylint: enable=too-many-arguments

    def unregister_code(self, name: str):
        """
        Unregister a cheat code by name.

        :param name: Name of the cheat code to unregister.
        :type name: str
        """
        self._codes.pop(name, None)

    def clear_buffer(self):
        """Clear the input buffer."""
        self._buffer.clear()

    def process_event(self, event: object, context: TContext) -> list[str]:
        """
        Call from Scene when a key is pressed.
        Returns list of cheat names matched (often 0 or 1).

        :param event: The event object from the backend/engine.
        :type event: object

        :param context: Context object passed to cheat callbacks.
        :type context: TContext
        """
        if not self.enabled:
            return []
        key = self._key_getter(event)
        if not key:
            return []
        return self.process_key(key, context)

    def process_key(self, key: str, context: TContext) -> list[str]:
        """
        Pure method for tests: feed a key string directly.

        :param key: The key string to process.
        :type key: str

        :param context: Context object passed to cheat callbacks.
        :type context: TContext

        :return: List of cheat names matched.
        :rtype: list[str]
        """
        if not self.enabled:
            return []

        k = self._normalize(key)
        if not k:
            return []

        self._buffer.append(k)
        buf = tuple(self._buffer)

        matched: list[str] = []
        # Check if buffer ends with any cheat sequence
        for code in self._codes.values():
            if not code.enabled:
                continue
            seq = code.sequence
            if len(seq) > len(buf):
                continue
            if buf[-len(seq) :] == seq:
                code.action(context)
                matched.append(code.name)
                if code.clear_buffer_on_match:
                    self.clear_buffer()
                    break  # buffer changed; stop early

        return matched

    @staticmethod
    def _default_key_getter(event: object) -> Optional[str]:
        """
        Best-effort extraction:
        - event.key
        - event.key_code
        - event.code
        - event.scancode
        - dict-like {"key": "..."}
        Adjust/override with key_getter in your engine if needed.

        :param event: The event object.
        :type event: object

        :return: Extracted key string, or None if not found.
        :rtype: Optional[str]
        """
        if event is None:
            return None

        # dict-like
        if isinstance(event, dict):
            v = (
                event.get("key")
                or event.get("key_code")
                or event.get("code")
                or event.get("scancode")
            )
            if isinstance(v, Enum):
                return v.name
            return str(v) if v is not None else None

        # object-like
        for attr in ("key", "key_code", "code", "scancode"):
            if hasattr(event, attr):
                v = getattr(event, attr)
                if v is None:
                    continue
                if isinstance(v, Enum):
                    return v.name  # <-- THIS is the important bit
                return str(v)

        return None


class CheatSystem(BaseSceneSystem, Generic[TScene]):
    """
    Scene system for handling cheat codes.

    :ivar priority (int): Priority of the system (lower runs first).
    :ivar enabled (bool): Whether the system is enabled.
    """

    priority = 10

    def __init__(self, scene: TScene, buffer_size=16):
        """
        :param buffer_size: Size of the cheat input buffer.
        :type buffer_size: int
        """
        super().__init__(scene)
        self.cheats = CheatManager(buffer_size=buffer_size)

    def register(self, name: str, seq: list[str], cmd: Callable, **kwargs):
        """
        Helper to register a cheat command.

        :param name: Unique name for the cheat code.
        :type name: str

        :param seq: Sequence of key strings that trigger the cheat.
        :type seq: list[str]

        :param cmd: Callable to execute when the cheat is activated.
        :type cmd: Callable

        :param kwargs: Additional keyword arguments for cheat registration.
        """
        self.cheats.register_command(name, seq, cmd, **kwargs)

    def on_enter(self):
        """
        Called when the scene is entered.
        """
        # register codes here (or via a builder)

    def handle_event(self, event: Event) -> bool:
        """
        Handle an event.

        :param event: The event to handle.
        :type event: Event

        :param scene: The scene receiving the event.
        :type scene: TScene

        :return: True if the event was handled, False otherwise.
        :rtype: bool
        """
        if event.type == EventType.KEYDOWN:
            self.cheats.process_event(event, self.scene)
        return False  # usually don't consume
