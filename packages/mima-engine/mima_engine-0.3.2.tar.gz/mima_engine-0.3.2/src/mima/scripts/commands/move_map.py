from typing import List, Optional

from ...maps.transition_map import TransitionMap
from ...objects.dynamic import Dynamic
from ...types.player import Player
from ...util.constants import HEIGHT, MOVE_MAP_DURATION, WIDTH
from ..command import Command


class CommandMoveMap(Command):
    def __init__(
        self,
        *,
        new_map_name: str,
        obj: Dynamic,
        target_px: float,
        target_py: float,
        vx: float,
        vy: float,
        players: Optional[List[Player]] = None,
    ):
        super().__init__()

        self.players = [obj.is_player()]
        self.src_map = self.engine.scene.tilemap
        self.dst_map = self.engine.assets.get_map(new_map_name)
        self.obj: Dynamic = obj
        self.vx: float = vx
        self.vy: float = vy
        self.start_px: float = 0
        self.start_py: float = 0
        self.start_ox: float = 0
        self.start_oy: float = 0
        self.target_px: float = target_px
        self.target_py: float = target_py
        self.target_ox: float = 0
        self.target_oy: float = 0
        self.final_px: float = target_px
        self.final_py: float = target_py

        if self.vx == 0 and self.vy == 0:
            # Error
            self.completed = True
            self.started = True

        self.duration: float = MOVE_MAP_DURATION
        self.time_so_far: float = 0.0

    def start(self) -> None:
        # Prevent circular import
        # from ...maps.transition_map import TransitionMap

        self.start_ox = self._get_offset_x(self.obj.px)
        self.start_oy = self._get_offset_y(self.obj.py)
        self.target_ox = self._get_offset_x(self.target_px)
        self.target_oy = self._get_offset_y(self.target_py)
        self.start_px = self.obj.px
        self.start_py = self.obj.py

        # print(
        #     f"start_pos=({self.start_px:.1f}, {self.start_py:.1f}), "
        #     f"tar_pos=({self.target_px:.1f}, {self.target_py:.1f}), "
        #     f"start_off=({self.start_ox:.1f}, {self.start_oy:.1f}), "
        #     f"tar_off=({self.target_ox:.1f}, {self.target_oy:.1f})"
        # )

        if self.vx != 0:
            if self.vx < 0:
                self.target_px -= self.target_ox
            else:
                self.target_px += self.start_ox
            self.target_py = self.start_py

        elif self.vy != 0:
            self.target_px = self.start_px
            if self.vy < 0:
                self.target_py -= self.target_oy + 1
            else:
                self.target_py += self.start_oy + 1

        self.obj.solid_vs_dyn = False
        self.obj.solid_vs_map = False
        self.obj.vx = self.obj.vy = 0
        self.engine.teleport_triggered = True
        self.engine.scene.tilemap = TransitionMap(
            self.src_map, self.dst_map, self.vx, self.vy
        )
        self.engine.scene.delete_map_dynamics()

    def update(self, elapsed_time):
        self.time_so_far += elapsed_time
        rela_time = self.time_so_far / self.duration
        if rela_time > 1.0:
            rela_time = 1.0

        self.obj.px = (
            self.target_px - self.start_px
        ) * rela_time + self.start_px
        self.obj.py = (
            self.target_py - self.start_py
        ) * rela_time + self.start_py

        ox = self._get_offset_x(self.obj.px)
        oy = self._get_offset_y(self.obj.py)
        self.obj.extra_ox = ox - self.start_ox
        self.obj.extra_oy = oy - self.start_oy

        if self.time_so_far >= self.duration:
            self.completed = True
        else:
            self.engine.teleport_triggered = True

        # print(f"obj_pos=({self.obj.px:.1f}, {self.obj.py:.1f})")

    def finalize(self):
        if self.vy != 0:
            self.obj.px = self.target_px
            if self.vy > 0:
                self.obj.py = self.target_py - self.start_oy - 1
            else:
                self.obj.py = self.target_py + self.target_oy + 1

        self.obj.vx = self.obj.vy = 0
        self.obj.solid_vs_dyn = True
        self.obj.solid_vs_map = True
        self.obj.extra_ox = self.obj.extra_oy = 0
        self.engine.scene.change_map(
            self.dst_map.name, self.final_px, self.final_py
        )

    def _get_offset_x(self, px: float) -> float:
        visible_tiles = WIDTH / self.engine.rtc.tile_width
        offset = px - visible_tiles / 2.0

        if offset < 0:
            offset = 0
        if offset > self.src_map.width - visible_tiles:
            offset = self.src_map.width - visible_tiles

        return offset

    def _get_offset_y(self, py: float) -> float:
        visible_tiles = HEIGHT / self.engine.rtc.tile_width - 1
        offset = py - visible_tiles / 2.0

        if offset < 0:
            offset = 0
        if offset > self.src_map.height - visible_tiles:
            offset = self.src_map.height - visible_tiles

        offset -= 1
        return offset
