from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Optional

from ..types.direction import Direction
from ..types.keys import Key as K
from ..types.player import Player
from ..types.window import Window
from ..util.colors import TRANS_CYAN, TRANS_LIGHT_RED
from ..util.constants import BIG_FONT_HEIGHT, BIG_FONT_WIDTH
from ..util.functions import wrap_text
from .mima_view import MimaView

if TYPE_CHECKING:
    from ..maps.tilemap import Tilemap
    from ..objects.dynamic import Dynamic
    from ..util.colors import Color
    from .camera import Camera
    from .mima_mode import MimaMode
    from .mima_scene import MimaScene


class MimaWindow(MimaView):
    def __init__(
        self,
        mode: MimaMode,
        scene: MimaScene,
        wtype: Window = Window.PLACEHOLDER,
    ) -> None:
        self.mode = mode
        self.scene = scene
        self.wtype = wtype

        self.p_obj: Optional[Dynamic] = None
        self.camera: Optional[Camera] = None
        self.dialog_to_show: List[str] = []
        self.additional_data: Optional[Any] = None

    def on_enter_focus(self):
        pass

    def on_exit_focus(self):
        pass

    def update(self, elapsed_time: float, camera: Camera) -> bool:
        return True

    def handle_user_input(self, player: Player) -> None:
        self.p_obj.vx = self.p_obj.vy = 0

        if self.engine.keys.key_held(K.UP, player):
            self.p_obj.vy = -1
            self.p_obj.facing_direction = Direction.NORTH
        if self.engine.keys.key_held(K.DOWN, player):
            self.p_obj.vy = 1
            self.p_obj.facing_direction = Direction.SOUTH
        if self.engine.keys.key_held(K.LEFT, player):
            self.p_obj.vx = -1
            self.p_obj.facing_direction = Direction.WEST
        if self.engine.keys.key_held(K.RIGHT, player):
            self.p_obj.vx = 1
            self.p_obj.facing_direction = Direction.EAST

    def draw_map_layers(self, tilemap: Tilemap, layers: List[int]) -> None:
        for pos in layers:
            tilemap.draw_self(
                self.camera.ox,
                self.camera.oy,
                self.camera.visible_tiles_sx,
                self.camera.visible_tiles_sy,
                self.camera.visible_tiles_ex,
                self.camera.visible_tiles_ey,
                pos,
                self.camera.name,
            )

    def draw_objects_y_sorted(
        self, objects: List[Dynamic], layers: Optional[List[int]] = None
    ) -> None:
        layers = layers if layers is not None else list(range(-3, 3))

        y_sorted = sorted(objects, key=lambda obj: obj.py)
        for layer in layers:
            for obj in y_sorted:
                if self._check_draw_object(obj, layer):
                    # print(
                    #     obj.px,
                    #     obj.py,
                    #     obj.name,
                    #     self._camera.name,
                    #     self._camera.ox,
                    #     self._camera.oy,
                    # )
                    obj.draw_self(
                        self.camera.ox, self.camera.oy, self.camera.name
                    )
                    if self.engine.draw_dyn_ids:
                        self.engine.backend.draw_small_text(
                            f"{obj.dyn_id}",
                            (obj.px - self.camera.ox)
                            * self.engine.rtc.tile_width,
                            (obj.py - self.camera.oy) * obj.sprite.height
                            + obj.sprite.height,
                            self.engine.rtc.color_red,
                            self.camera.name,
                        )

    def draw_effect_layers(
        self, effects: List[Dynamic], layers: List[int]
    ) -> None:
        for layer in layers:
            for effect in effects:
                if effect.layer == layer:
                    effect.draw_self(
                        self.camera.ox, self.camera.oy, self.camera.name
                    )

    def _check_draw_object(self, obj, layer) -> bool:
        if obj.redundant or not obj.visible or obj.layer != layer:
            return False

        return self.check_draw_object(obj, layer)

    def check_draw_object(self, obj, layer) -> bool:
        """Custom check if object should be drawn."""
        return True

    def draw_ui(self) -> None:
        pass

    def draw_controls(self) -> None:
        if not self.engine.show_touch_controls:
            return

        state = self.engine.keys.get_touch_state()
        if not state:
            return

        data_move = state[K.UP]
        if data_move["active"]:
            radius = self.engine.rtc.tile_width
            self.engine.backend.draw_circle(
                int(data_move["rsx"] * self.camera.pwidth),
                int(data_move["rsy"] * self.camera.pheight),
                radius,
                TRANS_LIGHT_RED,
                self.camera.name,
                draw_to_ui=True,
            )
            self.engine.backend.fill_circle(
                int(data_move["rpx"] * self.camera.pwidth),
                int(data_move["rpy"] * self.camera.pheight),
                radius,
                TRANS_LIGHT_RED,
                self.camera.name,
                draw_to_ui=True,
            )

        for idx in range(4, 12):
            key = K(idx)
            data = state.get(key, {})
            if not data:
                continue
            # print(data_a)

            ppx = int(data["rpx"] * self.camera.pwidth)
            ppy = int(data["rpy"] * self.camera.pheight)
            pwidth = int(data["rwidth"] * self.camera.pwidth)
            pheight = int(data["rheight"] * self.camera.pheight)
            if data["active"]:
                self.engine.backend.fill_rect(
                    ppx,
                    ppy,
                    pwidth,
                    pheight,
                    TRANS_LIGHT_RED,
                    self.camera.name,
                    draw_to_ui=True,
                )
            else:
                self.engine.backend.draw_rect(
                    ppx,
                    ppy,
                    pwidth,
                    pheight,
                    TRANS_LIGHT_RED,
                    self.camera.name,
                    draw_to_ui=True,
                )
                text = key.name
                text_width = len(text) * BIG_FONT_WIDTH
                self.engine.backend.draw_big_text(
                    text,
                    int(ppx + pwidth / 2 - text_width / 2),
                    int(ppy + pheight / 2 - BIG_FONT_HEIGHT / 2),
                    TRANS_LIGHT_RED,
                    self.camera.name,
                    draw_to_ui=True,
                )

        # self.engine.backend.fill_circle(
        #     int(data_a["px"] * self.camera.pwidth),
        #     int(data_a["py"] * self.camera.pheight),
        #     int(data_a["width"] * self.camera.pwidth / 2),
        #     color,
        #     self.camera.name,
        #     draw_to_ui=True,
        # )

    def set_camera(self, camera: Camera):
        self.camera = camera

    def set_player(self, player: Player):
        self.p_obj = self.engine.get_player(player)

    def display_dialog(
        self,
        lines: List[str],
        ppx: int,
        ppy: int,
        pwidth: int,
        pheight: int,
        pspacing: int,
        text_color: Color,
        bg_color: Color,
    ):
        self.engine.backend.fill_rect(
            ppx, ppy, pwidth, pheight, bg_color, self.camera.name
        )
        self.engine.backend.draw_rect(
            ppx, ppy, pwidth, pheight, text_color, self.camera.name
        )
        # print(ppx, ppy, pwidth, pheight, lines)
        for idx, line in enumerate(lines):
            self.engine.backend.draw_big_text(
                line,
                ppx + 4,
                ppy
                + 4
                + idx * pspacing
                + idx * self.engine.rtc.big_font_height,
                text_color,
                self.camera.name,
            )
