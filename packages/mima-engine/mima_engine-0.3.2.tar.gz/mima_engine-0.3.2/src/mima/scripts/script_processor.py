from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List, Optional

from ..types.player import Player
from .command import Command

if TYPE_CHECKING:
    from ..engine import MimaEngine


class ScriptProcessor:
    engine: MimaEngine

    def __init__(self):
        self.commands: Dict[Player : List[Command]] = {}

    def add_command(
        self, cmd: Command, *, players: Optional[List[Player]] = None
    ):
        if players is not None and players:
            cmd.set_players(players)

        for p in cmd.players:
            self.commands.setdefault(p, []).append(cmd)
        # self.commands.append(cmd)

    def process_command(self, elapsed_time: float):
        # for p in Player:
        #     self.engine.trigger_script(False, p)
        #     for cmd in self.commands:
        #         if p in cmd.players or Player.P0 in cmd.players:
        #             self.engine.trigger_script(True, p)
        #             break
        for p in self.commands:
            if self.commands[p]:
                self.engine.trigger_script(True, p)
                if not self.commands[p][0].completed:
                    if not self.commands[p][0].started:
                        self.commands[p][0].start()
                        self.commands[p][0].started = True
                    else:
                        self.commands[p][0].update(elapsed_time)
                else:
                    self.commands[p][0].finalize()
                    self.commands[p].pop(0)
                    self.engine.trigger_script(False, p)
            else:
                self.engine.trigger_script(False, p)

    def complete_command(self, player: Player, force: bool = False):
        if self.commands[player]:
            # for cmd in self.commands:
            #     if player in cmd.players or Player.P0 in cmd.players:

            if self.commands[player][0].can_complete(force):
                self.commands[player][0].completed = True
                return True
            else:
                return False
        return True
