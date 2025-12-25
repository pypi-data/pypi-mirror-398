from ...scripts.command import Command


class CommandSetSavePosition(Command):
    def __init__(self, map_name: str, px: float, py: float):
        self._map_name = map_name
        self._px = px
        self._py = py

    def start(self):

        self.engine.memory.player_state[self.players[0]].save_map = (
            self._map_name
        )
        self.engine.memory.player_state[self.players[0]].save_px = self._px
        self.engine.memory.player_state[self.players[0]].save_py = self._py
        self.completed = True
