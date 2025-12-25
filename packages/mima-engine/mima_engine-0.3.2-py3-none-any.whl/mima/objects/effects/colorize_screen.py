from typing import List, Optional

from ...types.alignment import Alignment
from ...types.player import Player
from ...util.colors import BLACK, Color
from ...util.constants import HEIGHT, WIDTH
from ..dynamic import Dynamic
from ..projectile import Projectile


class ColorizeScreen(Projectile):
    def __init__(
        self,
        color: Color = BLACK,
        alpha=BLACK.alpha,
        duration: float = -1.0,
        to_filter: bool = False,
        cameras: Optional[List[str]] = None,
    ):
        super().__init__(
            0,
            0,
            "ColorizeScreen",
            vx=0,
            vy=0,
            duration=duration,
            alignment=Alignment.GOOD,
        )
        self.layer = 1
        self.solid_vs_map = False
        self.color = color
        self.alpha = alpha
        self.vanishs_after_time: bool = duration > 0
        self.to_filter = to_filter
        self._cameras = (
            cameras if (cameras is not None and cameras) else ["C_DISPLAY"]
        )

    def update(self, elapsed_time: float, target: Dynamic = None):
        if self.vanishs_after_time:
            self.duration -= elapsed_time
            if self.duration <= 0.0:
                self.kill()

        # self.sprite.update(elapsed_time, self.facing_direction, self.graphic_state)

    def draw_self(self, ox: float, oy: float, camera_name=None):
        color = Color(
            self.color.red, self.color.green, self.color.blue, self.alpha
        )
        if camera_name in self._cameras:
            self.engine.backend.fill_rect(
                self.px,
                self.py,
                self.engine.backend.render_width,
                self.engine.backend.render_height,
                color,
                camera_name,
                draw_to_filter=self.to_filter,
            )
