from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from ...types.direction import Direction
from ..command import Command

if TYPE_CHECKING:
    from ...objects.dynamic import Dynamic


class CommandSetFacingDirection(Command):
    def __init__(self, dynamic: Dynamic, facing_direction: Direction):
        super().__init__()

        self._dynamic: Dynamic = dynamic
        self._new_direction: Direction = facing_direction

    def start(self):
        self._dynamic.facing_direction = self._new_direction
        self.completed = True