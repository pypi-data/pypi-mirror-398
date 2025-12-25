from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Tuple

from ..types.damage import Damage
from ..types.direction import Direction
from .item import Item

if TYPE_CHECKING:
    from ..objects.creature import Creature


class Weapon(Item):
    def __init__(self):
        super().__init__()

        self.equipable = True

        self.damage: int = 0
        self.dtype: Damage = Damage.BODY
        self.health_cost: float = 0.0
        self.magic_cost: float = 0.0
        self.stamina_cost: float = 0.0
        self.arrow_cost: int = 0
        self.bomb_cost: int = 0
        self.swing_timer: float = 0.2

    def init(self, data: Dict[str, Any]):
        for key, val in data.items():
            setattr(self, key, val)
        # self.usable_id = data["usable_id"]
        # self.name = data["display_name"]
        # self.description = data["description"]
        # self.sprite_name = data["sprite_name"]
        # self.price = data["attr_price"]
        # self.swing_timer = data["attr_swing_timer"]
        # self.damage = data["attr_damage"]
        # self.dtype = data["attr_dtype"]
        # self.health_cost = data["attr_health_cost"]
        # self.magic_cost = data["attr_magic_cost"]
        # self.stamina_cost = data["attr_stamina_cost"]
        # self.bomb_cost = data["attr_bomb_cost"]
        # self.arrow_cost = data["attr_arrow_cost"]
        # print()

    def _determine_attack_origin(self, obj: Creature) -> Tuple[float, float]:
        vx = 0.0
        vy = 0.0

        if obj.facing_direction == Direction.SOUTH:
            vy = 1.0
        if obj.facing_direction == Direction.WEST:
            vx = -1.0
        if obj.facing_direction == Direction.NORTH:
            vy = -1.0
        if obj.facing_direction == Direction.EAST:
            vx = 1.0

        return vx, vy

    def on_equip(self, obj: Creature):
        pass

    def on_unequip(self, obj: Creature):
        pass

    def on_interaction(self, target: Creature):
        return True  # Add to inventory
