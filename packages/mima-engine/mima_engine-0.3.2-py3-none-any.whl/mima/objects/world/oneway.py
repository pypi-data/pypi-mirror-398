from typing import List, Optional, Union

from ...maps.tilemap import Tilemap
from ...scripts.commands.oneway_move import CommandOnewayMove
from ...types.direction import Direction
from ...types.graphic_state import GraphicState
from ...types.nature import Nature
from ...types.object import ObjectType
from ...util.constants import ONEWAY_ACTIVATION_DELAY
from ..animated_sprite import AnimatedSprite
from ..dynamic import Dynamic


class Oneway(Dynamic):
    def __init__(
        self,
        px: float,
        py: float,
        name="Oneway",
        *,
        sprite_name: str = "",
        tilemap: Optional[Tilemap] = None,
        dyn_id=-1,
        jump_vx: float = 0.0,
        jump_vy: float = 0.0,
        width: float = 0.0,
        height: float = 0.0,
    ):
        super().__init__(
            px,
            py,
            name,
            tilemap=tilemap,
            sprite_name=sprite_name,
            dyn_id=dyn_id,
        )
        self.type = ObjectType.ONEWAY
        self.layer = 0
        self.sprite.width = int(width * self.engine.rtc.tile_width)
        self.sprite.height = int(height * self.engine.rtc.tile_height)

        self.hitbox_px, self.hitbox_py = 0.0, 0.0
        self.hitbox_width, self.hitbox_height = 1.0, 1.0
        self.solid_vs_map = False

        self.width: float = width
        self.height: float = height
        self.jump_vx: float = 0.0
        self.jump_vy: float = 0.0
        self.jump_direction = Direction.from_velocity(jump_vx, jump_vy)
        self.activation_delay: float = ONEWAY_ACTIVATION_DELAY
        self.triggered: bool = False
        self.is_active: bool = False
        self.cooldown: float = 0.0
        self.target = None

        if jump_vx < 0:
            self.jump_vx = jump_vx - 1
            # self.hitbox_px += 0.1
        elif jump_vx > 0:
            self.jump_vx = jump_vx + 1
            # self.hitbox_px -= 0.1

        if jump_vy < 0:
            self.jump_vy = jump_vy - 1
            # self.hitbox_py += 0.1
        elif jump_vy > 0:
            self.jump_vy = jump_vy + 1
            # self.hitbox_py -= 0.1

    def update(self, elapsed_time, target=None):
        self.sprite.update(
            elapsed_time, self.facing_direction, self.graphic_state
        )

        # Can only be triggered again after a certain time has passed.
        if self.cooldown >= 0.0:
            self.cooldown -= elapsed_time
            return
        else:
            self.cooldown = 0.0

        # If no interaction happened in a frame, the activation timer
        # gets resetted.
        if not self.triggered:
            self.timer = 0.0
            return

        # Activation countdown
        if self.timer > 0.0:
            self.timer -= elapsed_time

        # Activation countdown reached 0 and the jump is initiated.
        if self.timer <= 0.0 and self.target is not None:
            self.engine.script.add_command(
                CommandOnewayMove(
                    self.target,
                    self.jump_vx,
                    self.jump_vy,
                    target.get_player(),
                )
            )
            self.cooldown = 2.0
            self.is_active

        # Reset the triggered flag so it has to be activated again
        # by interaction
        self.triggered = False
        self.target = None

    def on_interaction(self, target, nature=Nature.WALK):
        if (
            target.type == ObjectType.PLAYER
            and nature == Nature.WALK
            and self.cooldown <= 0.0
        ):
            # No interaction when target is higher than the oneway
            if target.pz > 0:
                return False

            if self.jump_direction != target.facing_direction:
                return False

            tcenterx = target.px + (target.hitbox_px + target.hitbox_width) / 2
            tbottomy = target.py + target.hitbox_py + target.hitbox_height
            ttopy = target.py + target.hitbox_py
            tleftx = target.px + target.hitbox_px
            trightx = tleftx + target.hitbox_width

            # print(tcenterx, tbottomy)
            # We have to check that target is not placed "more" in the
            # target direction than the oneway
            if (
                self.jump_vx < 0
                and target.px < self.px + self.width - target.hitbox_px
            ):
                return False
            if self.jump_vx > 0 and target.px >= self.px:
                return False
            if (
                self.jump_vy < 0
                and target.py <= self.py + self.height - target.hitbox_py
            ):
                return False
            if self.jump_vy > 0 and tbottomy >= self.py:  # FIXME
                return False

            if self.jump_vx == 0:
                if target.px >= self.px + self.width:
                    return False
                if target.px + 1.0 <= self.px:
                    return False

            if self.jump_vy == 0:
                if target.py >= self.py + self.height:
                    return False
                if target.py + 1.0 <= self.py:
                    return False
            self.triggered = True
            self.target = target
            if self.timer <= 0.0:
                self.timer = self.activation_delay
                # return False

            # print(
            #     f"activated {self.timer:.3f}, {self.px, self.py}, {target.px, target.py}, {target.sprite.width, target.sprite.height}"
            # )
            return True

        return False

    def draw_self(self, ox: float, oy: float, camera_name: str = "display"):
        self.sprite.draw_self(self.px - ox, self.py - oy, camera_name)

    @staticmethod
    def load_from_tiled_object(obj, px, py, width, height, tilemap):
        oneway = Oneway(
            px,
            py,
            obj.name,
            sprite_name=obj.get_string("sprite_name"),
            tilemap=tilemap,
            dyn_id=obj.object_id,
            jump_vx=obj.get_float("jump_vx"),
            jump_vy=obj.get_float("jump_vy"),
            width=width,
            height=height,
        )
        oneway.graphic_state = (
            GraphicState[obj.get_string("graphic_state", "standing").upper()],
        )
        oneway.facing_direction = (
            Direction[obj.get_string("facing_direction", "south").upper()],
        )
        return [oneway]
