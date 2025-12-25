from __future__ import annotations

from typing import TYPE_CHECKING, List

from ...types.alignment import Alignment
from ...util.colors import DARK_RED, TRANS_LIGHT_RED
from ...util.constants import SMALL_FONT_HEIGHT, SMALL_FONT_WIDTH
from ..projectile import Projectile

if TYPE_CHECKING:
    from ...util.colors import Color
    from ..dynamic import Dynamic


class DynamicDebugBox(Projectile):
    def __init__(
        self,
        follow: Dynamic,
        color: Color = TRANS_LIGHT_RED,
        n_frames=1,
        ids=None,
    ) -> None:
        super().__init__(
            0,
            0,
            "DynamicDebugBox",
            duration=0.0,
            alignment=Alignment.NEUTRAL,
            tilemap=follow.tilemap,
        )
        self.layer = 2
        self.sprite = None

        self._follow: Dynamic = follow
        self._color: Color = color
        self._n_frames: int = n_frames
        self._ids: List[int] = ids if ids is not None else follow.chunks

    def update(self, elapsed_time: float, target: Dynamic = None):
        if self._n_frames >= 0:
            if self._n_frames == 0:
                self.kill()

            self._n_frames -= 1

    def draw_self(self, ox, oy, camera_name):
        ppx = (
            self._follow.px - ox + self._follow.hitbox_px
        ) * self.engine.rtc.tile_width
        ppy = (
            self._follow.py - oy + self._follow.hitbox_py
        ) * self.engine.rtc.tile_height
        pwidth = self._follow.hitbox_width * self.engine.rtc.tile_width
        pheight = self._follow.hitbox_height * self.engine.rtc.tile_height
        self.engine.backend.fill_rect(
            ppx, ppy, pwidth, pheight, self._color, camera_name
        )
        txt = ""
        for i in self._ids:
            txt += f"{i} "

        if txt:
            txt = txt.strip()
            text_pw = len(txt) * SMALL_FONT_WIDTH + 1
            text_ph = SMALL_FONT_HEIGHT + 1
            text_ppx = ppx + pwidth / 2 - text_pw / 2
            text_ppy = ppy + pheight / 2 - text_ph / 2
            self.engine.backend.fill_rect(
                text_ppx - 1,
                text_ppy - 1,
                text_pw + 1,
                text_ph + 1,
                DARK_RED,
                camera_name,
            )
            self.engine.backend.draw_small_text(
                txt, text_ppx, text_ppy, camera_name=camera_name
            )


class StaticDebugBox(Projectile):
    def __init__(self, px, py, width, height, color, n_frames=1, ids=None):
        super().__init__(
            px,
            py,
            "StaticDebugBox",
            duration=0.0,
            alignment=Alignment.NEUTRAL,
        )
        self.layer = 2
        self._color = color
        self._n_frames = n_frames
        self._px = px
        self._py = py
        self._width = width
        self._height = height
        self._ids: List[int] = ids if ids is not None else []

    def update(self, elapsed_time: float, target: Dynamic = None):
        if self._n_frames <= 0:
            self.kill()

        self._n_frames -= 1

    def draw_self(self, ox, oy, camera_name):
        ppx = (self._px - ox) * self.engine.rtc.tile_width
        ppy = (self._py - oy) * self.engine.rtc.tile_height
        pwidth = self._width * self.engine.rtc.tile_width
        pheight = self._height * self.engine.rtc.tile_height
        self.engine.backend.fill_rect(
            ppx, ppy, pwidth, pheight, self._color, camera_name
        )
        txt = ""
        for i in self._ids:
            txt += f"{i} "

        if txt:
            txt = txt.strip()
            text_pw = len(txt) * self.engine.rtc.small_font_width + 1
            text_ph = self.engine.rtc.small_font_height + 1
            text_ppx = ppx + pwidth / 2 - text_pw / 2
            text_ppy = ppy + pheight / 2 - text_ph / 2
            self.engine.backend.fill_rect(
                text_ppx - 1,
                text_ppy - 1,
                text_pw + 1,
                text_ph + 1,
                self.engine.rtc.color_dark_red,
                camera_name,
            )
            self.engine.backend.draw_small_text(
                txt, text_ppx, text_ppy, camera_name=camera_name
            )
