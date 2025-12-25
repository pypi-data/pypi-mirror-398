from __future__ import annotations

from typing import TYPE_CHECKING

from ..command import Command

if TYPE_CHECKING:
    from ...states.quest import Quest


class CommandAddQuest(Command):
    def __init__(self, quest: Quest):
        super().__init__()

        self._quest: Quest = quest

    def start(self):
        self.engine.add_quest(self._quest)
        self.completed = True
