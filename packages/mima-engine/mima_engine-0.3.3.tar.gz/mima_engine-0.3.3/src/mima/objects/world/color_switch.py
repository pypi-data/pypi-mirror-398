from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Union

from ...types.direction import Direction
from ...types.gate_color import GateColor
from ...types.graphic_state import GraphicState
from ...types.nature import Nature
from ...types.object import ObjectType
from ..dynamic import Dynamic
from .switch import Switch

if TYPE_CHECKING:
    from ...maps.tilemap import Tilemap


class ColorSwitch(Switch):
    def __init__(
        self,
        px: float,
        py: float,
        name="ColorSwitch",
        *,
        sprite_name: str = "",
        tilemap: Optional[Tilemap] = None,
        dyn_id=-1,
        graphic_state: GraphicState = GraphicState.OPEN,
        initial_signal=False,
        color: GateColor = GateColor.RED,
    ):
        super().__init__(
            px,
            py,
            name,
            sprite_name=sprite_name,
            tilemap=tilemap,
            dyn_id=dyn_id,
            graphic_state=graphic_state,
            initial_signal=initial_signal,
        )
        self.type = ObjectType.COLOR_SWITCH

        self.color = color
        self.graphic_state = (
            GraphicState.CLOSED
            if color == self.engine.gate_color
            else GraphicState.OPEN
        )
        # self.signal = self.graphic_state == GraphicState.CLOSED
        # self.send_initial_signal = False

    def update(self, elapsed_time: float, target: Optional[Dynamic] = None):
        self.graphic_state = (
            GraphicState.CLOSED
            if self.color == self.engine.gate_color
            else GraphicState.OPEN
        )
        # self.signal = self.graphic_state == GraphicState.CLOSED
        #
        self.sprite.update(
            elapsed_time, self.facing_direction, self.graphic_state
        )

    def on_interaction(self, target: Dynamic, nature: Nature):
        if (
            nature == Nature.TALK
            and target.type == ObjectType.PLAYER
            and self.visible
        ):
            if self.engine.gate_color != self.color:
                self.engine.gate_color = self.color
            else:
                self.engine.gate_color = GateColor(
                    (self.color.value + 1) % self.engine.n_gate_colors
                )
            self.state_changed = True
            self.engine.audio.play_sound("switch")
            return True

        return False

    @staticmethod
    def load_from_tiled_object(obj, px, py, width, height, tilemap):
        switch = ColorSwitch(
            px=px,
            py=py,
            name=obj.name,
            sprite_name=obj.get_string("sprite_name"),
            tilemap=tilemap,
            dyn_id=obj.object_id,
            graphic_state=GraphicState[
                obj.get_string("graphic_state", "closed").upper()
            ],
            color=GateColor[obj.get_string("color", "red").upper()],
            initial_signal=False,
        )

        # switch.sprite.width = int(width * ColorSwitch.engine.rtc.tile_width)
        # switch.sprite.height = int(height * ColorSwitch.engine.rtc.tile_height)

        return [switch]
