from __future__ import annotations

from typing import TYPE_CHECKING, List

from ..util.functions import strtobool

if TYPE_CHECKING:
    from ..engine.mima_engine import MimaEngine
    from ..objects.dynamic import Dynamic
    from ..types.nature import Nature
    from ..types.player import Player


class Quest:
    engine: MimaEngine

    def __init__(self):
        self.name: str = "Unnamed Quest"
        self.accepted: bool = False
        self.reward_unlocked: bool = False
        self.reward_received: bool = False
        self.completed: bool = False
        self.state: int = 0

    def on_interaction(self, target: Dynamic, nature: Nature, player: Player):
        return False

    def populate_dynamics(self, dynamics: List[Dynamic], map_name: str):
        return False

    def load_state(self):
        state = self.engine.game_state.load_group("quest", self.name)
        # key = f"quest__{self.name}__"
        self.accepted = state.get("accepted", False)
        self.reward_unlocked = state.get("reward_unlocked", False)
        self.reward_received = state.get("reward_received", False)
        self.completed = state.get("completed", False)
        self.state = state.get("state", 0)

    def save_state(self):
        key = f"quest__{self.name}__"
        self.clean_up()
        self.engine.game_state.save_value(f"{key}accepted", self.accepted)
        self.engine.game_state.save_value(f"{key}completed", self.completed)
        self.engine.game_state.save_value(
            f"{key}reward_received", self.reward_received
        )
        self.engine.game_state.save_value(
            f"{key}reward_unlocked", self.reward_unlocked
        )
        self.engine.game_state.save_value(f"{key}state", self.state)

    def clean_up(self):
        if self.accepted is None or not isinstance(self.accepted, bool):
            self.accepted = False

        if self.completed is None or not isinstance(self.completed, bool):
            self.completed = False

        if self.reward_unlocked is None or not isinstance(
            self.reward_unlocked, bool
        ):
            self.reward_unlocked = False

        if self.reward_received is None or not isinstance(
            self.reward_received, bool
        ):
            self.reward_received = False

        if self.state is None or not isinstance(self.state, int):
            self.state = 0
