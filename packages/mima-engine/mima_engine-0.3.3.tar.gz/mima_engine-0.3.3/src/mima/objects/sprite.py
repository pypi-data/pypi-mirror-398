from ..types.direction import Direction
from ..types.graphic_state import GraphicState
from ..util.constants import (
    DEFAULT_GRAPHIC_TIMER,
    DEFAULT_GRAPHIC_TIMER_DAMAGED,
    DEFAULT_GRAPHIC_TIMER_DEAD,
    DEFAULT_GRAPHIC_TIMER_STANDING,
    DEFAULT_GRAPHIC_TIMER_WALKING,
    DEFAULT_SPRITE_HEIGHT,
    DEFAULT_SPRITE_WIDTH,
)


class Sprite:
    engine = None

    def __init__(self, name: str = "", *, ox=0, oy=0, width=0, height=0):
        self.name = name
        self.ox: int = 0
        self.oy: int = 0
        self.width: int = DEFAULT_SPRITE_WIDTH if width == 0 else width
        self.height: int = DEFAULT_SPRITE_HEIGHT if height == 0 else height
        self.num_frames: int = 1
        self.frame_index: int = 0

        self.timer: float = 0.25
        self.timer_reset: float = 0.5

        self.last_direction: Direction = Direction.SOUTH
        self.last_graphic_state: GraphicState = GraphicState.STANDING

    def update(
        self,
        elapsed_time: float,
        direction: Direction = Direction.SOUTH,
        graphic_state: GraphicState = GraphicState.STANDING,
    ):
        if (
            direction == self.last_direction
            and graphic_state == self.last_graphic_state
        ):
            # Nothing has changed, normal case
            self.timer -= elapsed_time

            if self.timer <= 0.0:
                self.timer += self.timer_reset
                self.frame_index = (self.frame_index + 1) % self.num_frames

        else:
            # Something changed
            if graphic_state != self.last_graphic_state:
                # State changed
                if graphic_state == GraphicState.STANDING:
                    self.timer_reset = DEFAULT_GRAPHIC_TIMER_STANDING
                elif graphic_state == GraphicState.WALKING:
                    self.timer_reset = DEFAULT_GRAPHIC_TIMER_WALKING
                elif graphic_state == GraphicState.DAMAGED:
                    self.timer_reset = DEFAULT_GRAPHIC_TIMER_DAMAGED
                elif graphic_state == GraphicState.DEAD:
                    self.timer_reset = DEFAULT_GRAPHIC_TIMER_DEAD
                elif graphic_state == GraphicState.PUSHING:
                    self.timer_reset = DEFAULT_GRAPHIC_TIMER_WALKING
                else:
                    self.timer_reset = DEFAULT_GRAPHIC_TIMER

                # self.timer = self.timer_reset
                # self.frame_index = 0

            self.timer = self.timer_reset
            self.frame_index = 0

        self.last_direction = direction
        self.last_graphic_state = graphic_state

    def draw_self(
        self,
        px: float,
        py: float,
        camera_name: str = "display",
        draw_to_ui: bool = False,
    ):
        if self.name == "":
            return

        sheet_ox = sheet_oy = 0
        state_value = self.last_graphic_state.value

        if self.last_graphic_state == GraphicState.CELEBRATING:
            sheet_ox = (self.ox + self.frame_index) * self.width
            sheet_oy = (self.oy + state_value) * self.height
        elif self.last_graphic_state == GraphicState.DEAD:
            sheet_ox = (self.ox + 2 + self.frame_index) * self.width
            sheet_oy = (self.oy + state_value) * self.height
        else:
            if self.last_graphic_state == GraphicState.PUSHING:
                state_value -= 1
            sheet_ox = (
                self.ox + 2 * self.last_direction.value + self.frame_index
            ) * self.width
            sheet_oy = (self.oy + state_value) * self.height

        self.engine.backend.draw_partial_sprite(
            px * self.engine.rtc.tile_width,
            py * self.engine.rtc.tile_height,
            self.name,
            sheet_ox,
            sheet_oy,
            self.width,
            self.height,
            camera_name,
            draw_to_ui=draw_to_ui,
        )

    def reset(self):
        self.frame_index = 0
        self.timer = 0.0
