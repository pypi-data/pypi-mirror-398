from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict

from ..util.constants import DEFAULT_SPRITE_HEIGHT, DEFAULT_SPRITE_WIDTH

if TYPE_CHECKING:
    from ..engine import MimaEngine
    from ..objects.creature import Creature
    from ..objects.dynamic import Dynamic


class Item:
    engine: MimaEngine

    def __init__(self):
        self.name: str = ""
        self.description: str = ""
        self.sprite_name: str = ""
        # self.sprite_ox: int = 0
        # self.sprite_oy: int = 0
        # self.sprite_width: int = DEFAULT_SPRITE_WIDTH
        # self.sprite_height: int = DEFAULT_SPRITE_HEIGHT
        self.key_item: bool = False
        self.equipable: bool = False
        self.price: int = 0
        self.stackable: bool = False
        self.stackable_by_merchant: bool = False

    def init(self, data: Dict[str, Any]):

        for key, val in data.items():
            setattr(self, key, val)
        # self.usable_id = data["usable_id"]
        # self.name = data["name"]
        # self.description = data["description"]
        # self.price = data.get("attr_price", 0)
        # self.sprite_name = data.get("sprite_name")

    def on_interaction(self, obj: Dynamic):
        return False

    def on_use(self, obj: Creature):
        return False

    def __str__(self):
        txt = f"{type(self).__name__}({self.name})"
        return txt

    def __repr__(self):
        return str(self)
