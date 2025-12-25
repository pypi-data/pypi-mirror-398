from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List, Optional

from ..types.position import Position
from ..types.window import Window
from ..util.colors import BLACK, WHITE
from ..util.constants import (
    DIALOG_CHARS_PER_LINE,
    DIALOG_HEIGHT,
    DIALOG_N_LINES,
    DIALOG_WIDTH,
)
from .camera import Camera
from .mima_view import MimaView
from .mima_window import MimaWindow

if TYPE_CHECKING:
    from ..objects.dynamic import Dynamic
    from ..types.player import Player


class MimaScene(MimaView):
    def __init__(
        self,
        player: Player,
        position: Position,
        camera_name: Optional[str] = None,
    ) -> None:
        self.window_stack: List[Window] = []
        self.windows: Dict[Window, MimaWindow] = {}
        self._current_window: Optional[MimaWindow] = None
        self.stack_changed = False
        self.skip_draw_ui = False

        self.player: Player = player
        self._position: Position = position

        self._camera_name: str = (
            camera_name if camera_name is not None else f"C_{player.name}"
        )
        self._controls_camera_name: str = f"{self._camera_name}_CONTROLS"

        self.camera: Camera
        self.controls_camera: Camera
        self._dialog_px: float
        self._dialog_py: float
        self._dialog_width: float = DIALOG_WIDTH
        self._dialog_height: float = DIALOG_HEIGHT
        self._dialog_spacing: float = 3 / self.engine.rtc.tile_height

        self._dialog_text_color = BLACK
        self._dialog_bg_color = WHITE

        self.update_scene_position(self._position)

    def update_scene_position(self, position: Position) -> None:
        width = self.engine.backend.render_width / self.engine.rtc.tile_width
        height = (
            self.engine.backend.render_height / self.engine.rtc.tile_height
        )
        # print(f"Starting camera setup: {width}, {height}, {position}")
        if position in (
            Position.LEFT,
            Position.RIGHT,
            Position.TOP_LEFT,
            Position.TOP_RIGHT,
            Position.BOTTOM_LEFT,
            Position.BOTTOM_RIGHT,
        ):
            width /= 2
            self._dialog_px = 1
        else:
            self._dialog_px = width / 2 - self._dialog_width / 2

        if position in (
            Position.TOP,
            Position.BOTTOM,
            Position.TOP_LEFT,
            Position.TOP_RIGHT,
            Position.BOTTOM_LEFT,
            Position.BOTTOM_RIGHT,
        ):
            height /= 2
            self._dialog_py = height - 4
        else:
            self._dialog_py = height - 4

        self.camera = Camera(self._camera_name, width, height)
        # self.controls_camera = Camera(
        #     self._controls_camera_name, width, height
        # )
        if position == Position.CENTER:
            # print(f"Camera setup finished: {width}, {height}")
            return

        if position in (
            Position.RIGHT,
            Position.BOTTOM_RIGHT,
            Position.TOP_RIGHT,
        ):
            self.camera.px = self.engine.backend.render_width / 2
            self.camera.border_left = True

        if position in (
            Position.BOTTOM,
            Position.BOTTOM_LEFT,
            Position.BOTTOM_RIGHT,
        ):
            self.camera.py = self.engine.backend.render_height / 2
            self.camera.border_top = True

        if position in (
            Position.LEFT,
            Position.TOP_LEFT,
            Position.BOTTOM_LEFT,
        ):
            self.camera.border_right = True
            self.camera.border_color = BLACK

        if position in (Position.TOP, Position.TOP_LEFT, Position.TOP_RIGHT):
            self.camera.border_bottom = True
            self.camera.border_color = BLACK

    def update(
        self,
        elapsed_time: float,
        *,
        target: Optional[Dynamic] = None,
        map_width: int = 0,
        map_height: int = 0,
    ) -> bool:
        self.update_window()

        self.camera.update(target, map_width, map_height)
        self.update_dialog_position()

        # print(type(self._current_window))
        return self._current_window.update(elapsed_time, self.camera)

    def clear_stack(self, windows: Optional[List[Window]] = None):
        self.stack_changed = True
        if windows is not None:
            self.window_stack = windows
        else:
            self.window_stack = []

    def add_window(self, window: Window):
        self.window_stack.append(window)
        self.stack_changed = True

    def pop_window(self):
        self.stack_changed = True
        return self.window_stack.pop()

    def get_window(self) -> MimaWindow:
        return self._current_window

    def get_next_window_type(self) -> Window:
        return self.window_stack[-1]

    def get_previous_window_type(self) -> Window:
        return self.window_stack[-2]

    def handle_user_input(self):
        if self._current_window is None:
            self.update_window()
        self._current_window.handle_user_input(self.player)

    def draw_map_and_objects(
        self, player, camera, tmap, dynamics, projectiles, effects
    ) -> None:
        self._current_window.draw_map_layers(tmap, [-1, 0])
        self._current_window.draw_objects_y_sorted(
            dynamics + projectiles, [-1, 0, 1, 2]
        )

        self._current_window.draw_effect_layers(effects, [0])

        self._current_window.draw_map_layers(tmap, [1, 2])

        self._current_window.draw_effect_layers(effects, [1, 2, 3, 4])

    def draw_ui(self):
        if self.skip_draw_ui:
            self.skip_draw_ui = False
            return
        self._current_window.draw_ui()
        self._current_window.draw_controls()

    def draw_camera_border(self):
        self.camera.draw_borders()

    def load_window(self):
        self._current_window.load(
            self.engine.get_view().maps[self.player].name
        )

    def update_window(self):
        old_window = self._current_window
        self._current_window = self.windows[self.window_stack[-1]]
        self._current_window.set_camera(self.camera)
        self._current_window.set_player(self.player)

        if self._current_window != old_window or self.stack_changed:
            self.stack_changed = False
            if old_window is not None:
                old_window.on_exit_focus()

            self._current_window.on_enter_focus()
            self.skip_draw_ui = True

    def update_dialog_position(self):
        self._dialog_px = (
            self.camera.visible_tiles_ex - self._dialog_width
        ) / 2
        self._dialog_py = (
            self.camera.visible_tiles_ey - self._dialog_height - 1
        )

    def display_dialog(self, lines):
        self._current_window.display_dialog(
            lines,
            int(self._dialog_px * self.engine.rtc.tile_width),
            int(self._dialog_py * self.engine.rtc.tile_height),
            int(self._dialog_width * self.engine.rtc.tile_width),
            int(self._dialog_height * self.engine.rtc.tile_height),
            int(self._dialog_spacing * self.engine.rtc.tile_height),
            self._dialog_text_color,
            self._dialog_bg_color,
        )
