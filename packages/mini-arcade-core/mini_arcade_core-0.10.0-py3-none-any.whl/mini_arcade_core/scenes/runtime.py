"""
Container for scene services like entity and overlay managers.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from mini_arcade_core.managers.entities import EntityManager
from mini_arcade_core.managers.inputs import InputManager
from mini_arcade_core.managers.overlays import OverlayManager
from mini_arcade_core.managers.system import SystemManager


@dataclass
class SceneRuntime:
    """
    Container for scene services like entity and overlay managers.

    :ivar input (InputManager): InputManager for handling input bindings and commands.
    :ivar entities (EntityManager): EntityManager for managing scene entities.
    :ivar overlays (OverlayManager): OverlayManager for managing scene overlays.
    :ivar systems (SystemManager): SystemManager for managing scene systems.
    """

    input: InputManager = field(default_factory=InputManager)
    entities: EntityManager = field(default_factory=EntityManager)
    overlays: OverlayManager = field(default_factory=OverlayManager)
    systems: SystemManager = field(default_factory=SystemManager)
