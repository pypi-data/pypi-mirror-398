from ...types.direction import Direction
from ...types.graphic_state import GraphicState
from ..dynamic import Dynamic
from ..projectile import Projectile


class WalkingOnGrass(Projectile):
    def __init__(
        self,
        follow: Dynamic,
        name: str = "WalkingOnGrass",
        sprite_name: str = "walking_on_grass",
    ):
        super().__init__(
            follow.px,
            follow.py,
            name,
            sprite_name=sprite_name,
            tilemap=follow.tilemap,
            vx=0,
            vy=0,
            duration=1.0,
            alignment=follow.alignment,
        )
        self.layer = 0
        # self.sprite.name = "simple_sheet"
        # self.sprite.ox = 32
        # self.sprite.oy = 10
        # self.sprite.num_frames = 2
        # self.sprite.timer = 0.2
        # self.sprite.timer_reset = 0.2
        self._follow = follow
        self.renew: bool = True
        self.solid_vs_map = False
        # self.moves_on_collision = False

    def update(self, elapsed_time: float, target: Dynamic = None):
        if not self.renew:
            self.kill()

        self.px = (
            self._follow.px
            + (self._follow.sprite.width - self.sprite.width)
            / 2
            / self.engine.rtc.tile_width
        )
        self.py = (
            self._follow.py
            + (self._follow.sprite.height - self.sprite.height)
            / self.engine.rtc.tile_height
        )

        if self._follow.graphic_state == GraphicState.WALKING:
            self.graphic_state = GraphicState.WALKING
        else:
            self.graphic_state = GraphicState.STANDING
            # elapsed_time = 0
        self.sprite.update(elapsed_time, Direction.SOUTH, self.graphic_state)

        self.renew = False

    def draw_self(self, ox: float, oy: float, camera_name):
        if (
            self.sprite.name is None
            or self.sprite.name == ""
            or self.redundant
        ):
            return

        self.sprite.draw_self(self.px - ox, self.py - oy, camera_name)
