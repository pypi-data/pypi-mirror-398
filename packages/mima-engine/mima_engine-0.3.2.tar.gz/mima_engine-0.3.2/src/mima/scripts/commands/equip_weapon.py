from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from ..command import Command

if TYPE_CHECKING:
    from ...objects.creature import Creature
    from ...types.weapon_slot import WeaponSlot
    from ...usables.weapon import Weapon


class CommandEquipWeapon(Command):
    def __init__(self, weapon: Weapon, creature: Creature, slot: WeaponSlot):
        super().__init__()

        self._weapon: Weapon = weapon
        self._target: Creature = creature
        self._slot: WeaponSlot = slot

    def start(self):
        self._target.equip_weapon(self._slot, self._weapon)
        self.completed = True
