from typing import Optional

from ...maps.tilemap import Tilemap
from ...types.direction import Direction
from ...types.graphic_state import GraphicState
from ...types.nature import Nature
from ...types.object import ObjectType
from ..dynamic import Dynamic
from .switch import Switch


class FloorSwitch(Switch):
    def __init__(
        self,
        px: float,
        py: float,
        name="Floor Switch",
        *,
        sprite_name: str = "",
        tilemap: Optional[Tilemap] = None,
        dyn_id: int = -1,
        graphic_state: GraphicState = GraphicState.OPEN,
        initial_signal: bool = True,
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
        self.layer = 0

        self.type = ObjectType.FLOOR_SWITCH
        self.interacted = False
        self.interacted_before = False
        self.solid_vs_dyn = False

    def update(self, elapsed_time: float, target: Dynamic):
        if self.send_initial_signal:
            self.send_signal(self.signal)
            self.send_initial_signal = False
        self.state_changed = False
        if not self.interacted:
            if self.interacted_before:
                self.state_changed = True
            self.interacted_before = False

        else:
            if not self.interacted_before:
                self.state_changed = True
            self.interacted_before = True

        self.interacted = False

        if self.state_changed:
            self.signal = not self.signal
            self.send_signal(self.signal)

        self.graphic_state = (
            GraphicState.CLOSED if self.signal else GraphicState.OPEN
        )
        self.sprite.update(
            elapsed_time, self.facing_direction, self.graphic_state
        )

    def on_interaction(self, target: Dynamic, nature: Nature):
        if nature == Nature.WALK and not target.type == ObjectType.PROJECTILE:
            if target.type == ObjectType.MOVABLE:
                if not target.visible:
                    return False
            self.interacted = True
            return True

        return False

    @staticmethod
    def load_from_tiled_object(obj, px, py, width, height, tilemap):
        fswitch = FloorSwitch(
            px=px,
            py=py,
            name=obj.name,
            sprite_name=obj.get_string("sprite_name"),
            tilemap=tilemap,
            dyn_id=obj.object_id,
            graphic_state=GraphicState[
                obj.get_string("graphic_state", "closed").upper()
            ],
            initial_signal=obj.get_bool("initial_signal", True),
        )
        # TODO: Why was this used?
        # fswitch.sprite.width = int(width * FloorSwitch.engine.rtc.tile_width)
        # fswitch.sprite.height = int(
        #     height * FloorSwitch.engine.rtc.tile_height
        # )

        ctr = 1
        while True:
            key = f"output{ctr}"
            listener_id = obj.get_int(key, -1)
            if listener_id < 0:
                break
            fswitch.listener_ids.append(listener_id)
            ctr += 1

        return [fswitch]
