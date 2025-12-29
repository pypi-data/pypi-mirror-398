"""
Manager for scene systems.
"""

from __future__ import annotations

from dataclasses import dataclass

from mini_arcade_core.managers.base import ListManager
from mini_arcade_core.scenes.system import BaseSceneSystem


@dataclass
class SystemManager(ListManager[BaseSceneSystem]):
    """
    Manager for scene systems.
    """

    def sorted(self) -> list[BaseSceneSystem]:
        """
        Get systems sorted by priority.

        :return: List of systems sorted by priority.
        :rtype: list[BaseSceneSystem]
        """
        return sorted(self.items, key=lambda s: getattr(s, "priority", 0))
