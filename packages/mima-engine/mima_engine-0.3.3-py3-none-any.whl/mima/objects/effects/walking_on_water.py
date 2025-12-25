from ...types.direction import Direction
from ...types.graphic_state import GraphicState
from ..dynamic import Dynamic
from .walking_on_grass import WalkingOnGrass


class WalkingOnWater(WalkingOnGrass):
    def __init__(
        self,
        follow: Dynamic,
        name: str = "WalkingOnWater",
        sprite_name: str = "walking_on_water",
    ):
        super().__init__(follow, name, sprite_name)
        # self.sprite.name = "simple_sheet"
        # self.sprite.ox = 32
        # self.sprite.oy = 9
        # self.sprite.num_frames = 2
        # self.sprite.timer = 0.2
        # self.sprite.timer_reset = 0.2
        self._follow = follow
        self.renew: bool = True
        self.solid_vs_map = False

    # def update(self, elapsed_time: float, target: Dynamic = None):
    #     if not self.renew:
    #         self.kill()

    #     self.px = (
    #         self._follow.px
    #         + (self._follow.sprite.width - self.sprite.width)
    #         / 2
    #         / self.engine.rtc.tile_width
    #     )
    #     self.py = (
    #         self._follow.py
    #         + (self._follow.sprite.height - self.sprite.height)
    #         / self.engine.rtc.tile_height
    #     )

    #     if self._follow.graphic_state == GraphicState.STANDING:
    #         elapsed_time = 0
    #     self.sprite.update(
    #         elapsed_time, Direction.SOUTH, GraphicState.STANDING
    #     )

    #     self.renew = False

    def draw_self(self, ox: float, oy: float, camera_name: str):
        if (
            self.sprite.name is None
            or self.sprite.name == ""
            or self.redundant
        ):
            return

        self.sprite.draw_self(self.px - ox, self.py - oy, camera_name)
