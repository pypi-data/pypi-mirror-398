import logging
from typing import List, Optional, Union

from ...types.player import Player
from ..command import Command

LOG = logging.getLogger(__name__)


class CommandSerial(Command):
    START_AND_UPDATE: int = 0
    START_WITHOUT_UPDATE: int = 1

    def __init__(
        self,
        cmds: List[Command],
        update_when: Union[int, List[int]] = START_AND_UPDATE,
        players: Optional[List[Player]] = None,
    ):
        super().__init__(players)
        self._cmds: List[Command] = cmds

        self._current: int = 0
        self._update_when: List[int]
        if not isinstance(update_when, list):
            self._update_when = [
                update_when for _ in range(len(self._cmds) - 1)
            ]
        else:
            self._update_when = update_when

        if len(self._update_when) + 1 < len(self._cmds):
            LOG.warning(
                "Unsufficient information for 'update_when' of serial command:"
                f"cmds={self._cmds}, update_when={self._update_when}. Using "
                "default value!"
            )

    def start(self):
        self._cmds[self._current].start()

    def update(self, delta_time):
        if not self._cmds[self._current].completed:
            # Not completed -> Update current command
            self._cmds[self._current].update(delta_time)
        else:
            # Current command completed -> progress to next
            self._current += 1
            if self._current == len(self._cmds):
                # Reached end? -> Finish serial command
                self.completed = True
            else:
                # End not reached -> call start of next command
                self._cmds[self._current].start()
                if (
                    self._update_when[self._current - 1]
                    == self.START_AND_UPDATE
                ):
                    # Start the command already with update
                    self._cmds[self._current].update(delta_time)

    def finalize(self):
        for cmd in self._cmds:
            cmd.finalize()

    def set_players(self, players: List[Player]):
        self.players = players
        for cmd in self._cmds:
            cmd.set_players(players)
