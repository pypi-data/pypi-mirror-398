from typing import List

from ...types.alignment import Alignment
from ...types.blend import Blend
from ..dynamic import Dynamic
from ..projectile import Projectile


class Light(Projectile):
    def __init__(
        self,
        follow: Dynamic,
        max_size: int = 64,
        fixed_size: bool = False,
        update_from_target: bool = False,
    ):
        super().__init__(
            0,
            0,
            name="Light",
            tilemap=follow.tilemap,
            duration=0,
            alignment=Alignment.GOOD,
        )
        self.layer = 1
        self.sprite.name = "light_small"
        self.sprite.width = 48
        self.sprite.height = 48
        self.solid_vs_map = False
        # self.moves_on_collision = False
        self._follow: Dynamic = follow
        self._fixed_size: bool = fixed_size
        self._update_from_target: bool = update_from_target

        self._timer: float = 0.2
        self._timer_reset: float = 0.2
        self._size_idx: int = 0

        self._sizes: List[int]
        self._max_size: int

        self._prepare_light(max_size)

    def update(self, elapsed_time: float, target: Dynamic = None):
        self.px = (
            self._follow.px
            + self._follow.sprite.width / self.engine.rtc.tile_width * 0.5
        )
        self.py = (
            self._follow.py
            + self._follow.sprite.height / self.engine.rtc.tile_height * 0.5
        )

        rad = self._follow.light_radius()
        if self._max_size != rad:
            self._prepare_light(rad)

        if self._follow.redundant:
            self.kill()

        if self._fixed_size:
            return

        self._timer -= elapsed_time
        if self._timer <= 0.0:
            self._timer += self._timer_reset
            self._size_idx = (self._size_idx + 1) % len(self._sizes)

    def draw_self(self, ox: float, oy: float, camera_name: str):
        self.engine.backend.fill_circle(
            (self.px - ox + self._follow.extra_ox)
            * self.engine.rtc.tile_width,
            (self.py - oy + self._follow.extra_oy)
            * self.engine.rtc.tile_height,
            self._sizes[self._size_idx] * 0.65,  # 0.3125 *
            self.engine.rtc.color_dark_grey,
            camera_name,
            blend_mode=Blend.SUB,
            draw_to_filter=True,
        )
        self.engine.backend.fill_circle(
            (self.px - ox + self._follow.extra_ox)
            * self.engine.rtc.tile_width,
            (self.py - oy + self._follow.extra_oy)
            * self.engine.rtc.tile_height,
            self._sizes[self._size_idx] * 0.5,  # 0.3125 *
            self.engine.rtc.color_very_light_grey,
            camera_name,
            blend_mode=Blend.SUB,
            draw_to_filter=True,
        )

    def _prepare_light(self, max_size):
        self._max_size = max_size
        self._sizes = [max_size]
        if not self._fixed_size:
            self._sizes.extend(
                [
                    int(max_size * 0.97),
                    int(max_size * 0.94),
                    int(max_size * 0.97),
                ]
            )
