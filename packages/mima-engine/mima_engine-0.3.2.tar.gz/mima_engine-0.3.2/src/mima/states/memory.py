from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List

from ..types.player import Player

if TYPE_CHECKING:
    from ..objects.creature import Creature
    from ..usables.item import Item
    from .quest import Quest


class Memory:
    def __init__(self):
        self.player: Dict[Player, Creature] = {}
        self.items: Dict[str, Any] = {}
        self.quests: List[Quest] = []
        self.teleport_active: Dict[Player, bool] = {p: False for p in Player}
        self.dialog_active: Dict[Player, bool] = {p: False for p in Player}
        self.script_active: Dict[Player, bool] = {p: False for p in Player}
        self.player_collision_active: Dict[Player, bool] = {
            p: False for p in Player
        }
        self.bag: Dict[Player, List[Item]] = {p: [] for p in Player}
        self.map_name: Dict[Player, str] = {}

        self.last_spawn_px: Dict[Player, float] = {p: 0.0 for p in Player}
        self.last_spawn_py: Dict[Player, float] = {p: 0.0 for p in Player}
