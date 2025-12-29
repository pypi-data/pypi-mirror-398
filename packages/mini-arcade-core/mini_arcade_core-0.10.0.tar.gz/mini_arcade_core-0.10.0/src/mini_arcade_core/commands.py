"""
Command protocol for executing commands with a given context.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, Protocol, TypeVar

from mini_arcade_core.game import Game
from mini_arcade_core.scenes.model import SceneModel

if TYPE_CHECKING:
    from mini_arcade_core.scenes.scene import Scene

# Justification: Generic type for context
# pylint: disable=invalid-name
TContext = TypeVar("TContext")
# pylint: enable=invalid-name


class BaseCommand(Protocol, Generic[TContext]):
    """
    Protocol for a command that can be executed with a given context.
    """

    def __call__(self, context: TContext) -> None:
        """
        Execute the cheat code with the given context.

        :param context: Context object for cheat execution.
        :type context: TContext
        """
        self.execute(context)

    def execute(self, context: TContext):
        """
        Execute the command with the given context.

        :param context: Context object for command execution.
        :type context: TContext
        """


class BaseGameCommand(BaseCommand[Game]):
    """
    Base class for commands that operate on the Game context.
    """

    def execute(self, context: Game) -> None:
        """
        Execute the command with the given Game context.

        :param context: Game context for command execution.
        :type context: Game
        """
        raise NotImplementedError(
            "Execute method must be implemented by subclasses."
        )


class BaseSceneCommand(BaseCommand[SceneModel]):
    """
    Base class for commands that operate on the Scene SceneModel context within a scene.
    """

    def execute(self, context: SceneModel) -> None:
        """
        Execute the command with the given Scene Model context.

        :param context: Scene Model context for command execution.
        :type context: SceneModel
        """
        raise NotImplementedError(
            "Execute method must be implemented by subclasses."
        )


class QuitGameCommand(BaseGameCommand):
    """
    Command to quit the game.
    """

    def execute(self, context: Game) -> None:
        context.quit()
