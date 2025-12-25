from typing import Dict

from ..types.damage import Damage
from ..util.constants import ATTRIBUTE_TIMER


class Attributes:
    """A class holding all the attributes of an object.

    Attributes
    ----------

    health: float
        The current health of the object.
    health_max: float
        The maximum health of the object.
    speed: float
        The current speed value of the object. If different run speeds
        are not relevant for the object, this is the only value to
        consider. Otherwise, this value might be changed by objects
        itself to reflect different states.
    speed_mod: float
        A modification of the speed used by the game engine, e.g., when
        walking in shallow water
    walk_speed: float
        The speed value when the objects moves slow, e.g., when it is
        walking.
    run_speed: float
        The speed value when the object moves fast, e.g., when it is
        running.
    acceleration: float
        The acceleration of the object when it starts to move. Ranges
        between 0 and 1
    friction: float
        The friction of the object when it stops moving. Ranges between
        0 and 1.

    """

    def __init__(self):
        self.health: float = 10.0
        self.health_max: float = 10.0
        self.health_per_second: float = 0.0
        self.magic: float = 10.0
        self.magic_max: float = 10.0
        self.magic_per_second: float = 0.1
        self.stamina: float = 10.0
        self.stamina_max: float = 10.0
        self.stamina_per_second: float = 2.0
        self.speed: float = 1.0
        self.speed_mod: float = 1.0
        self.walk_speed: float = 1.0
        self.run_speed: float = 1.0
        # self.current_speed: float = 0.0  # Acceleration and Friction
        self.knock_speed: float = 5.0
        self.acceleration: float = 15.0
        self.friction: float = 15.0

        self.timer: float = 0.25
        self.gravity_vz: float = 40.0
        self.light_radius: float = 32

        self.coins: int = 0
        self.coins_max: int = 100_000
        self.keys: int = 0
        self.keys_max: int = 100_000
        self.bombs: int = 0
        self.bombs_max: int = 5
        self.arrows: int = 0
        self.arrows_max: int = 15

        self.body_damage: int = 0

        self.strength: int = 0
        self.dexterity: int = 0
        self.intelligence: int = 0
        self.wisdom: int = 0
        self.initiative: int = 0

        self.sell_factor: float = 1.0
        self.buy_factor: float = 1.0

        self.experience: int = 0
        self.defense: Dict[Damage, int] = {dt: 0 for dt in Damage}

    def update(self, elapsed_time: float):
        self.timer -= elapsed_time
        if self.timer <= 0.0:
            self.timer += ATTRIBUTE_TIMER

            self.health = min(
                self.health + self.health_per_second * ATTRIBUTE_TIMER,
                self.health_max,
            )
            self.magic = min(
                self.magic + self.magic_per_second * ATTRIBUTE_TIMER,
                self.magic_max,
            )
            self.stamina = min(
                self.stamina + self.stamina_per_second * ATTRIBUTE_TIMER,
                self.stamina_max,
            )

    @staticmethod
    def from_dict(data):
        attr = Attributes()

        for key, val in data.items():
            if "defense" in key:
                def_key = key.split("_", 1)[1]
                attr.defense[def_key] = val
            setattr(attr, key, val)

        return attr

    @property
    def health_percent(self):
        return self.health / self.health_max

    @property
    def magic_percent(self):
        return self.magic / self.magic_max

    @property
    def stamina_percent(self):
        return self.stamina / self.stamina_max
