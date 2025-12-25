from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from ..util.constants import (
    MAP_TRANSITION_DURATION_FACTOR,
    MOVE_MAP_DURATION,
    UI_HIGHT,
)
from .tilemap import Tilemap

if TYPE_CHECKING:
    from .tile import Tile


class TransitionMap(Tilemap):
    def __init__(
        self, src_map: Tilemap, dst_map: Tilemap, dst_vx: int, dst_vy: int
    ):
        super().__init__(src_map.name)

        self.src_map: Tilemap = src_map
        self.dst_map: Tilemap = dst_map
        self.vx: int = int(dst_vx)
        self.vy: int = int(dst_vy)
        self.progress: float = 0.0
        self.duration: float = (
            MOVE_MAP_DURATION * MAP_TRANSITION_DURATION_FACTOR
        )
        self.time_so_far: float = 0.0
        self.step_size: float = 1.0
        self._extra_oy = UI_HIGHT

        self.width: int = self.src_map.width
        self.height: int = self.src_map.height
        self.tiles_nx = (
            self.engine.backend.render_width / self.engine.rtc.tile_width
        )
        self.tiles_ny = (
            self.engine.backend.render_height / self.engine.rtc.tile_height
        )

        if self.vx != 0:
            self.step_size = self.duration / (self.tiles_nx * 0.75)
        elif self.vy != 0:
            self.step_size = self.duration / ((self.tiles_ny - 1) * 0.75)

    def update(self, elapsed_time: float) -> bool:
        self.progress = self.time_so_far / self.step_size
        self.time_so_far += elapsed_time

        return self.src_map.update(elapsed_time)

    def draw_self(
        self,
        ox: float,
        oy: float,
        visible_tiles_sx: int,
        visible_tiles_sy: int,
        visible_tiles_ex: int,
        visible_tiles_ey: int,
        layer_pos: int = 0,
    ) -> bool:
        src_tiles_sx = dst_tiles_sx = int(visible_tiles_sx)
        src_tiles_sy = dst_tiles_sy = int(visible_tiles_sy)
        src_tiles_ex = dst_tiles_ex = int(visible_tiles_ex)
        src_tiles_ey = dst_tiles_ey = int(visible_tiles_ey)
        src_ox = dst_ox = ox
        src_oy = dst_oy = oy

        if self.vx < 0:  # Transition west
            src_tiles_sx += int(self.progress)
            src_tiles_ex += int(self.progress)
            dst_tiles_ex = src_tiles_sx + 1
            src_ox = max(-self.tiles_nx, -self.progress)
            dst_ox = (
                self.dst_map.width - self.tiles_nx + visible_tiles_ex + src_ox
            )

        elif self.vx > 0:  # Transition east
            src_tiles_sx -= int(self.progress)
            src_tiles_ex -= int(self.progress)
            dst_tiles_sx = src_tiles_ex
            src_ox = self.src_map.width + min(0, self.progress - self.tiles_nx)
            dst_ox = src_ox - self.src_map.width

        elif self.vy < 0:  # Transition north
            src_tiles_sy += int(self.progress)
            src_tiles_ey += int(self.progress)
            dst_tiles_ey = src_tiles_sy + 1
            src_oy = max(-self.tiles_ny, -self.progress - self._extra_oy)
            dst_oy = (
                self.dst_map.height - self.tiles_ny + visible_tiles_ey + src_oy
            )

        elif self.vy > 0:  # Transition south
            src_tiles_sy -= int(self.progress)
            src_tiles_ey -= int(self.progress)
            dst_tiles_sy = src_tiles_ey
            src_oy = self.src_map.height + min(
                0, self.progress - self.tiles_ny
            )
            dst_oy = -visible_tiles_ey + self.progress

        # if layer_pos == 0:
        #     print(
        #         f"o({ox:.2f}),t({self.tiles_nx}),"
        #         f"ss({self.src_map.width}),so({src_ox:.2f}),"
        #         f"ts({src_tiles_sx}),te({src_tiles_ex}) -> "
        #         f"ds({self.dst_map.width}),do({dst_ox:.2f}),"
        #         f"ts({dst_tiles_sx}),te({dst_tiles_ex})"
        #     )
        # print(
        #     f"o({ox:.2f},{oy:.2f}),"
        #     f"ss({self.src_map.width},{self.src_map.height}),so({src_ox:.2f},{src_oy:.2f}),"
        #     f"ts({src_tiles_sx},{src_tiles_sy}),te{src_tiles_ex,src_tiles_ey} -> "
        #     f"ds({self.dst_map.width},{self.dst_map.height}),do({dst_ox:.2f},{dst_oy:.2f}),"
        #     f"ts({dst_tiles_sx},{dst_tiles_sy}),te({dst_tiles_ex},{dst_tiles_ey})"
        # )
        # print(src_oy, dst_oy, self.map_screen_oy)
        self.src_map.draw_self(
            src_ox,
            src_oy,
            src_tiles_sx,
            src_tiles_sy,
            src_tiles_ex,
            src_tiles_ey,
            layer_pos,
        )
        self.dst_map.draw_self(
            dst_ox,
            dst_oy,
            dst_tiles_sx,
            dst_tiles_sy,
            dst_tiles_ex,
            dst_tiles_ey,
            layer_pos,
        )

        return True

    def is_solid(self, px: int, py: int) -> bool:
        return False

    def get_tile(self, px: int, py: int) -> Optional[Tile]:
        return None
