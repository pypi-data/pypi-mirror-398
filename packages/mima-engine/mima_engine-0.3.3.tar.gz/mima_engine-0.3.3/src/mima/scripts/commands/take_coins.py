from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from ...scripts.command import Command

if TYPE_CHECKING:
    from ...objects.dynamic import Dynamic


class CommandTakeCoins(Command):
    def __init__(self, amount: int = 0, dynamic: Optional[Dynamic] = None):
        super().__init__()

        if dynamic is None:
            dynamic = self.engine.player

        self._amount: int = amount
        self._dynamic: Dynamic = dynamic

    def start(self):
        self._dynamic.attributes.coins -= self._amount
        self.completed = True
