from typing import List

from ...scripts.command import Command
from ...types.keys import Key as K
from ...types.player import Player


class CommandShowChoices(Command):
    def __init__(
        self,
        options: List[str],
        replies: List[Command],
        default_option: int = 0,
    ):
        super().__init__()

        self.uninterruptible = True
        self._options: List[str] = options
        self._replies: List[Command] = replies
        self._default_option: int = default_option

        self._cursor_pos: int = 0

    def update(self, elapsed_time: float):
        if self.engine.keys.new_key_release(K.UP, self.players[0]):
            self._cursor_pos = (self._cursor_pos - 1) % len(self._options)
        elif self.engine.keys.new_key_release(K.DOWN, self.players[0]):
            self._cursor_pos = (self._cursor_pos + 1) % len(self._options)
        elif self.engine.keys.new_key_press(K.A, self.players[0]):
            self.completed = True
        elif self.engine.keys.new_key_release(K.B, self.players[0]):
            self._cursor_pos = self._default_option
            self.completed = True

        lines = []
        for idx, opt in enumerate(self._options):
            if idx == self._cursor_pos:
                lines.append(f"> {opt}")
            else:
                lines.append(f"  {opt}")
        # for p in self.players:
        self.engine.get_view().show_dialog(lines, self.players[0])

    def finalize(self):
        self.engine.script.add_command(
            self._replies[self._cursor_pos], players=self.players
        )

    def set_players(self, players: List[Player]):
        for cmd in self._replies:
            cmd.set_players(players)
        self.players = players
