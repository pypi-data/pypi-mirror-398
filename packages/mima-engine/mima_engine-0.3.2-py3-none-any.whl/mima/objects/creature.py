from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List, Optional

from ..types.direction import Direction
from ..types.graphic_state import GraphicState, Until
from ..types.nature import Nature
from ..types.object import ObjectType
from ..types.player import Player
from ..types.terrain import Terrain
from ..types.weapon_slot import WeaponSlot

# from ..types.weapon_slot import WeaponSlot
from ..util.colors import BLACK
from ..util.constants import DEFAULT_KNOCK_SPEED
from .animated_sprite import AnimatedSprite
from .dynamic import Dynamic
from .effects.light import Light
from .effects.walking_on_grass import WalkingOnGrass
from .effects.walking_on_water import WalkingOnWater
from .projectile import Projectile

if TYPE_CHECKING:
    from ..maps.tilemap import Tilemap
    from ..usables.weapon import Weapon
    from ..util.trading_item import TradingItem


class Creature(Dynamic):
    def __init__(
        self,
        px: float = 0,
        py: float = 0,
        name: str = "Unnamed Creature",
        *,
        sprite_name: str = "",
        tilemap: Tilemap = None,
        dyn_id: int = -1,
        player: Player = Player.P0,
    ):
        super().__init__(
            px,
            py,
            name,
            sprite_name=sprite_name,
            tilemap=tilemap,
            dyn_id=dyn_id,
        )

        # self.sprite = self.engine.db.get_sprite(
        #     sprite_name
        # )  # AnimatedSprite(tileset_name, image_name, sprite_name)
        self.player = player
        self.type = ObjectType.CREATURE
        self.knock_speed: float = DEFAULT_KNOCK_SPEED

        # self.sprite.name = sprite_name
        # self.sprite.num_frames = 2
        self.attackable = True
        self.knockable = True
        self.moves_on_collision = True

        self._knock_vx: float = 0.0
        self._knock_vy: float = 0.0
        self.real_vx: float = 0.0
        self.real_vy: float = 0.0
        self.last_vx: float = 0.0
        self.last_vy: float = 0.0
        self._attack_timer: float = 0.0
        self._invincible_timer: float = 0.0
        self._knock_timer: float = 0.0
        self._state_timer: float = 0.0

        self.invincible: bool = False
        # self.use_acceleration: bool = True
        # self.use_friction: bool = True

        self.projectiles: List[Projectile] = []
        self.weapons: Dict[WeaponSlot, Optional[Weapon]] = {
            WeaponSlot.FIRST_HAND: None,
            WeaponSlot.SECOND_HAND: None,
        }
        self._light = None

        # self.attributes.speed = 1.0
        # self.use_acceleration = True
        # self.use_friction = True
        # self.attributes.friction = 0.1

    def start_shining(self):
        self._light = Light(self, fixed_size=True, update_from_target=True)
        self.engine.get_view().add_effect(self._light, self.tilemap.name)

    def stop_shining(self):
        if self._light is not None:
            self._light.kill()
            self._light = None

    def update(self, elapsed_time: float, target: Optional[Dynamic] = None):
        if not self.visible:
            self.vx = self.vy = 0.0
            return

        if self._knock_timer > 0.0:  # Handle knocking
            self._knock_timer -= elapsed_time
            self._invincible_timer -= elapsed_time
            self.vx, self.vy = self._knock_vx, self._knock_vy
            self.speed = self.knock_speed
            self.change_graphic_state(GraphicState.DAMAGED)

            if self._knock_timer <= 0.0:  # Knocking is over
                self._state_timer = 0.0
                self.controllable = True
                self.solid_vs_dyn = True
                self.sprite.reset()

        else:  # Usual update
            if self._invincible_timer > 0.0:
                self._invincible_timer -= elapsed_time
            if self._invincible_timer <= 0.0:
                self.invincible = False
                self.knockable = True
                self._invincible_timer = 0.0

            if self._attack_timer > 0.0:
                self._attack_timer -= elapsed_time
                self.change_graphic_state(GraphicState.ATTACKING)

            if self._attack_timer <= 0:
                self._attack_timer = 0.0
                if abs(self.vx) > 0 or abs(self.vy) > 0:
                    self.change_graphic_state(GraphicState.WALKING)
                else:
                    self.change_graphic_state(GraphicState.STANDING)

            if self.attributes.health <= 0:
                self.change_graphic_state(GraphicState.DEAD)

            if self.can_act():
                self.behavior(elapsed_time, target)

            if self.vx < -0.01:
                self.facing_direction = Direction.WEST
            if self.vx > 0.01:
                self.facing_direction = Direction.EAST
            if self.vy < -0.01:
                self.facing_direction = Direction.NORTH
            if self.vy > 0.01:
                self.facing_direction = Direction.SOUTH

            self.speed = self.attributes.speed

        self.sprite.update(
            elapsed_time, self.facing_direction, self.graphic_state
        )

        self._handle_terrain(elapsed_time)

        if self.graphic_state == GraphicState.DEAD:
            self.attackable = False
            self.vx = self.vy = 0
            if self.despawn_timer is None:
                self.despawn_timer = self.despawn_duration
                self.engine.play_sound("enemy_killed")
            else:
                self.despawn_timer -= elapsed_time

            if self.despawn_timer <= 0.0:
                self.kill()
        else:
            eff2r = []
            for eff in self.attribute_effects:
                if (
                    self.attributes.health < eff.health_cost
                    or self.attributes.magic < eff.magic_cost
                    or self.attributes.stamina < eff.stamina_cost
                    # and self.attributes.arrows >= weapon.arrow_cost
                    # and self.attributes.bombs >= weapon.bomb_cost
                ):
                    eff.redundant = True
                    self.attributes.health_per_second += eff.health_cost
                    self.attributes.magic_per_second += eff.magic_cost
                    self.attributes.stamina_per_second += eff.stamina_cost
                    eff2r.append(eff)
            for e in eff2r:
                self.attribute_effects.remove(e)

            self.attributes.update(elapsed_time)

        if self._gs_lock_condition == Until.NEXT_UPDATE:
            self.graphic_state_locked = False

    def draw_self(self, ox: float, oy: float, camera_name: str = "display"):
        if (
            self.sprite.name is None
            or self.sprite.name == ""
            or not self.visible
        ):
            return

        px = self.px - ox + self.extra_ox
        py = self.py - oy + self.extra_oy

        if self.pz != 0:
            self.engine.backend.fill_circle(
                (px + 0.5) * self.sprite.width,
                (py + 0.7) * self.sprite.height,
                0.3125 * self.sprite.width,
                BLACK,
                camera_name,
            )

        self.sprite.draw_self(px, py - self.pz, camera_name)
        # for effect in self.effects:
        #     effect.draw_self(px, py - self.pz)

    def behavior(self, elapsed_time: float, target: Optional[Dynamic] = None):
        # No default behavior
        pass

    def on_interaction(self, target=None, nature=Nature.WALK):
        if nature == Nature.SIGNAL:
            self.solid_vs_dyn = False
            self.visible = False
            return True

        elif nature == Nature.NO_SIGNAL:
            self.visible = True
            self.solid_vs_dyn = True
            return True
        return False

    def knock_back(self, vx: float, vy: float, dist: float):
        if self.knockable:
            self._knock_vx = vx
            self._knock_vy = vy
            self._knock_timer = dist

            self.knockable = False
            self._invincible_timer = dist + 0.5
            # self.solid_vs_dyn = False
            self.controllable = False
            self.invincible = True
            self.sprite.reset()
            self.cancel_attack()

    def can_act(self):
        actable_states = [
            GraphicState.STANDING,
            GraphicState.WALKING,
            GraphicState.CELEBRATING,
            # GraphicState.DAMAGED,
            GraphicState.PUSHING,
        ]
        if self.graphic_state in actable_states:
            return True

        return False

    def perform_attack(self, slot: WeaponSlot) -> bool:
        weapon = self.weapons.get(slot, None)

        if weapon is None or not self.can_attack:
            # print(f"Cannot attack. Weapon={weapon}")
            return False

        # Clean up all previous projectiles
        self.cancel_attack()

        if (
            self.attributes.health >= weapon.health_cost
            and self.attributes.magic >= weapon.magic_cost
            and self.attributes.stamina >= weapon.stamina_cost
            and self.attributes.arrows >= weapon.arrow_cost
            and self.attributes.bombs >= weapon.bomb_cost
        ):
            self.attributes.health -= weapon.health_cost
            self.attributes.magic -= weapon.magic_cost
            self.attributes.stamina -= weapon.stamina_cost
            self.attributes.arrows -= weapon.arrow_cost
            self.attributes.bombs -= weapon.bomb_cost
        else:
            return False

        if weapon.on_use(self):
            self.vx = self.vy = 0.0
            self._attack_timer = weapon.swing_timer
            return True

        return False

    def cancel_attack(self):
        # if self.projectiles:
        for projectile in self.projectiles:
            if projectile is not None:
                projectile.spawn_on_death = []
                projectile.kill()

        self.projectiles = []

    def on_enter_map(self):
        pass

    def on_exit_map(self):
        pass

    def on_death(self):
        if self.spawn_on_death:
            for do in self.spawn_on_death:
                if do.redundant:
                    continue
                if do.type == ObjectType.PROJECTILE:
                    if do.inherit_pos:
                        do.px = self.px
                        do.py = self.py
                    self.engine.get_view().add_projectile(
                        do, self.tilemap.name
                    )
                else:
                    self.engine.get_view().add_dynamic(do, self.tilemap.name)

        self.spawn_on_death = []

    def _handle_terrain(self, elapsed_time: float):
        e2rm = []
        for effect in self.effects:
            if isinstance(effect, WalkingOnGrass):
                if self.walking_on == Terrain.DEFAULT:
                    e2rm.append(effect)

        for effect in e2rm:
            self.effects.remove(effect)

        if self.walking_on in [Terrain.GRASS, Terrain.SHALLOW_WATER]:
            self.attributes.speed_mod = 0.7
            effect_active = False
            for effect in self.effects:
                if isinstance(effect, (WalkingOnGrass, WalkingOnWater)):
                    effect_active = True
                    effect.renew = True
                    break

            if not effect_active:
                if self.walking_on == Terrain.GRASS:
                    eff = WalkingOnGrass(self)
                else:
                    eff = WalkingOnWater(self)
                self.effects.append(eff)
                self.engine.get_view().add_effect(eff, self.tilemap.name)
        else:
            self.attributes.speed_mod = 1.0

    def equip_weapon(self, slot, weapon):
        if self.weapons[slot] == weapon:
            # Weapon already equipped; unequip
            self.weapons[slot] = None
            weapon.on_unequip(self)
            return

        for s, w in self.weapons.items():
            if slot != s and weapon == w:
                # Weapon equipped in a different slot; change
                if self.weapons[slot] is not None:
                    self.weapons[slot].on_unequip(self)
                self.weapons[slot] = weapon
                self.weapons[s] = None
                return

        if self.weapons[slot] is not None:
            # Other weapon equipped; unequip that
            self.weapons[slot].on_unequip(self)

        self.weapons[slot] = weapon
        weapon.on_equip(self)

    def unequip_weapon(self, slot):
        if self.weapons[slot] is not None:
            self.weapons[slot].on_unequip(self)

    def get_trading_items(self) -> List[TradingItem]:
        return []

    def __str__(self):
        return f"C({self.name}, {self.dyn_id})"
