from __future__ import annotations

import logging
from enum import Enum
from typing import Any, Generic, TypeVar

import pygame

from mima.standalone.transformed_view import TileTransformedView

LOG = logging.getLogger(__name__)

V = TypeVar("V")
S = TypeVar("S")


class Position(Enum):
    FULL = 0  # One Window
    TOP = 1  # Two or three Windows
    BOTTOM = 2  # Two or three Windows
    LEFT = 3  # Two or three Windows
    RIGHT = 4  # Two or three Windows
    TOP_LEFT = 5  # Three or four Windows
    TOP_RIGHT = 6  # Three or four Windows
    BOTTOM_LEFT = 7  # Three or four Windows
    BOTTOM_RIGHT = 8  # Three or four Windows
    CUSTOM = 9  # Custom size and position


class View(Generic[V]):
    """A view displays things on certain areas of the screen."""

    def __init__(
        self,
        view_type: V,
        screen: pygame.Surface,
        position: Position = Position.FULL,
        tile_size: pygame.Vector2 | None = None,
        *,
        pixel_pos: pygame.Vector2 | None = None,
        pixel_size: pygame.Vector2 | None = None,
        pixel_scale: float = 1.0,
    ) -> None:
        self._view_type = view_type
        self._screen = screen
        self._position = position
        self._tile_size = pygame.Vector2(1, 1) if tile_size is None else tile_size

        if position == Position.CUSTOM:
            self._pos = pygame.Vector2(0, 0) if pixel_pos is None else pixel_pos
            self._size = (
                pygame.Vector2(screen.get_size()) if pixel_size is None else pixel_size
            )
        else:
            self._pos, self._size = position_to_screen_rect(
                position, pygame.Vector2(0, 0), pygame.Vector2(screen.get_size())
            )

        self.ttv = TileTransformedView(
            self._screen, self._size, self._tile_size, pixel_scale
        )

        self.ttv._pos = self._pos
        self._window: Window | None = None

    def enter_focus(self, data: dict[str, Any]) -> None:
        """Prepare this view for presentation.

        This function is called when this view enters the screen. Data provided
        from the previous view is stored in ``data``.

        Args:
            data: Data from previous view (provided via ``push_view``)
        """
        return

    def _enter_focus(self, data: dict[str, Any] | None) -> None:
        LOG.debug("%s (%s) enter focus", self, self._view_type)
        self.enter_focus(data or {})

    def exit_focus(self) -> dict[str, Any] | None:
        """Clean-up when this view leaves the screen.

        This function is called before a new view is presented. Additional data
        can be passed to potential following views.

        Returns:
            A dict with data for a following scene or None. The other scene has
            to explicitly call ``get_data_from_previous_view()`` to retrieve
            the data. For most cases, it is recommended to use ``push_view()``
            to pass data directly to the ``enter_focus()`` because it gives more
            control over what data to pass to which following view.
        """
        return

    def _exit_focus(self) -> dict[str, Any]:
        LOG.debug("%s (%s) exit focus.", self, self._view_type)
        return self.exit_focus() or {}

    def handle_input(
        self, events: list[pygame.event.Event] | None
    ) -> list[pygame.event.Event]:
        events = self.ttv.handle_pan_and_zoom(events=events)

        return events

    def update(self, elapsed_time: float) -> bool:
        return True

    def draw(self) -> None:
        pass

    def get_type(self) -> V:
        return self._view_type

    def set_window(self, window: Window, position: Position = Position.FULL) -> None:
        self._window = window
        self._position = position
        self._pos, self._size = position_to_screen_rect(
            position, pygame.Vector2(0, 0), pygame.Vector2(self._screen.get_size())
        )

        self.ttv._view_area = self._size
        self.ttv.set_pos(self._pos)

    def get_window(self) -> Window[V]:
        if self._window is None:
            msg = "Window is not initialized yet!"
            raise ValueError(msg)
        return self._window

    def get_scene(self) -> Scene[V]:
        return self.get_window().get_scene()

    def push_scene(
        self, key: Any, data_for_scene: dict[str, Any] | None = None
    ) -> None:
        self.get_window().get_scene().get_manager().push_scene(key, data_for_scene)

    def pop_scene(self, empty_ok: bool = False) -> Any | None:
        return self.get_window().get_scene().get_manager().pop_scene(empty_ok)

    def push_view(self, key: Any, data_for_view: dict[str, Any] | None = None) -> None:
        self.get_window().push_view(key, data_for_view)

    def pop_view(self, empty_ok: bool = False) -> V | None:
        return self.get_window().pop_view(empty_ok)

    def get_screen_area(self) -> tuple[pygame.Vector2, pygame.Vector2]:
        return self.ttv.get_pos(), self.ttv.get_view_area()

    def get_data_from_previous_view(self) -> dict[str, Any] | None:
        return self.get_window().get_data_from_previous_view()


