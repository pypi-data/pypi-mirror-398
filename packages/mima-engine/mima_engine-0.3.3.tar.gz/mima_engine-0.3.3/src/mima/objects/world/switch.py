from typing import List, Optional, Union

from ...maps.tilemap import Tilemap
from ...types.alignment import Alignment
from ...types.direction import Direction
from ...types.graphic_state import GraphicState
from ...types.nature import Nature
from ...types.object import ObjectType
from ..animated_sprite import AnimatedSprite
from ..dynamic import Dynamic


class Switch(Dynamic):
    def __init__(
        self,
        px: float,
        py: float,
        name="Switch",
        *,
        sprite_name: str = "",
        tilemap: Optional[Tilemap] = None,
        dyn_id=0,
        graphic_state: GraphicState = GraphicState.OPEN,
        initial_signal=True,
    ):
        if graphic_state not in [GraphicState.OPEN, GraphicState.CLOSED]:
            msg = (
                f"graphic_state of Switch {name}{dyn_id} must be either "
                f" 'open' or 'closed', but it is {graphic_state.name}"
            )
            raise ValueError(msg)

        super().__init__(
            px,
            py,
            name,
            tilemap=tilemap,
            sprite_name=sprite_name,
            dyn_id=dyn_id,
        )

        self.type = ObjectType.SWITCH
        self.alignment = Alignment.NEUTRAL
        self.graphic_state = graphic_state
        self.signal = self.graphic_state == GraphicState.CLOSED
        self.listener_ids: List[int] = []
        self.listeners: List[Dynamic] = []
        self.send_initial_signal = initial_signal
        self.cooldown = 0.0
        self.cooldown_reset = 0.8

        # self._gs_map = {False: GraphicState.OPEN, True: GraphicState.CLOSED}

    def update(self, elapsed_time: float, target: Optional[Dynamic] = None):
        if self.cooldown > 0.0:
            self.cooldown -= elapsed_time

        if self.send_initial_signal:
            self.send_signal(self.signal)
            self.send_initial_signal = False

        self.solid_vs_dyn = self.visible
        self.graphic_state = (
            GraphicState.CLOSED if self.signal else GraphicState.OPEN
        )
        self.sprite.update(
            elapsed_time, self.facing_direction, self.graphic_state
        )

    def draw_self(self, ox: float, oy: float, camera_name: str = "display"):
        if not self.visible:
            # print(f"{self.name} is not visible")
            return
        self.sprite.draw_self(self.px - ox, self.py - oy, camera_name)

    def on_interaction(self, target: Dynamic, nature: Nature):
        # if target.is_player().value > 0:
        #     print(f"{target.is_player()} talked to me({self.name})")
        if self.cooldown > 0.0:
            return False

        if (
            nature == Nature.TALK
            and target.type == ObjectType.PLAYER
            and self.visible
        ):
            self.state_changed = True
            self.engine.audio.play_sound("switch", 0.2)
            self.cooldown = self.cooldown_reset
            # print("Player talked")

        elif nature == Nature.WALK and target.type == ObjectType.PROJECTILE:
            if self.signal:
                # Projectiles from the right will activate the switch
                if target.px > self.px and target.vx < 0:
                    self.state_changed = True
                    if "body" not in target.name:
                        self.engine.audio.play_sound("switch", 0.2)
                        self.cooldown = self.cooldown_reset
            else:
                # Projectiles from the left will (de)activate the switch
                if (
                    target.px <= self.px and target.vx > 0
                ):  # Sword does not activate because vx=0
                    self.state_changed = True
                    if "body" not in target.name:
                        self.engine.audio.play_sound("switch", 0.2)
                        self.cooldown = self.cooldown_reset

        elif nature == Nature.SIGNAL:
            self.visible = False
            return True

        elif nature == Nature.NO_SIGNAL:
            self.visible = True
            return True

        if self.state_changed:
            self.signal = not self.signal
            self.send_signal(self.signal)

            if target.type == ObjectType.PROJECTILE:
                target.kill()
            return True
        return False

    def send_signal(self, nature: Union[Nature, bool]):
        if isinstance(nature, bool):
            nature = Nature.SIGNAL if nature else Nature.NO_SIGNAL

        for listener in self.listeners:
            listener.on_interaction(self, nature)

        # if (
        #     not self.send_initial_signal
        #     and abs(self.engine.player.px - self.px)
        #     < (self.engine.backend.render_width // (TILE_WIDTH * 2))
        #     and abs(self.engine.player.py - self.py)
        #     < (self.engine.backend.render_height // (TILE_HEIGHT * 2))
        # ):
        #     print(
        #         (
        #             self.engine.player.px - self.px,
        #             self.engine.player.py - self.py,
        #         ),
        #         (
        #             self.engine.backend.render_width // (TILE_WIDTH * 2),
        #             self.engine.backend.render_height // (TILE_HEIGHT * 2),
        #         ),
        #     )

    @staticmethod
    def load_from_tiled_object(obj, px, py, width, height, tilemap):
        switch = Switch(
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

        # switch.sprite.width = int(width * Switch.engine.rtc.tile_width)
        # switch.sprite.height = int(height * Switch.engine.rtc.tile_height)

        ctr = 1
        while True:
            key = f"output{ctr}"
            listener_id = obj.get_int(key, -1)
            if listener_id < 0:
                break
            switch.listener_ids.append(listener_id)
            ctr += 1

        return [switch]
