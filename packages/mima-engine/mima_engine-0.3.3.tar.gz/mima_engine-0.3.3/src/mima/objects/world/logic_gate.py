from enum import Enum
from typing import List, Optional, Union

from ...maps.tilemap import Tilemap
from ...types.alignment import Alignment
from ...types.direction import Direction
from ...types.graphic_state import GraphicState
from ...types.nature import Nature
from ...types.object import ObjectType
from ..animated_sprite import AnimatedSprite
from ..dynamic import Dynamic


class LogicFunction(Enum):
    LOGIC_PASS = 0
    LOGIC_NOT = 1
    LOGIC_AND = 2
    LOGIC_OR = 3
    LOGIC_NAND = 4
    LOGIC_NOR = 5
    LOGIC_XOR = 6
    LOGIC_IMPL = 7
    LOGIC_EQUI = 8


class LogicGate(Dynamic):
    def __init__(
        self,
        px: float,
        py: float,
        name: str = "Logic Gate",
        *,
        sprite_name: str = "",
        tilemap: Optional[Tilemap] = None,
        dyn_id: int = -1,
        mode: LogicFunction = LogicFunction.LOGIC_PASS,
        initial_signal: bool = False,
        visible: bool = False,
    ):
        super().__init__(
            px,
            py,
            name,
            sprite_name=sprite_name,
            tilemap=tilemap,
            dyn_id=dyn_id,
        )

        self.type = ObjectType.LOGIC_GATE
        self.alignment = Alignment.NEUTRAL
        self.visible = visible

        self.input_id1: int = -1
        self.input_id2: int = -1

        self.mode = mode
        self.signal: bool = False
        self.last_signal: bool = False
        self.input1: bool = False
        self.input2: bool = False

        self.listener_ids: List[int] = []
        self.listeners: List[Dynamic] = []
        self.send_initial_signal: bool = initial_signal
        self.state_changed: bool = False

    def update(self, elapsed_time: float, target: Optional[Dynamic] = None):
        if self.mode == LogicFunction.LOGIC_NOT:
            self.signal = not self.input1
        elif self.mode == LogicFunction.LOGIC_AND:
            self.signal = self.input1 and self.input2
        elif self.mode == LogicFunction.LOGIC_OR:
            self.signal = self.input1 or self.input2
        else:
            self.signal = self.input1

        if self.last_signal != self.signal:
            self.state_changed = True
        else:
            self.state_changed = False

        if self.send_initial_signal or self.state_changed:
            self.send_signal(self.signal)
            self.send_initial_signal = False

        self.last_signal = self.signal

        self.graphic_state = (
            GraphicState.ON if self.signal else GraphicState.OFF
        )
        self.sprite.update(
            elapsed_time, self.facing_direction, self.graphic_state
        )

    def on_interaction(self, target: Dynamic, nature: Nature):
        if nature == Nature.SIGNAL:
            if target.dyn_id == self.input_id1:
                self.input1 = True
            elif target.dyn_id == self.input_id2:
                self.input2 = True
            else:
                return False
            return True
        elif nature == Nature.NO_SIGNAL:
            if target.dyn_id == self.input_id1:
                self.input1 = False
            elif target.dyn_id == self.input_id2:
                self.input2 = False
            else:
                return False
            return True

        return False

    def draw_self(self, ox: float, oy: float, camera_name: str = "display"):
        if self.visible:
            self.sprite.draw_self(self.px - ox, self.py - oy, camera_name)

    def send_signal(self, nature: Union[Nature, bool]):
        if isinstance(nature, bool):
            nature = Nature.SIGNAL if nature else Nature.NO_SIGNAL

        for listener in self.listeners:
            listener.on_interaction(self, nature)

    @staticmethod
    def load_from_tiled_object(obj, px, py, width, height, tilemap):
        logic = LogicGate(
            px,
            py,
            obj.name,
            sprite_name=obj.get_string("sprite_name"),
            tilemap=tilemap,
            dyn_id=obj.object_id,
            mode=LogicFunction[obj.get_string("mode", "logic_pass").upper()],
            initial_signal=obj.get_bool("initial_signal", False),
            visible=obj.get_bool("visible", True),
        )
        logic.facing_direction = Direction[
            obj.get_string("facing_direction", "south").upper()
        ]
        logic.graphic_state = GraphicState[
            obj.get_string("graphic_state", "closed").upper()
        ]
        # logic.send_initial_signal =
        # logic.sprite.width = int(width * LogicGate.engine.rtc.tile_width)
        # logic.sprite.height = int(height * LogicGate.engine.rtc.tile_height)

        ctr = 1
        while True:
            listener_id = obj.get_int(f"output{ctr}", -1)
            if listener_id < 0:
                break
            logic.listener_ids.append(listener_id)
            ctr += 1

        return [logic]
