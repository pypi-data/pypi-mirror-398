import math
from typing import List, Optional

from ...maps.tilemap import Tilemap
from ...types.alignment import Alignment
from ...types.damage import Damage
from ...types.direction import Direction
from ...types.graphic_state import GraphicState
from ...types.keys import Key as K
from ...types.nature import Nature
from ...types.object import ObjectType
from ...util.colors import BLACK
from ..animated_sprite import AnimatedSprite
from ..dynamic import Dynamic
from ..projectile import Projectile


class Movable(Dynamic):
    def __init__(
        self,
        px: float,
        py: float,
        name="Movable",
        *,
        sprite_name: str,
        tilemap: Optional[Tilemap] = None,
        dyn_id=-1,
        mrange: float = 0.0,
        liftable: bool = False,
        destroyable: bool = False,
        movable: bool = False,
        intangible: bool = False,
        force_collision_check: bool = False,
    ):
        super().__init__(
            px,
            py,
            name,
            tilemap=tilemap,
            sprite_name=sprite_name,
            dyn_id=dyn_id,
        )

        self.type = ObjectType.MOVABLE
        self.alignment = Alignment.NEUTRAL
        self.solid_vs_map = True

        self.range = mrange
        self.total_range = 0
        self.spawn_px = px
        self.spawn_py = py

        self.liftable = liftable
        self.destroyable = destroyable
        self.movable = movable
        self.intangible = intangible
        self.moving = False
        self.lift_started = False
        self.lifted = False
        self.thrown = False
        self.visible = True
        self.visible_pz = 0.0
        self.actor: Optional[Dynamic] = None
        self.vx_mask = 0
        self.vy_mask = 0
        self._vx_throw = 0
        self._vy_throw = 0
        self._speed_throw = 4.0
        self.move_direction: str = ""
        self.moves_on_collision = self.movable or self.destroyable
        # self.onscreen_collision_skippable = (
        #     not self.movable and not force_collision_check
        # )

        self._impact_offsets = [
            [0.5, 0.5],
            [-0.5, 0.5],
            [-0.5, -0.5],
            [0.5, -0.5],
        ]

    def update(self, elapsed_time: float, target: Optional[Dynamic] = None):
        if self.intangible:
            self.solid_vs_dyn = False
        else:
            self.solid_vs_dyn = (
                self.visible and not self.lifted and not self.thrown
            )
        if self.pz > 1.0:
            self.solid_vs_map = False
        else:
            self.solid_vs_map = True

        self.sprite.update(
            elapsed_time, self.facing_direction, self.graphic_state
        )

        if self.thrown:
            return self._throw()

        self.vx = self.vy = 0.0

        if self.moving:
            return self._move()

        if self.lift_started or self.lifted:
            self.moves_on_collision = True
            return self._lift()
        self.moves_on_collision = self.movable or self.destroyable

    def on_interaction(self, target: Dynamic, nature: Nature):
        if self.moving:
            return False
        if self.lifted:
            return False

        pt = target.get_player()
        if pt.value > 0:
            if nature == Nature.TALK and self.liftable and target.can_lift:
                self.lift_started = True
                self.actor = target
                self.solid_vs_dyn = False
                target.can_attack = False
                return True

            if (
                self.movable
                and self.visible
                and self.total_range < self.range
                and target.graphic_state
                in [GraphicState.WALKING, GraphicState.PUSHING]
            ):
                if (
                    target.facing_direction == Direction.WEST
                    and self.engine.keys.key_held(K.LEFT, pt)
                    and target.vy == 0
                ):
                    self.move_direction = K.LEFT
                    self.vx_mask = -1
                elif (
                    target.facing_direction == Direction.EAST
                    and self.engine.keys.key_held(K.RIGHT, pt)
                    and target.vy == 0
                ):
                    self.move_direction = K.RIGHT
                    self.vx_mask = 1
                elif (
                    target.facing_direction == Direction.SOUTH
                    and self.engine.keys.key_held(K.DOWN, pt)
                    and target.vx == 0
                ):
                    self.move_direction = K.DOWN
                    self.vy_mask = 1
                elif (
                    target.facing_direction == Direction.NORTH
                    and self.engine.keys.key_held(K.UP, pt)
                    and target.vx == 0
                ):
                    self.move_direction = K.UP
                    self.vy_mask = -1
                else:
                    return False

                self.actor = target
                self.moving = True
                self.actor.lock_graphic_state(GraphicState.PUSHING)

                return True

        elif target.type == ObjectType.PROJECTILE:
            if self.destroyable:
                damage = target.damage - self.attributes.defense[target.dtype]
                if damage > 0:
                    self.kill()
                    if target.one_hit:
                        target.kill()
                return True

        elif nature == Nature.SIGNAL:
            self.visible = False
            return True

        elif nature == Nature.NO_SIGNAL:
            self.visible = True
            return True

        return False

    def draw_self(self, ox: float, oy: float, camera_name: str = "display"):
        if not self.visible:
            return

        py = self.py - oy - (self.pz + self.visible_pz)

        if self.pz != 0:
            self.engine.backend.fill_circle(
                (self.px - ox + 0.5) * self.sprite.width,
                (self.py - oy + 0.7) * self.sprite.height,
                0.3125 * self.sprite.width,
                BLACK,
                camera_name,
            )
        self.sprite.draw_self(self.px - ox, py, camera_name)

    def _throw(self):
        if self.pz < 0.5:
            self.solid_vs_dyn = True
            self.speed = 1.0
        if self.pz > 0:
            self.vx = self._vx_throw
            self.vy = self._vy_throw
            self.speed = self._speed_throw
            return

        self._create_impact()

        # self.solid_vs_dyn = True
        self.thrown = False
        self.vx = self.vy = 0.0
        if self.destroyable:
            self.kill()
        return

    def _move(self):
        if self.actor.graphic_state == GraphicState.PUSHING:
            stop_moving = False
            for button in [K.DOWN, K.LEFT, K.UP, K.RIGHT]:
                if button == self.move_direction:
                    if self.engine.keys.key_held(
                        button, self.actor.get_player()
                    ):
                        self.vx = self.vx_mask
                        self.vy = self.vy_mask
                else:
                    if self.engine.keys.key_held(
                        button, self.actor.get_player()
                    ):
                        stop_moving = True
                        self.vx = 0
                        self.vy = 0
                        break
            if (
                abs(self.actor.px - self.px) > 1.1
                or abs(self.actor.py - self.py) > 1.1
            ):
                stop_moving = True

            if not stop_moving and abs(self.vx) > abs(self.vy):
                self.vy = 0
            elif not stop_moving and abs(self.vy) > abs(self.vx):
                self.vx = 0
            else:
                self.vx = self.vy = 0.0

        dx = self.px - self.spawn_px
        dy = self.py - self.spawn_py
        self.total_range = math.sqrt(dx * dx + dy * dy)

        if self.total_range >= self.range:
            self.vx = self.vy = 0.0

        if self.vx == 0.0 and self.vy == 0.0:
            self.moving = False
            self.vx_mask = self.vy_mask = 0
            self.actor.unlock_graphic_state()
            self.engine.audio.stop_sound("move_block")
        else:
            self.engine.audio.play_sound("move_block")
        return

    def _lift(self):
        if self.lifted and self.engine.keys.new_key_press(
            K.A, self.actor.get_player()
        ):
            # Throw away
            self.vx = self.vy = 0
            if self.actor.facing_direction == Direction.SOUTH:
                self.vy = self._vy_throw = 1
            if self.actor.facing_direction == Direction.WEST:
                self.vx = self._vx_throw = -1
            if self.actor.facing_direction == Direction.NORTH:
                self.vy = self._vy_throw = -1
            if self.actor.facing_direction == Direction.EAST:
                self.vx = self._vx_throw = 1

            self.vz = 6.0
            self.pz = self.actor.pz + 0.9
            self.visible_pz = 0
            self.actor.can_attack = True
            self.lifted = False
            self.actor = None
            self.thrown = True

        elif self.lift_started and self.engine.keys.new_key_release(
            K.A, self.actor.get_player()
        ):
            self.lift_started = False
            self.lifted = True
            self.solid_vs_dyn = False
        else:
            self.solid_vs_dyn = False
            self.px = self.actor.px
            self.py = self.actor.py
            self.visible_pz = self.actor.pz + 0.9
            self.vx = self.vy = 0.0

    def _create_impact(self):
        # impact: List[Projectile] = []
        # impact.append(
        #     Projectile(
        #         self.px + 0.5,
        #         self.py + 0.5,
        #         0,
        #         0,
        #         0.2,
        #         self.alignment,
        #         self.tilemap,
        #     )
        # )
        for idx, offsets in enumerate(self._impact_offsets):
            p = Projectile(
                self.px + offsets[0],
                self.py + offsets[1],
                f"Movable Impact {idx}",
                sprite_name="small_explosion",
                tilemap=self.tilemap,
                alignment=self.alignment,
                duration=0.2,
            )
            p.solid_vs_dyn = False
            p.solid_vs_map = False
            p.damage = 5
            # impact.append(p)
            self.engine.get_view().add_projectile(p, self.tilemap.name)

        # impact.append(
        #     Projectile(
        #         self.px - 0.5,
        #         self.py + 0.5,
        #         0,
        #         0,
        #         0.2,
        #         self.alignment,
        #         self.tilemap,
        #     )
        # )
        # impact.append(
        #     Projectile(
        #         self.px - 0.5,
        #         self.py - 0.5,
        #         0,
        #         0,
        #         0.2,
        #         self.alignment,
        #         self.tilemap,
        #     )
        # )
        # impact.append(
        #     Projectile(
        #         self.px + 0.5,
        #         self.py - 0.5,
        #         0,
        #         0,
        #         0.2,
        #         self.alignment,
        #         self.tilemap,
        #     )
        # )

        # for pro in impact:
        #     pro.sprite.name = "explosion"
        #     pro.solid_vs_dyn = False
        #     pro.solid_vs_map = False
        #     pro.damage = 5

    @staticmethod
    def load_from_tiled_object(obj, px, py, width, height, tilemap):
        movable = Movable(
            px=px,
            py=py,
            name=obj.name,
            sprite_name=obj.get_string("sprite_name"),
            tilemap=tilemap,
            dyn_id=obj.object_id,
            mrange=obj.get_float("range"),
            liftable=obj.get_bool("liftable"),
            destroyable=obj.get_bool("destroyable"),
            movable=obj.get_bool("movable"),
            intangible=obj.get_bool("intangible"),
            force_collision_check=obj.get_bool("force_collision_check"),
        )
        # movable.sprite.width = int(width * Movable.engine.rtc.tile_width)
        # movable.sprite.height = int(height * Movable.engine.rtc.tile_height)
        for dt in Damage:
            movable.attributes.defense[dt] = obj.get_int(
                f"defense_{dt.name.lower()}"
            )

        return [movable]
