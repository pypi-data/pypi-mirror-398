from enum import Enum


class GraphicState(Enum):
    STANDING = 0
    WALKING = 1
    ATTACKING = 2
    DAMAGED = 3
    CELEBRATING = 4
    DEAD = 5
    DEFEATED = 6
    PUSHING = 7
    OPEN = 8
    CLOSED = 9
    LOCKED = 10
    OFF = 11
    ON = 12
    ICON = 13


class Until(Enum):
    UNLOCK = 0
    NEXT_UPDATE = 1