class Window(Generic[V]):
    """A class that manages different views."""

    def __init__(self, pos: Position) -> None:
        self._views: dict[V, View] = {}
        self._view: View[V] | None = None
        self._view_stack: list[V] = []
        self._stack_changed: bool = False
        self._scene: Scene | None = None
        self._pos: Position = pos
        self._data_for_view: dict[str, Any] = {}
        self._data_from_view: dict[str, Any] = {}

    def add_view(self, view: View[V]) -> None:
        view.set_window(self, self._pos)
        self._views[view.get_type()] = view

    def push_view(self, view: V, data_for_view: dict[str, Any] | None = None) -> None:
        self._view_stack.append(view)
        self._stack_changed = True
        self._data_for_view = {} if data_for_view is None else data_for_view

    def pop_view(self, empty_ok: bool = False) -> V | None:
        self._stack_changed = True
        if self._view_stack:
            return self._view_stack.pop()
        elif empty_ok:
            return None
        else:
            msg = "Stack is empty. Set `empty_ok` to True if you don't mind."
            raise IndexError(msg)

    def enter_focus(self, data: dict[str, Any]) -> None:
        LOG.debug("%s enter focus", self)
        if self._view_stack and self._view is not None:
            self._view._enter_focus(data)
        return

    def exit_focus(self) -> dict[str, Any]:
        LOG.debug("%s exit focus", self)
        data = {}
        if not self._view_stack:
            return data
        if self._view is not None:
            data = self._view._exit_focus()

        return {} if data is None else data

    def get_data_from_previous_view(self) -> dict[str, Any] | None:
        return self._data_from_view

    def handle_input(
        self, events: list[pygame.event.Event]
    ) -> list[pygame.event.Event]:
        if self._view is not None:
            return self._view.handle_input(events)
        return events

    def update(self, elapsed_time: float) -> bool:
        if not self._view_stack:
            return True
        old_view = self._view
        self._view = self._views[self._view_stack[-1]]

        if self._view != old_view or self._stack_changed:
            self._stack_changed = False
            if old_view is not None:
                self._data_from_view = old_view._exit_focus()

            self._view._enter_focus(self._data_for_view)

        if self._view is not None:
            return self._view.update(elapsed_time)
        else:
            return True

    def draw(self) -> None:
        if self._view is not None:
            self._view._screen.set_clip(self._view.get_screen_area())
            self._view.draw()
            self._view._screen.set_clip(None)

    def set_scene(self, scene: Scene[V]) -> None:
        self._scene = scene

    def get_scene(self) -> Scene[V]:
        if self._scene is None:
            msg = "Scene is not initialized yet!"
            raise ValueError(msg)
        return self._scene


