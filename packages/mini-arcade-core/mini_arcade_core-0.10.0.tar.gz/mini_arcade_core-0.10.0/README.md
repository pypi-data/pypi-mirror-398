# mini-arcade-core 🎮

Tiny Python game core for building simple scene-based arcade games  
(Pong, Breakout, Space Invaders, etc.).

> Minimal, opinionated abstractions: **Game**, **Scene**, and **Entity** – nothing else.

---

## Features

- 🎯 **Tiny API surface**
  - `GameConfig` – basic window & FPS configuration
  - `Game` – abstract game core to plug your own backend (e.g. pygame)
  - `Scene` – base class for screens/states (menus, gameplay, pause)
  - `Entity` / `SpriteEntity` – simple game object primitives
  - `run_game()` – convenience helper once a concrete `Game` backend is wired

- 🧩 **Backend-agnostic**
  - The core doesn’t depend on any specific rendering/input library.
  - You can build backends using `pygame`, `pyglet`, or something custom.

- 🕹️ **Perfect for small arcade projects**
  - Pong, Breakout, Snake, Asteroids-likes, runners, flappy-likes, etc.
  - Great for learning, experiments, and portfolio-friendly mini games.

---

## Installation

> **Note:** Adjust this once it’s on PyPI.

```bash
# From a local checkout
pip install -e .
```

Or, once published:

```bash
pip install mini-arcade-core
```

Requires Python 3.9–3.11.

---

## Core Concepts

### ``GameConfig``

Basic configuration for your game:

```python
from mini_arcade_core import GameConfig

config = GameConfig(
    width=800,
    height=600,
    title="My Mini Arcade Game",
    fps=60,
    background_color=(0, 0, 0),  # RGB
)
```

### ``Game``

Abstract base class that owns:

- the main loop
- the active ``Scene``
- high-level control like ``run()`` and ``change_scene()``

You subclass ``Game`` to plug in your rendering/input backend.

### ``Scene``

Represents one state of your game (menu, gameplay, pause, etc.):

```python
from mini_arcade_core import Scene, Game

class MyScene(Scene):
    def on_enter(self):
        print("Scene entered")

    def on_exit(self):
        print("Scene exited")

    def handle_event(self, event: object):
        # Handle input / events from your backend
        pass

    def update(self, dt: float):
        # Game logic
        pass

    def draw(self, surface: object):
        # Rendering via your backend
        pass
```

### ``Entity`` & ``SpriteEntity``

Lightweight game object primitives:

```python
from mini_arcade_core import Entity, SpriteEntity

class Ball(Entity):
    def __init__(self):
        self.x = 100.0
        self.y = 100.0
        self.vx = 200.0
        self.vy = 150.0

    def update(self, dt: float):
        self.x += self.vx * dt
        self.y += self.vy * dt

    def draw(self, surface: object):
        # Use your backend to draw the ball on `surface`
        pass

paddle = SpriteEntity(x=50.0, y=300.0, width=80, height=16)
```

---

### Example: Minimal pygame Backend

``mini-arcade-core`` doesn’t force any backend.
Here’s a minimal example using pygame as a backend:

```python
# example_pygame_game.py

import pygame
from mini_arcade_core import Game, GameConfig, Scene


class PygameGame(Game):
    def __init__(self, config: GameConfig):
        super().__init__(config)
        pygame.init()
        self._screen = pygame.display.set_mode(
            (config.width, config.height)
        )
        pygame.display.set_caption(config.title)
        self._clock = pygame.time.Clock()

    def change_scene(self, scene: Scene):
        if self._current_scene is not None:
            self._current_scene.on_exit()
        self._current_scene = scene
        self._current_scene.on_enter()

    def run(self, initial_scene: Scene):
        self.change_scene(initial_scene)
        self._running = True

        while self._running:
            dt = self._clock.tick(self.config.fps) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False
                elif self._current_scene is not None:
                    self._current_scene.handle_event(event)

            if self._current_scene is not None:
                self._current_scene.update(dt)
                self._screen.fill(self.config.background_color)
                self._current_scene.draw(self._screen)
                pygame.display.flip()

        pygame.quit()


class PongScene(Scene):
    def __init__(self, game: Game):
        super().__init__(game)
        self.x = 100.0
        self.y = 100.0
        self.vx = 200.0
        self.vy = 150.0
        self.radius = 10

    def on_enter(self):
        print("Pong started")

    def on_exit(self):
        print("Pong finished")

    def handle_event(self, event: object):
        # no input yet
        pass

    def update(self, dt: float):
        self.x += self.vx * dt
        self.y += self.vy * dt

        width = self.game.config.width
        height = self.game.config.height

        if self.x < self.radius or self.x > width - self.radius:
            self.vx *= -1
        if self.y < self.radius or self.y > height - self.radius:
            self.vy *= -1

    def draw(self, surface: pygame.Surface):  # type: ignore[override]
        pygame.draw.circle(
            surface, (255, 255, 255), (int(self.x), int(self.y)), self.radius
        )


if __name__ == "__main__":
    cfg = GameConfig(width=640, height=360, title="Mini Arcade - Pong")
    game = PygameGame(cfg)
    scene = PongScene(game)
    game.run(scene)
```

Once you have a shared backend like PygameGame in its own package (or inside your game repo), you can also wire run_game() to use it instead of the abstract Game.

---

## Testing

This project uses pytest for tests.

```bash
pip install -e ".[dev]"
pytest
```

### Roadmap

[ ] First concrete backend (e.g. ``mini-arcade-pygame``)
[ ] Example games: Pong, Breakout, Snake, Asteroids-lite, Endless Runner
[ ] Packaging the example games as separate repos using this core

## License

![License: MIT License](https://img.shields.io/badge/License-mit-blue.svg) — feel free to use this as a learning tool, or as a base for your own mini arcade projects.
