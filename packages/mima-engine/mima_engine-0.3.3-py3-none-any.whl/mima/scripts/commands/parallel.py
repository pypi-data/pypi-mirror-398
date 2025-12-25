from typing import List, Optional

from ...types.player import Player
from ..command import Command


class CommandParallel(Command):
    ALL_COMPLETED: int = 0
    ANY_COMPLETED: int = 1
    FIRST_COMPLETED: int = 2

    def __init__(
        self,
        cmds: List[Command],
        completed_when: int = ALL_COMPLETED,
        players: Optional[List[Player]] = None,
    ):
        super().__init__()
        self._cmds: List[Command] = cmds
        self._completed_when: int = completed_when

    def start(self):
        for cmd in self._cmds:
            cmd.start()

    def update(self, delta_time):
        for cmd in self._cmds:
            cmd.update(delta_time)

        if self._completed_when == self.ALL_COMPLETED:
            self._check_for_all()
        elif self._completed_when == self.ANY_COMPLETED:
            self._check_for_any()
        elif self._completed_when == self.FIRST_COMPLETED:
            self._check_for_first()
        else:
            raise ValueError(
                f"Unknown value {self._completed_when} for "
                "attribute _completed_when"
            )

    def finalize(self):
        for cmd in self._cmds:
            cmd.finalize()

    def _check_for_all(self):
        completed = True
        for cmd in self._cmds:
            completed = completed and cmd.completed

        self.completed = completed

    def _check_for_any(self):
        completed = False
        for cmd in self._cmds:
            completed = completed or cmd.completed

        self.completed = completed

    def _check_for_first(self):
        self.completed = self._cmds[0].completed

    def set_players(self, players: List[Player]):
        self.players = players
        for cmd in self._cmds:
            cmd.set_players(players)
