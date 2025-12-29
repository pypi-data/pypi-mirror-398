"""
Game core module defining the Game class and configuration.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from time import perf_counter, sleep
from typing import TYPE_CHECKING, Literal, Union

from PIL import Image  # type: ignore[import]

from mini_arcade_core.backend import Backend
from mini_arcade_core.scenes.registry import SceneRegistry

if TYPE_CHECKING:  # avoid runtime circular import
    from mini_arcade_core.scenes import Scene

SceneOrId = Union["Scene", str]


@dataclass
class GameConfig:
    """
    Configuration options for the Game.

    :ivar width: Width of the game window in pixels.
    :ivar height: Height of the game window in pixels.
    :ivar title: Title of the game window.
    :ivar fps: Target frames per second.
    :ivar background_color: RGB background color.
    :ivar backend: Optional Backend instance to use for rendering and input.
    """

    width: int = 800
    height: int = 600
    title: str = "Mini Arcade Game"
    fps: int = 60
    background_color: tuple[int, int, int] = (0, 0, 0)
    backend: Backend | None = None


Difficulty = Literal["easy", "normal", "hard", "insane"]


@dataclass
class GameSettings:
    """
    Game settings that can be modified during gameplay.

    :ivar difficulty: Current game difficulty level.
    """

    difficulty: Difficulty = "normal"


@dataclass
class _StackEntry:
    scene: "Scene"
    as_overlay: bool = False


class Game:
    """Core game object responsible for managing the main loop and active scene."""

    def __init__(
        self, config: GameConfig, registry: SceneRegistry | None = None
    ):
        """
        :param config: Game configuration options.
        :type config: GameConfig

        :param registry: Optional SceneRegistry for scene management.
        :type registry: SceneRegistry | None

        :raises ValueError: If the provided config does not have a valid Backend.
        """
        self.config = config
        self._current_scene: Scene | None = None
        self._running: bool = False

        if config.backend is None:
            raise ValueError(
                "GameConfig.backend must be set to a Backend instance"
            )
        self.backend: Backend = config.backend
        self.registry = registry or SceneRegistry(_factories={})
        self._scene_stack: list[_StackEntry] = []
        self.settings = GameSettings()

    def current_scene(self) -> "Scene | None":
        """
        Get the currently active scene.

        :return: The active Scene instance, or None if no scene is active.
        :rtype: Scene | None
        """
        return self._scene_stack[-1].scene if self._scene_stack else None

    def change_scene(self, scene: SceneOrId):
        """
        Swap the active scene. Concrete implementations should call
        ``on_exit``/``on_enter`` appropriately.

        :param scene: The new scene to activate.
        :type scene: SceneOrId
        """
        scene = self._resolve_scene(scene)

        while self._scene_stack:
            entry = self._scene_stack.pop()
            entry.scene.on_exit()

        self._scene_stack.append(_StackEntry(scene=scene, as_overlay=False))
        scene.on_enter()

    def push_scene(self, scene: SceneOrId, as_overlay: bool = False):
        """
        Push a scene on top of the current one.
        If as_overlay=True, underlying scene(s) may still be drawn but never updated.

        :param scene: The scene to push onto the stack.
        :type scene: SceneOrId

        :param as_overlay: Whether to treat the scene as an overlay.
        :type as_overlay: bool
        """
        scene = self._resolve_scene(scene)

        top = self.current_scene()
        if top is not None:
            top.on_pause()

        self._scene_stack.append(
            _StackEntry(scene=scene, as_overlay=as_overlay)
        )
        scene.on_enter()

    def pop_scene(self) -> "Scene | None":
        """
        Pop the top scene. If stack becomes empty, quit.

        :return: The popped Scene instance, or None if the stack is now empty.
        :rtype: Scene | None
        """
        if not self._scene_stack:
            return None

        popped = self._scene_stack.pop()
        popped.scene.on_exit()

        top = self.current_scene()
        if top is None:
            self.quit()
            return popped.scene

        top.on_resume()
        return popped.scene

    def _visible_stack(self) -> list["Scene"]:
        """
        Return the list of scenes that should be drawn (base + overlays).
        We draw from the top-most non-overlay scene upward.
        """
        if not self._scene_stack:
            return []

        # find top-most base scene (as_overlay=False)
        base_idx = 0
        for i in range(len(self._scene_stack) - 1, -1, -1):
            if not self._scene_stack[i].as_overlay:
                base_idx = i
                break

        return [e.scene for e in self._scene_stack[base_idx:]]

    def quit(self):
        """Request that the main loop stops."""
        self._running = False

    def run(self, initial_scene: SceneOrId):
        """
        Run the main loop starting with the given scene.

        This is intentionally left abstract so you can plug pygame, pyglet,
        or another backend.

        :param initial_scene: The scene to start the game with.
        :type initial_scene: SceneOrId
        """
        backend = self.backend
        backend.init(self.config.width, self.config.height, self.config.title)

        br, bg, bb = self.config.background_color
        backend.set_clear_color(br, bg, bb)

        self.change_scene(initial_scene)

        self._running = True
        target_dt = 1.0 / self.config.fps if self.config.fps > 0 else 0.0
        last_time = perf_counter()

        while self._running:
            now = perf_counter()
            dt = now - last_time
            last_time = now

            top = self.current_scene()
            if top is None:
                break

            for ev in backend.poll_events():
                top.handle_event(ev)

            top.update(dt)

            backend.begin_frame()
            for scene in self._visible_stack():
                scene.draw(backend)
            backend.end_frame()

            if target_dt > 0 and dt < target_dt:
                sleep(target_dt - dt)

        # exit remaining scenes
        while self._scene_stack:
            entry = self._scene_stack.pop()
            entry.scene.on_exit()

    @staticmethod
    def _convert_bmp_to_image(bmp_path: str, out_path: str) -> bool:
        """
        Convert a BMP file to another image format using Pillow.

        :param bmp_path: Path to the input BMP file.
        :type bmp_path: str

        :param out_path: Path to the output image file.
        :type out_path: str

        :return: True if conversion was successful, False otherwise.
        :rtype: bool
        """
        try:
            img = Image.open(bmp_path)
            img.save(out_path)  # Pillow chooses format from extension
            return True
        # Justification: Pillow can raise various exceptions on failure
        # pylint: disable=broad-exception-caught
        except Exception:
            return False
        # pylint: enable=broad-exception-caught

    def screenshot(
        self, label: str | None = None, directory: str = "screenshots"
    ) -> str | None:
        """
        Ask backend to save a screenshot. Returns the file path or None.

        :param label: Optional label to include in the filename.
        :type label: str | None

        :param directory: Directory to save screenshots in.
        :type directory: str

        :return: The file path of the saved screenshot, or None on failure.
        :rtype: str | None
        """
        os.makedirs(directory, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        label = label or "shot"
        filename = f"{stamp}_{label}"
        bmp_path = os.path.join(directory, f"{filename}.bmp")

        if self.backend.capture_frame(bmp_path):
            out_path = Path(directory) / f"{filename}.png"
            self._convert_bmp_to_image(bmp_path, str(out_path))
            return str(out_path)
        return None

    def _resolve_scene(self, scene: SceneOrId) -> "Scene":
        if isinstance(scene, str):
            return self.registry.create(scene, self)
        return scene
