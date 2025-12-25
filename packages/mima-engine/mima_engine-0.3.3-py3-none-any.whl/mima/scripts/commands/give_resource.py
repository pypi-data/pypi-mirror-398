from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Optional

from ..command import Command

if TYPE_CHECKING:
    from ...objects.dynamic import Dynamic


class CommandGiveResource(Command):
    def __init__(self, dynamic: Optional[Dynamic] = None, **resources: Dict[str, int]):
        super().__init__()

        if dynamic is None:
            dynamic = self.engine.player

        self._dynamic: Dynamic = dynamic
        self._health: int = resources.get("health", 0)
        self._magic: int = resources.get("magic", 0)
        self._stamina: int = resources.get("stamina", 0)
        self._arrows: int = resources.get("arrows", 0)
        self._bombs: int = resources.get("bombs", 0)
        self._coins: int = resources.get("coins", 0)
        self._keys: int = resources.get("keys", 0)

    def start(self):
        self._dynamic.attributes.health = min(
            self._dynamic.attributes.health + self._health,
            self._dynamic.attributes.health_max,
        )
        self._dynamic.attributes.magic = min(
            self._dynamic.attributes.magic + self._magic,
            self._dynamic.attributes.magic_max,
        )
        self._dynamic.attributes.stamina = min(
            self._dynamic.attributes.stamina + self._stamina,
            self._dynamic.attributes.stamina_max,
        )
        self._dynamic.attributes.arrows = min(
            self._dynamic.attributes.arrows + self._arrows,
            self._dynamic.attributes.arrows_max,
        )
        self._dynamic.attributes.bombs = min(
            self._dynamic.attributes.bombs + self._bombs,
            self._dynamic.attributes.bombs_max,
        )
        self._dynamic.attributes.coins += self._coins
        self._dynamic.attributes.keys += self._keys

        self.completed = True
