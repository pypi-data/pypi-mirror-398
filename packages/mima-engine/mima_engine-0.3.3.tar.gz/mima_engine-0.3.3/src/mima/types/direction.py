from __future__ import annotations

from enum import Enum
from typing import Tuple


class Direction(Enum):
    SOUTH = 0
    WEST = 1
    NORTH = 2
    EAST = 3

    def from_velocity(vx: float, vy: float):
        direction = None
        if abs(vx) >= abs(vy):
            if vx > 0:
                direction = Direction.EAST
            elif vx < 0:
                direction = Direction.WEST
            else:
                # TODO: Check for up and down
                pass
        elif abs(vx) < abs(vy):
            if vy > 0:
                direction = Direction.SOUTH
            elif vy < 0:
                direction = Direction.NORTH
            else:
                # TODO: Check for left and right
                pass
        return direction

    def to_velocity(direction: Direction) -> Tuple[int, int]:
        vx = vy = 0

        if direction == Direction.SOUTH:
            vy = 1
        elif direction == Direction.EAST:
            vx = 1
        elif direction == Direction.NORTH:
            vy = -1
        elif direction == Direction.WEST:
            vx = -1
        return vx, vy