class Scene(Generic[V]):
    """A scene can have multiple windows aka split-screen."""

    def __init__(self) -> None:
        self._windows: dict[int, Window[V]] = {}
        self._manager: SceneManager | None = None

    def add_window(self, win: Window[V], key: int = 0) -> None:
        self._windows[key] = win

    def enter_focus(self, data: dict[str, Any]) -> None:
        return

    def _enter_focus(self, data: dict[str, Any]) -> None:
        LOG.debug("%s enter focus", self)
        self.enter_focus(data)
        for win in self._windows.values():
            win.enter_focus(data)

    def exit_focus(self) -> dict[str, Any]:
        return {}

    def _exit_focus(self) -> dict[str, Any]:
        LOG.debug("%s exit focus", self)
        data = {}
        for key, win in self._windows.items():
            data[key] = win.exit_focus()

        return self.exit_focus()

    def handle_input(
        self, events: list[pygame.event.Event] | None = None
    ) -> list[pygame.event.Event]:
        if events is None:
            events = [e for e in pygame.event.get()]

        for window in self._windows.values():
            events = window.handle_input(events)

        return events

    def update(self, elapsed_time: float) -> bool:
        return False

    def _update(self, elapsed_time: float) -> bool:
        success = self.update(elapsed_time)
        for window in self._windows.values():
            success = window.update(elapsed_time) and success
        return success

    def draw(self) -> None:
        for window in self._windows.values():
            window.draw()

    def set_manager(self, manager: SceneManager) -> None:
        self._manager = manager

    def get_manager(self) -> SceneManager:
        if self._manager is None:
            msg = "Manager is not initialized yet!"
            raise ValueError(msg)
        return self._manager


class SceneManager(Generic[S, V]):
    """A class that manages different scenes."""

    def __init__(self) -> None:
        self._scenes: dict[S, Scene[V]] = {}
        self._scene: Scene[V] | None = None
        self._stack: list[S] = []
        self._stack_changed: bool = False
        self._data_for_scene: dict[str, Any] = {}
        self._data_from_scene: dict[str, Any] = {}

    def add_scene(self, scene: Scene[V], key: S) -> None:
        scene.set_manager(self)
        self._scenes[key] = scene

    def push_scene(self, key: S, data_for_scene: dict[str, Any] | None = None) -> None:
        self._stack.append(key)
        self._stack_changed = True
        self._data_for_scene = {} if data_for_scene is None else data_for_scene

    def pop_scene(self, empty_ok: bool = False) -> S | None:
        self._stack_changed = True
        if self._stack:
            return self._stack.pop()
        elif empty_ok:
            return None
        else:
            msg = "Stack is empty. Set `empty_ok` to True if you don't mind."
            raise IndexError(msg)

    def get_scene(self) -> Scene[V]:
        if self._scene is None:
            msg = "No scene initialized yet."
            raise ValueError(msg)

        return self._scene

    def handle_input(
        self, events: list[pygame.event.Event] | None = None
    ) -> list[pygame.event.Event]:
        if events is None:
            events = [e for e in pygame.event.get()]

        if self._scene is not None:
            return self._scene.handle_input(events)

        return events

    def update(self, elapsed_time: float) -> bool:
        if not self._stack:
            # There is nothing to update
            return True

        old_scene = self._scene
        self._scene = self._scenes[self._stack[-1]]

        if self._scene != old_scene or self._stack_changed:
            self._stack_changed = False
            if old_scene is not None:
                self._data_from_scene = old_scene._exit_focus()

            self._scene._enter_focus(self._data_for_scene)

        if self._scene is not None:
            return self._scene._update(elapsed_time)

        return True

    def get_data_from_previous_scene(self) -> dict[str, Any]:
        return self._data_from_scene

    def draw(self) -> None:
        if self._scene is None:
            return

        self._scene.draw()


def position_to_screen_rect(
    position: Position, screen_pos: pygame.Vector2, screen_size: pygame.Vector2
) -> tuple[pygame.Vector2, pygame.Vector2]:
    v_pos = screen_pos
    v_size = screen_size
    if position in (Position.TOP, Position.TOP_LEFT, Position.TOP_RIGHT):
        v_size.y /= 2

    if position in (Position.BOTTOM, Position.BOTTOM_LEFT, Position.BOTTOM_RIGHT):
        v_size.y /= 2
        v_pos.y = v_size.y

    if position in (Position.LEFT, Position.TOP_LEFT, Position.BOTTOM_LEFT):
        v_size.x /= 2

    if position in (Position.RIGHT, Position.TOP_RIGHT, Position.BOTTOM_RIGHT):
        v_size.x /= 2
        v_pos.x = v_size.x

    return v_pos, v_size
