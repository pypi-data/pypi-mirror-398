from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict

from ..objects.animated_sprite import AnimatedSprite
from ..types.damage import Damage

if TYPE_CHECKING:
    from .engine import MimaEngine

LOG = logging.getLogger(__name__)


class Database:
    engine: MimaEngine

    def __init__(self):
        self._cache = {}
        self._known_locale = ""
        self._active_sprites = []

    def get_usable_data(self, usable_id) -> Dict[str, Any]:
        if usable_id in self._cache:
            return self._cache[usable_id]

        data = {}
        tpl = self.engine.assets.get_template(usable_id)

        data["usable_id"] = tpl.get_string("usable_id")
        data["name"] = tpl.get_string(f"display_name_{self.engine.rtc.locale}")
        data["description"] = tpl.get_string(f"description_{self.engine.rtc.locale}")
        data["sprite_name"] = tpl.get_string("sprite_name")
        data["dtype"] = Damage[tpl.get_string("dtype", "body").upper()]
        for pid, prop in tpl.properties.items():
            if not pid.startswith("attr_"):
                continue
            _, attr = pid.split("_", 1)
            data[attr] = tpl.get(pid)
        # data["attr_price"] = tpl.get_int("attr_price")
        # data["attr_swing_timer"] = tpl.get_float("attr_swing_timer")
        # data["attr_damage"] = tpl.get_int("attr_damage")
        # data["attr_health_cost"] = tpl.get_int("attr_health_cost")
        # data["attr_magic_cost"] = tpl.get_int("attr_magic_cost")
        # data["attr_stamina_cost"] = tpl.get_int("attr_stamina_cost")
        # data["attr_bomb_cost"] = tpl.get_int("attr_bomb_cost")
        # data["attr_arrow_cost"] = tpl.get_int("attr_arrow_cost")

        self._cache[usable_id] = data
        return data

    def get_object_data(self, object_id) -> Dict[str, Any]:
        return {}

    def get_sprite(self, sprite_id):
        sprite = AnimatedSprite(sprite_id)
        self._active_sprites.append(sprite)
        return sprite
