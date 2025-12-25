from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from ...scripts.command import Command
from ...util.constants import DIALOG_CHARS_PER_LINE, DIALOG_N_LINES
from ...util.functions import wrap_text

if TYPE_CHECKING:
    from ...types.player import Player


class CommandShowDialog(Command):
    def __init__(
        self,
        lines: List[str],
        *,
        no_auto_wrap: bool = False,
        chars_per_line: int = DIALOG_CHARS_PER_LINE,
        n_lines: int = DIALOG_N_LINES,
    ):
        super().__init__()

        self.lines: List[str] = lines
        self._current_lines: List[str] = []
        self._no_auto_wrap: bool = no_auto_wrap
        self._chars_per_line: int = chars_per_line
        self._n_lines: int = n_lines
        self._row: int = 0
        self._char: int = 0
        self._first_row: int = 0
        self._last_row: int = self._n_lines

        self._timer_reset = 0.01
        self._timer = self._timer_reset
        self._auto_scroll: bool = True
        self._progress: bool = False
        self._lines_changed: bool = True

    def start(self):
        if not self._no_auto_wrap:
            one_liner = ""
            for line in self.lines:
                one_liner += f"{line.strip()} "

            self.lines = wrap_text(one_liner, self._chars_per_line)
        self._current_lines = [self.lines[0][0]]
        self._char += 1
        for p in self.players:
            self.engine.get_view().show_dialog(self._current_lines, p)

    def update(self, elapsed_time: float):
        if self._auto_scroll:
            self._timer -= elapsed_time
            if self._timer <= 0.0:
                self._timer += self._timer_reset

                self._current_lines = []
                for r in range(self._first_row, self._last_row):
                    if r < self._row:
                        self._current_lines.append(self.lines[r])
                        continue

                    line = ""

                    for c in range(self._char + 1):
                        if c + 1 >= self._char or c + 1 >= len(self.lines[r]):
                            break
                        line += self.lines[r][c]

                    self._current_lines.append(line)

                    if r + 1 >= self._row:
                        break

                self._char += 1
                if self._char >= self._chars_per_line or self._char >= len(
                    self.lines[r]
                ):
                    self._char = 0
                    self._row += 1

                if self._row >= self._n_lines + self._first_row:
                    self._first_row += 1
                    self._last_row += 1
                if self._row >= len(self.lines):
                    self._auto_scroll = False

                # print(f"'{self._current_lines}'")
                for p in self.players:
                    self.engine.get_view().show_dialog(self._current_lines, p)
        else:
            if self._lines_changed:
                self._current_lines = []
                for r in range(self._first_row, self._last_row):
                    if r >= len(self.lines):
                        break
                    self._current_lines.append(self.lines[r])
                for p in self.players:
                    self.engine.get_view().show_dialog(self._current_lines, p)
                self._lines_changed = False

            if self._progress:
                self._first_row += self._n_lines
                self._last_row += self._n_lines
                self._progress = False
                self._lines_changed = True

    def can_complete(self, force: bool = False) -> bool:
        if force:
            return True
        if self._auto_scroll:
            self._auto_scroll = False
        elif self._last_row >= len(self.lines):
            return True
        else:
            self._progress = True
        return False
