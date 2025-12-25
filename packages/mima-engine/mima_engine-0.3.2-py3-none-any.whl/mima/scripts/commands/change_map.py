from typing import List, Optional

from ...types.player import Player
from ..command import Command


class CommandChangeMap(Command):
    def __init__(
        self,
        map_name: str,
        spawn_px: float,
        spawn_py,
        players: Optional[List[Player]] = None,
    ):
        if players is None:
            players = [Player.P1]

        super().__init__(players)

        self._map_name: str = map_name
        self._spawn_px: float = spawn_px
        self._spawn_py: float = spawn_py

    def start(self):
        self.engine.get_view().unload_map(self.players[0])
        self.engine.get_view().load_map(
            self._map_name, self._spawn_px, self._spawn_py, self.players[0]
        )
        # self.engine.change_map(self._map_name, self._spawn_px, self._spawn_py)
        self.completed = True

    def finalize(self):
        self.engine.trigger_teleport(False, self.players[0])
        self.engine.trigger_player_collision(False, self.players[0])
