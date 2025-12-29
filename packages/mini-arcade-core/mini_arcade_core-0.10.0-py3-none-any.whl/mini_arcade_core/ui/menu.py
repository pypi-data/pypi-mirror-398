"""
Menu system for mini arcade core.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, Sequence

from mini_arcade_core.backend import Backend, Color, Event, EventType
from mini_arcade_core.commands import BaseCommand, QuitGameCommand
from mini_arcade_core.game import Game
from mini_arcade_core.keymaps import Key
from mini_arcade_core.scenes import BaseSceneSystem, Scene, SceneModel
from mini_arcade_core.spaces.d2 import Size2D


@dataclass(frozen=True)
class MenuItem:
    """
    Represents a single item in a menu.

    :ivar label (str): The text label of the menu item.
    :ivar on_select (BaseCommand): The action to perform when the item is selected.
    """

    id: str
    label: str
    on_select: BaseCommand
    label_fn: Optional[Callable[[Game], str]] = None

    def resolved_label(self, game: Game) -> str:
        """
        Get the resolved label for this menu item.

        :param game: The current game instance.
        :type game: Game

        :return: The resolved label string.
        :rtype: str
        """
        return self.label_fn(game) if self.label_fn else self.label


# Justification: Data container for styling options needs
# some attributes.
# pylint: disable=too-many-instance-attributes
@dataclass
class MenuStyle:
    """
    Styling options for the Menu.

    :ivar normal (Color): Color for unselected items.
    :ivar selected (Color): Color for the selected item.
    :ivar line_height (int): Vertical spacing between items.
    :ivar title_color (Color): Color for the title text.
    :ivar title_spacing (int): Vertical space between title and first item.
    :ivar title_margin_bottom (int): Additional margin below the title.
    :ivar background_color (Color | None): Solid background color for the menu.
    :ivar overlay_color (Color | None): Full-screen overlay color.
    :ivar panel_color (Color | None): Color for the panel behind content.
    :ivar panel_padding_x (int): Horizontal padding inside the panel.
    :ivar panel_padding_y (int): Vertical padding inside the panel.
    :ivar button_enabled (bool): Whether to render items as buttons.
    :ivar button_fill (Color): Fill color for buttons.
    :ivar button_border (Color): Border color for buttons.
    :ivar button_selected_border (Color): Border color for the selected button.
    :ivar button_width (int | None): Fixed width for buttons, or None for auto-fit.
    :ivar button_height (int): Fixed height for buttons.
    :ivar button_gap (int): Vertical gap between buttons.
    :ivar button_padding_x (int): Horizontal padding inside buttons.
    :ivar hint (str | None): Optional hint text to display at the bottom.
    :ivar hint_color (Color): Color for the hint text.
    :ivar hint_margin_bottom (int): Additional margin below the hint text.
    :ivar title_font_size (int): Font size for the title text.
    :ivar hint_font_size (int): Font size for the hint text.
    :ivar item_font_size (int): Font size for the menu items.
    """

    normal: Color = (220, 220, 220)
    selected: Color = (255, 255, 0)

    # Layout
    line_height: int = 28
    title_color: Color = (255, 255, 255)
    title_spacing: int = 18
    title_margin_bottom: int = 20

    # Scene background (solid)
    background_color: Color | None = None  # e.g. BACKGROUND

    # Optional full-screen overlay (dim)
    overlay_color: Color | None = None  # e.g. (0,0,0,0.5) for pause

    # Panel behind content (optional)
    panel_color: Color | None = None
    panel_padding_x: int = 24
    panel_padding_y: int = 18

    # Button rendering (optional)
    button_enabled: bool = False
    button_fill: Color = (30, 30, 30, 1.0)
    button_border: Color = (120, 120, 120, 1.0)
    button_selected_border: Color = (255, 255, 0, 1.0)
    button_width: int | None = (
        None  # if None -> auto-fit to longest label + padding
    )
    button_height: int = 40
    button_gap: int = 20
    button_padding_x: int = 20  # used for auto-fit + text centering

    # Hint footer (optional)
    hint: str | None = None
    hint_color: Color = (200, 200, 200)
    hint_margin_bottom: int = 50

    # Font sizes (not used directly here, but for reference)
    title_font_size = 44
    hint_font_size = 14
    item_font_size = 24


class Menu:
    """A simple text-based menu system."""

    # Justification: Multiple attributes for menu state
    # pylint: disable=too-many-arguments
    def __init__(
        self,
        items: Sequence[MenuItem],
        *,
        viewport: Size2D | None = None,
        title: str | None = None,
        style: MenuStyle | None = None,
        on_select: Optional[Callable[[MenuItem], None]] = None,
    ):
        """
        :param items: Sequence of MenuItem instances to display.
        :type items: Sequence[MenuItem]

        :param viewport: Viewport size for the menu's layout and centering.
        :type viewport: Size2D | None

        :param title: Optional title text for the menu.
        :type title: str | None

        :param style: Optional MenuStyle for customizing appearance.
        :type style: MenuStyle | None
        """
        self.items = list(items)
        self.viewport = viewport
        self.title = title
        self.style = style or MenuStyle()
        self.selected_index = 0
        self._on_select = on_select
        self._max_content_w_seen = 0
        self._max_button_w_seen = 0
        self.stable_width = True

    # pylint: enable=too-many-arguments

    def set_labels(self, labels: Sequence[str]):
        """Set the labels of the menu items.
        :param labels: Sequence of new labels for the menu items.
        :type labels: Sequence[str]
        """
        for index, label in enumerate(labels):
            if index < len(self.items):
                item = self.items[index]
                self.items[index] = MenuItem(
                    id=item.id,
                    label=label,
                    on_select=item.on_select,
                    label_fn=item.label_fn,
                )

    def move_up(self):
        """Move the selection up by one item, wrapping around if necessary."""
        if self.items:
            self.selected_index = (self.selected_index - 1) % len(self.items)

    def move_down(self):
        """Move the selection down by one item, wrapping around if necessary."""
        if self.items:
            self.selected_index = (self.selected_index + 1) % len(self.items)

    def select(self):
        """Select the currently highlighted item, invoking its action."""
        if not self.items:
            return
        item = self.items[self.selected_index]
        if self._on_select is not None:
            self._on_select(item)

    def handle_event(
        self,
        event: Event,
        *,
        up_key: int,
        down_key: int,
        select_key: int,
    ) -> bool:
        """
        Handle an input event to navigate the menu.

        :param event: The input event to handle.
        :type event: Event

        :param up_key: Key code for moving selection up.
        type up_key: int

        :param down_key: Key code for moving selection down.
        :type down_key: int

        :param select_key: Key code for selecting the current item.
        :type select_key: int
        """
        if event.type != EventType.KEYDOWN or event.key is None:
            return False

        if event.key == up_key:
            self.move_up()
            return True
        if event.key == down_key:
            self.move_down()
            return True
        if event.key == select_key:
            self.select()
            return True

        return False

    def draw(self, surface: Backend):
        """
        Draw the menu onto the given backend surface.

        :param surface: The backend surface to draw on.
        :type surface: Backend
        """
        if self.viewport is None:
            raise ValueError(
                "Menu requires viewport=Size2D for centering/layout"
            )

        vw, vh = self.viewport.width, self.viewport.height

        # 0) Solid background (for main menus)
        if self.style.background_color is not None:
            surface.draw_rect(0, 0, vw, vh, color=self.style.background_color)

        # 1) Overlay (for pause, etc.)
        if self.style.overlay_color is not None:
            surface.draw_rect(0, 0, vw, vh, color=self.style.overlay_color)

        # 2) Compute menu content bounds (panel area)
        content_w, content_h, title_h = self._measure_content(surface)

        pad_x, pad_y = self.style.panel_padding_x, self.style.panel_padding_y
        panel_w = content_w + pad_x * 2
        panel_h = content_h + pad_y * 2

        x0 = (vw - panel_w) // 2
        y0 = (vh - panel_h) // 2

        # Optional vertical offset if you add it later:
        # y0 += self.style.center_offset_y

        # 3) Panel (optional)
        if self.style.panel_color is not None:
            surface.draw_rect(
                x0, y0, panel_w, panel_h, color=self.style.panel_color
            )

        # 4) Draw title + items
        cursor_y = y0 + pad_y
        x_center = x0 + (panel_w // 2)

        if self.title:
            self._draw_text_center_x(
                surface,
                x_center,
                cursor_y,
                self.title,
                color=self.style.title_color,
                font_size=self.style.title_font_size,
            )
            cursor_y += (
                title_h
                + self.style.title_spacing
                + self.style.title_margin_bottom
            )

        if self.style.button_enabled:
            self._draw_buttons(surface, x_center, cursor_y)
        else:
            self._draw_text_items(surface, x_center, cursor_y)

        # 5) Hint footer (optional)
        if self.style.hint:
            self._draw_text_center_x(
                surface,
                vw // 2,
                vh - self.style.hint_margin_bottom,
                self.style.hint,
                color=self.style.hint_color,
                font_size=self.style.hint_font_size,
            )

    def _draw_text_items(self, surface: Backend, x_center: int, cursor_y: int):
        for i, item in enumerate(self.items):
            color = (
                self.style.selected
                if i == self.selected_index
                else self.style.normal
            )
            self._draw_text_center_x(
                surface,
                x_center,
                cursor_y + i * self.style.line_height,
                item.label,
                color=color,
                font_size=self.style.item_font_size,
            )

    # Justification: Local variables for layout calculations
    # pylint: disable=too-many-locals
    def _draw_buttons(self, surface: Backend, x_center: int, cursor_y: int):
        # Determine button width: fixed or auto-fit
        if self.style.button_width is not None:
            bw = self.style.button_width
        else:
            max_label_w = 0
            for it in self.items:
                w, _ = surface.measure_text(
                    it.label, font_size=self.style.item_font_size
                )
                max_label_w = max(max_label_w, w)
            bw = max_label_w + self.style.button_padding_x * 2

            # ✅ Sticky button width (never shrink)
            if self.stable_width:
                self._max_button_w_seen = max(self._max_button_w_seen, bw)
                bw = self._max_button_w_seen

        bh = self.style.button_height
        gap = self.style.button_gap

        # We treat cursor_y as “top of first button”
        for i, item in enumerate(self.items):
            y = cursor_y + i * (bh + gap)
            x = x_center - bw // 2

            selected = i == self.selected_index
            border = (
                self.style.button_selected_border
                if selected
                else self.style.button_border
            )

            # Border rect
            surface.draw_rect(x - 4, y - 4, bw + 8, bh + 8, color=border)
            # Fill rect
            surface.draw_rect(x, y, bw, bh, color=self.style.button_fill)

            # Label color
            text_color = self.style.selected if selected else self.style.normal
            tw, th = surface.measure_text(
                item.label, font_size=self.style.item_font_size
            )
            tx = x + (bw - tw) // 2
            ty = y + (bh - th) // 2
            surface.draw_text(
                tx,
                ty,
                item.label,
                color=text_color,
                font_size=self.style.item_font_size,
            )

    # pylint: enable=too-many-locals

    def _measure_content(self, surface: Backend) -> tuple[int, int, int]:
        # If button mode: content height differs (button_height + gaps)
        max_w = 0
        title_h = 0

        # Title
        if self.title:
            tw, th = surface.measure_text(
                self.title, font_size=self.style.title_font_size
            )
            max_w = max(max_w, tw)
            title_h = th

        if not self.items:
            content_h = title_h if self.title else 0
            # Apply stable width even for empty items
            if self.stable_width:
                self._max_content_w_seen = max(self._max_content_w_seen, max_w)
                max_w = self._max_content_w_seen
            return max_w, content_h, title_h

        if self.style.button_enabled:
            # Width: fixed or auto-fit by longest label
            if self.style.button_width is not None:
                items_w = self.style.button_width
            else:
                max_label_w = 0
                for it in self.items:
                    w, _ = surface.measure_text(
                        it.label, font_size=self.style.item_font_size
                    )
                    max_label_w = max(max_label_w, w)
                items_w = max_label_w + self.style.button_padding_x * 2

            max_w = max(max_w, items_w)

            bh = self.style.button_height
            gap = self.style.button_gap
            items_h = len(self.items) * bh + (len(self.items) - 1) * gap
        else:
            for it in self.items:
                w, _ = surface.measure_text(
                    it.label, font_size=self.style.item_font_size
                )
                max_w = max(max_w, w)
            items_h = len(self.items) * self.style.line_height

        content_h = items_h
        if self.title:
            content_h += (
                title_h
                + self.style.title_spacing
                + self.style.title_margin_bottom
            )

        # ✅ Sticky width (never shrink)
        if self.stable_width:
            self._max_content_w_seen = max(self._max_content_w_seen, max_w)
            max_w = self._max_content_w_seen

        return max_w, content_h, title_h

    # Justification: Many arguments for text drawing utility
    # pylint: disable=too-many-arguments
    @staticmethod
    def _draw_text_center_x(
        surface: Backend,
        x_center: int,
        y: int,
        text: str,
        *,
        color: Color,
        font_size: int | None = None,
    ):
        w, _ = surface.measure_text(text, font_size=font_size)
        surface.draw_text(
            x_center - (w // 2), y, text, color=color, font_size=font_size
        )

    # pylint: enable=too-many-arguments


# pylint: enable=too-many-instance-attributes


@dataclass
class MenuModel(SceneModel):
    """Data model for menu scenes."""

    up_key: Key = Key.UP
    down_key: Key = Key.DOWN
    select_key: Key = Key.ENTER


class MenuSystem(BaseSceneSystem):
    """
    Scene system to manage menu interaction and rendering.

    :ivar menu (Menu): The Menu instance being managed.
    """

    menu: Menu
    scene: BaseMenuScene

    def __init__(self, scene):
        super().__init__(scene)
        self.menu: Menu | None = None

    def on_enter(self):
        self.menu = Menu(
            self.scene.menu_items(),
            viewport=self.scene.size,
            title=self.scene.menu_title,
            style=self.scene.menu_style(),
            on_select=lambda item: item.on_select.execute(self.scene.game),
        )

    def handle_event(self, event: Event) -> bool:
        if self.menu is None:
            return False

        # Let menu update selection; on select -> emit event / run command
        selected_action = self.menu.handle_event(
            event,
            up_key=self.scene.model.up_key,
            down_key=self.scene.model.down_key,
            select_key=self.scene.model.select_key,
        )
        return selected_action

    def draw(self, surface: Backend):
        self.menu.set_labels(
            [it.resolved_label(self.scene.game) for it in self.menu.items]
        )
        self.menu.draw(surface)


class BaseMenuScene(Scene):
    """
    Base scene class for menu-based scenes.

    :ivar model (MenuModel): The data model for the menu scene.
    """

    model: MenuModel

    def __init__(self, game: Game):
        super().__init__(game)
        self.model = MenuModel()

    # hooks
    @property
    def menu_title(self) -> str | None:
        """
        Optional title text for the menu.

        :return: Title string or None for no title.
        :rtype: str | None
        """
        return None

    def menu_style(self) -> MenuStyle:
        """
        MenuStyle instance for customizing menu appearance.

        :return: MenuStyle instance.
        :rtype: MenuStyle
        """
        return MenuStyle()

    def menu_items(self) -> list[MenuItem]:
        """
        Return the list of MenuItem instances for this menu.

        :return: List of MenuItem instances.
        :rtype: list[MenuItem]

        :raises NotImplementedError: If not overridden in subclass.
        """
        raise NotImplementedError

    def quit_command(self) -> BaseCommand[Game] | None:
        """
        Quit command to bind to ESCAPE and window close events.

        :return: BaseCommand instance to execute on quit, or None for no action.
        :rtype: BaseCommand[Game] | None
        """
        return QuitGameCommand()  # core default (optional)

    def on_enter(self):
        # install menu system (core)
        self.services.systems.add(MenuSystem(self))

        # bind quit if provided
        cmd = self.quit_command()
        if cmd:
            self.services.input.on_key_down(Key.ESCAPE, cmd, "quit")
            self.services.input.on_quit(cmd, "quit")

        self._systems_on_enter()

    def handle_event(self, event: Event):
        if self._systems_handle_event(event):
            return
        self.services.input.handle_event(event, self)

    def draw(self, surface: Backend):
        self._systems_draw(surface)

    def on_exit(self): ...

    def update(self, dt: float): ...
