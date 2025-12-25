from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from ..types.player import Player

if TYPE_CHECKING:
    from ..engine import MimaEngine


class Command:
    engine: MimaEngine

    def __init__(self, players: Optional[List[Player]] = None):
        self.started: bool = False
        self.completed: bool = False
        self.uninterruptible: bool = False
        self.players: List[Player] = (
            players if (players is not None and players) else [Player.P0]
        )

    def start(self):
        pass

    def update(self, elapsed_time: float):
        pass

    def can_complete(self, force: bool = False) -> bool:
        if self.uninterruptible and not force:
            return False

        return True

    def finalize(self):
        pass

    def set_players(self, players: List[Player]):
        self.players = players
