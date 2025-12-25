from typing import List, Optional, Union

from ...maps.tilemap import Tilemap
from ...types.direction import Direction
from ...types.gate_color import GateColor
from ...types.graphic_state import GraphicState
from ...types.nature import Nature
from ...types.object import ObjectType
from ..dynamic import Dynamic
from .gate import Gate


class ColorGate(Gate):

    def __init__(
        self,
        px: float,
        py: float,
        name: str = "ColorGate",
        *,
        sprite_name: str = "",
        tilemap: Optional[Tilemap] = None,
        dyn_id: int = -1,
        graphic_state: GraphicState = GraphicState.STANDING,
        facing_direction: Direction = Direction.SOUTH,
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
            facing_direction=facing_direction,
            bombable=False,
        )
        self.color = color
        self.type = ObjectType.COLOR_GATE

    def update(self, elapsed_time, float, target: Optional[Dynamic] = None):
        self.open = self.engine.gate_color == self.color
        super().update(elapsed_time, target)

    def on_interaction(self, target: Dynamic, nature: Nature):
        return False

    @staticmethod
    def load_from_tiled_object(obj, px, py, width, height, tilemap):
        gate = ColorGate(
            px=px,
            py=py,
            name=obj.name,
            sprite_name=obj.get_string("sprite_name"),
            tilemap=tilemap,
            dyn_id=obj.object_id,
            graphic_state=GraphicState[
                obj.get_string("graphic_state", "closed").upper()
            ],
            facing_direction=Direction[
                obj.get_string("facing_direction", "south").upper()
            ],
            color=GateColor[obj.get_string("color", "red").upper()],
        )

        return [gate]
