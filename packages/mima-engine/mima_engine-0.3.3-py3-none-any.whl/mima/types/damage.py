from enum import Enum


class Damage(Enum):
    NO_DAMAGE = 0
    BODY = 1
    SLICING = 2
    PIERCING = 3
    HEAVY = 4
    EXPLOSION = 5
    MAGIC = 6
    FIRE = 7
    WATER = 8
    WIND = 9
    EARTH = 10
    HEAL = 11
    DARK = 12
    FRONT = 13
    SIDE = 14
    BACK = 15


PHYSICAL = [
    Damage.BODY,
    Damage.SLICING,
    Damage.PIERCING,
    Damage.HEAVY,
    Damage.EXPLOSION,
    Damage.FRONT,
    Damage.SIDE,
    Damage.BACK,
]

MAGICAL = [
    Damage.MAGIC,
    Damage.FIRE,
    Damage.WATER,
    Damage.WIND,
    Damage.EARTH,
    Damage.HEAL,
    Damage.DARK,
]
