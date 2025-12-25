from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from ..command import Command

if TYPE_CHECKING:
    from ...objects.dynamic import Dynamic


class CommandGiveItem(Command):
    def __init__(self, item_name: str, dynamic: Optional[Dynamic] = None):
        super().__init__()

        self._item_name: str = item_name

        # if dynamic is None:
        #     dynamic = self.engine.player

        self._dynamic: Dynamic = dynamic

    def start(self):
        # if self._dynamic is None:
        #     self._dynamic = self.engine.get_player(self.players[0])
        self.engine.give_item(self._item_name, self.players[0])
        self.completed = True
