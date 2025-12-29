"""
Input manager for handling input bindings and commands.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, Dict, Optional

from mini_arcade_core.backend import Event, EventType
from mini_arcade_core.commands import BaseCommand, BaseSceneCommand
from mini_arcade_core.keymaps import Key

if TYPE_CHECKING:
    from mini_arcade_core.scenes.scene import Scene

logger = logging.getLogger(__name__)


Predicate = Callable[["Event"], bool]


@dataclass(frozen=True)
class InputBinding:
    """
    Defines an input binding.

    :ivar action (str): The action name.
    :ivar command (BaseCommand): The command to execute.
    :ivar predicate (Predicate): Predicate to match events.
    """

    action: str
    command: BaseCommand
    predicate: Predicate  # decides whether this binding matches an event


class InputManager:
    """
    Manager for handling input bindings and commands.
    """

    def __init__(self):
        # event_type -> key -> action -> command
        self._bindings: Dict[EventType, Dict[Key, Dict[str, BaseCommand]]] = {}

    # Justification: The method needs multiple optional parameters for flexibility.
    # pylint: disable=too-many-arguments
    def bind(
        self,
        event_type: EventType,
        action: str,
        command: BaseCommand,
        *,
        key: Optional[Key] = None,
        button: Optional[int] = None,
        predicate: Optional[Predicate] = None,
    ):
        """
        Generic binding.

        You can filter by:
        - key: for KEYDOWN/KEYUP
        - button: for MOUSEBUTTONDOWN/MOUSEBUTTONUP (if your Event exposes it)
        - predicate: custom matcher (for anything)

        :param event_type: The type of event to bind to.
        :type event_type: EventType

        :param action: The action name for the binding.
        :type action: str

        :param command: The command to execute when the binding is triggered.
        :type command: BaseCommand

        :param key: Optional key to filter KEYDOWN/KEYUP events.
        :type key: Key | None

        :param button: Optional button to filter MOUSEBUTTONDOWN/MOUSEBUTTONUP events.
        :type button: int | None

        :param predicate: Optional custom predicate to match events.
        :type predicate: Predicate | None
        """
        logger.debug(
            f"Binding {action} to {event_type} with key={key}, button={button}"
        )

        def default_predicate(ev: Event) -> bool:
            if key is not None and getattr(ev, "key", None) != key:
                return False
            if button is not None and getattr(ev, "button", None) != button:
                return False
            return True

        pred = predicate or default_predicate
        self._bindings.setdefault(event_type, []).append(
            InputBinding(action=action, command=command, predicate=pred)
        )

    # pylint: enable=too-many-arguments

    def unbind(self, event_type: EventType, action: str):
        """
        Remove bindings by action for an event type.

        :param event_type: The type of event to unbind from.
        :type event_type: EventType

        :param action: The action name of the binding to remove.
        :type action: str
        """
        lst = self._bindings.get(event_type, [])
        self._bindings[event_type] = [b for b in lst if b.action != action]

    def clear(self):
        """Clear all input bindings."""
        self._bindings.clear()

    def handle_event(self, event: Event, scene: Scene):
        """
        Handle an incoming event, executing any matching commands.

        :param event: The event to handle.
        :type event: Event

        :param scene: The current scene context.
        :type scene: Scene
        """
        et = event.type

        for binding in self._bindings.get(et, []):
            if binding.predicate(event):
                to_inject = (
                    scene.model
                    if isinstance(binding.command, BaseSceneCommand)
                    else scene.game
                )
                binding.command.execute(to_inject)

    # --- Convenience API ------------------------------------------------------

    def on_quit(self, command: BaseCommand, action: str = "quit"):
        """
        Bind a command to the QUIT event.

        :param command: The command to execute on quit.
        :type command: BaseCommand

        :param action: The action name for the binding.
        :type action: str
        """
        self.bind(EventType.QUIT, action=action, command=command)

    def on_key_down(self, key: Key, command: BaseCommand, action: str):
        """
        Bind a command to a key down event.

        :param key: The key to bind to.
        :type key: Key

        :param command: The command to execute on key down.
        :type command: BaseCommand

        :param action: The action name for the binding.
        :type action: str
        """
        self.bind(EventType.KEYDOWN, key=key, action=action, command=command)

    def on_key_up(self, key: Key, command: BaseCommand, action: str):
        """
        Bind a command to a key up event.

        :param key: The key to bind to.
        :type key: Key

        :param command: The command to execute on key up.
        :type command: BaseCommand

        :param action: The action name for the binding.
        :type action: str
        """
        self.bind(EventType.KEYUP, key=key, action=action, command=command)

    def on_mouse_button_down(
        self, button: int, command: BaseCommand, action: str
    ):
        """
        Bind a command to a mouse button down event.

        :param button: The mouse button to bind to.
        :type button: int

        :param command: The command to execute on mouse button down.
        :type command: BaseCommand

        :param action: The action name for the binding.
        :type action: str
        """
        self.bind(
            EventType.MOUSEBUTTONDOWN,
            button=button,
            action=action,
            command=command,
        )

    def on_mouse_button_up(
        self, button: int, command: BaseCommand, action: str
    ):
        """
        Bind a command to a mouse button up event.

        :param button: The mouse button to bind to.
        :type button: int

        :param command: The command to execute on mouse button up.
        :type command: BaseCommand

        :param action: The action name for the binding.
        :type action: str
        """
        self.bind(
            EventType.MOUSEBUTTONUP,
            button=button,
            action=action,
            command=command,
        )

    def on_mouse_motion(
        self, command: BaseCommand, action: str = "mouse_motion"
    ):
        """
        Bind a command to mouse motion events.

        :param command: The command to execute on mouse motion.
        :type command: BaseCommand

        :param action: The action name for the binding.
        :type action: str
        """
        self.bind(EventType.MOUSEMOTION, action=action, command=command)

    def on_mouse_wheel(
        self, command: BaseCommand, action: str = "mouse_wheel"
    ):
        """
        Bind a command to mouse wheel events.

        :param command: The command to execute on mouse wheel.
        :type command: BaseCommand

        :param action: The action name for the binding.
        :type action: str
        """
        self.bind(EventType.MOUSEWHEEL, action=action, command=command)

    def on_window_resized(
        self, command: BaseCommand, action: str = "window_resized"
    ):
        """
        Bind a command to window resized events.

        :param command: The command to execute on window resize.
        :type command: BaseCommand

        :param action: The action name for the binding.
        :type action: str
        """
        self.bind(EventType.WINDOWRESIZED, action=action, command=command)

    def on_text_input(self, command: BaseCommand, action: str = "text_input"):
        """
        Bind a command to text input events.

        :param command: The command to execute on text input.
        :type command: BaseCommand

        :param action: The action name for the binding.
        :type action: str
        """
        self.bind(EventType.TEXTINPUT, action=action, command=command)
