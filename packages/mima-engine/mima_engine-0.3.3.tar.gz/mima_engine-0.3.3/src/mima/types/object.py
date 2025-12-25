from enum import Enum


class ObjectType(Enum):
    UNDEFINED = -1
    PLAYER = 0
    DYNAMIC = 1
    PROJECTILE = 2
    CREATURE = 3
    SCRIPTED_CREATURE = 4
    TELEPORT = 5
    PICKUP = 6
    MOVABLE = 7
    GATE = 8
    CONTAINER = 9
    SWITCH = 10
    FLOOR_SWITCH = 11
    ONEWAY = 12
    LOGIC_GATE = 13
    LIGHT_SOURCE = 14
    COLOR_SWITCH = 15
    COLOR_GATE = 16
