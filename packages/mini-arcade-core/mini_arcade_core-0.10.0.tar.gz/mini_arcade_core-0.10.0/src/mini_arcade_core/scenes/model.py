"""
Scene base model module.
Provides the Scene class and related services.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any


@dataclass
class SceneModel:
    """
    Basic data model for a scene.
    """

    @staticmethod
    def _serialize_dataclass(obj) -> dict[str, Any]:
        out = {}
        for f in fields(obj):
            if f.metadata.get("serialize", True) is False:
                continue
            out[f.name] = getattr(obj, f.name)
        return out

    def to_dict(self) -> dict:
        """
        Convert the SceneModel to a dictionary.

        :return: Dictionary representation of the SceneModel.
        :rtype: dict
        """
        return self._serialize_dataclass(self)
