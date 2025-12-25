from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from ..backend.pygame_camera import PygameCamera
from ..util.colors import Color

if TYPE_CHECKING:
    from ..engine import MimaEngine
    from ..maps.tilemap import Tilemap
    from ..objects.dynamic import Dynamic


class Camera:
    engine: MimaEngine

    def __init__(
        self,
        name: str,
        width: float,
        height: float,
        visible_tiles_sx: int = 0,
        visible_tiles_sy: int = 0,
        visible_tiles_ex: Optional[int] = None,
        visible_tiles_ey: Optional[int] = None,
    ):
        self.pwidth = int(width * self.engine.rtc.tile_width)
        self.pheight = int(height * self.engine.rtc.tile_height)
        self._ui_pwidth = self.pwidth
        self._ui_pheight = self.pheight
        self.ui_pwidth = self.pwidth
        self.ui_pheight = self.pheight

        self.engine.backend.new_camera(name, self.pwidth, self.pheight)

        self.name = name

        if visible_tiles_ex is None:
            visible_tiles_ex = width
        if visible_tiles_ey is None:
            visible_tiles_ey = height

        self._visible_tiles_sx: int = int(visible_tiles_sx)
        self._visible_tiles_sy: int = int(visible_tiles_sy)
        self._visible_tiles_ex: int = int(visible_tiles_ex)
        self._visible_tiles_ey: int = int(visible_tiles_ey)
        self.visible_tiles_sx: float = visible_tiles_sx
        self.visible_tiles_sy: float = visible_tiles_sy
        self.visible_tiles_ex: float = visible_tiles_ex
        self.visible_tiles_ey: float = visible_tiles_ey

        self._zoom: float = 1.0
        self._zoom_changed: bool = False
        self.camera_scale: float = 1.0
        self._ui_zoom: float = 1.0
        self._ui_zoom_changed: bool = False

        if self.visible_tiles_ex is None:
            self.visible_tiles_ex = (
                self.engine.backend.render_width / self.engine.rtc.tile_width
                - self.visible_tiles_sx
            )

        if self.visible_tiles_ey is None:
            self.visible_tiles_ey = (
                self.engine.backend.render_height / self.engine.rtc.tile_height
                - self.visible_tiles_sy
            )
        self.border_left: bool = False
        self.border_right: bool = False
        self.border_top: bool = False
        self.border_bottom: bool = False
        self.border_width: int = 1
        self.border_color: Color = self.engine.rtc.color_white

    def update(
        self,
        target: Optional[Dynamic] = None,
        map_width: int = 0,
        map_height: int = 0,
    ):
        self.visible_tiles_sx = self._visible_tiles_sx * 1 / self.zoom
        self.visible_tiles_sy = self._visible_tiles_sy * 1 / self.zoom
        self.visible_tiles_ex = self._visible_tiles_ex * 1 / self.zoom
        self.visible_tiles_ey = self._visible_tiles_ey * 1 / self.zoom
        self.camera_scale = self.engine.backend.render_width / (
            self.visible_tiles_ex * self.engine.rtc.tile_width
        )

        if target is not None:
            # Calculate x offset
            self.ox = target.px - self.visible_tiles_ex / 2.0

            # Calculate y offset
            self.oy = target.py - self.visible_tiles_ey / 2.0

        if map_width > 0:
            # Adjust x offset to map
            self.ox = min(map_width - self.visible_tiles_ex, max(0, self.ox))
            if map_width < self.visible_tiles_ex:
                self.ox += (self.visible_tiles_ex - map_width) / 2.0
        if map_height > 0:
            # Adjust y offset to map
            self.oy = min(map_height - self.visible_tiles_ey, max(0, self.oy))
            if map_height < self.visible_tiles_ey:
                self.oy += (self.visible_tiles_ey - map_height) / 2.0

        self.ox -= self.visible_tiles_sx
        self.oy -= self.visible_tiles_sy

        if self._zoom_changed:
            self.engine.backend.get_camera(self.name).change_zoom(
                int(self.visible_tiles_ex * self.engine.rtc.tile_width),
                int(self.visible_tiles_ey * self.engine.rtc.tile_height),
            )
            self.engine.backend.get_camera(
                self.name
            ).camera_scale = self.camera_scale

            self._zoom_changed = False
        if self._ui_zoom_changed:
            # print(
            #     int(self.ui_pwidth * self._ui_zoom),
            #     int(self.ui_pheight * self._ui_zoom),
            # )
            self.ui_pwidth = int(self._ui_pwidth * 1 / self._ui_zoom)
            self.ui_pheight = int(self._ui_pheight * 1 / self._ui_zoom)

            self.engine.backend.get_camera(self.name).change_ui_zoom(
                self.ui_pwidth, self.ui_pheight
            )
            self._ui_zoom_changed = False

    def draw(self, *sprites):
        for sprite in sprites:
            sprite.draw_self(self.ox, self.oy)

    def draw_borders(self):
        if self.border_left:
            self.engine.backend.draw_line(
                0,
                0,
                0,
                self.pheight - 1,
                self.border_color,
                camera_name=self.name,
                width=self.border_width,
            )
        if self.border_right:
            self.engine.backend.draw_line(
                self.pwidth - 1,
                0,
                self.pwidth - 1,
                self.pheight - 1,
                self.border_color,
                camera_name=self.name,
                width=self.border_width,
            )

    @property
    def zoom(self):
        return self._zoom

    @zoom.setter
    def zoom(self, val):
        self._zoom = val
        self._zoom_changed = True

    @property
    def ui_zoom(self):
        return self._ui_zoom

    @ui_zoom.setter
    def ui_zoom(self, val):
        self._ui_zoom = val
        self._ui_zoom_changed = True

    @property
    def px(self):
        return self.engine.backend.get_camera(self.name).px

    @property
    def py(self):
        return self.engine.backend.get_camera(self.name).py

    @px.setter
    def px(self, val):
        self.engine.backend.get_camera(self.name).px = val

    @py.setter
    def py(self, val):
        self.engine.backend.get_camera(self.name).py = val
