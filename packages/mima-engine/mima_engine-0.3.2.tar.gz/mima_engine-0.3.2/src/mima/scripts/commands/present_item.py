from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from ...objects.projectile import Projectile
from ...scripts.command import Command
from ...types.graphic_state import GraphicState

if TYPE_CHECKING:
    from ...objects.dynamic import Dynamic


class CommandPresentItem(Command):
    def __init__(self, item_name: str, dynamic: Optional[Dynamic] = None):
        super().__init__()

        self._dynamic: Optional[Dynamic] = dynamic
        self._item_name: str = item_name
        self._item_sprite: Optional[Projectile] = None

    def start(self):
        if self._dynamic is None:
            self._dynamic = self.engine.get_player(self.players[0])
        item = self.engine.get_item(self._item_name)
        self._item_sprite = Projectile(
            self._dynamic.px,
            self._dynamic.py - 1,
            f"Present {item.name}",
            sprite_name=item.sprite_name,
            tilemap=self._dynamic.tilemap,
            duration=3600,
            alignment=self._dynamic.alignment,
        )
        self._item_sprite.layer = 2
        # self._item_sprite.sprite.name = item.sprite_name
        # self._item_sprite.sprite.ox = item.sprite_ox
        # self._item_sprite.sprite.oy = item.sprite_oy
        # self._item_sprite.sprite.width = item.sprite_width
        # self._item_sprite.sprite.height = item.sprite_height
        self._item_sprite.solid_vs_dyn = False
        self._item_sprite.solid_vs_map = False
        self._item_sprite.one_hit = False
        self._item_sprite.damage = 0

        self.engine.get_view().add_projectile(
            self._item_sprite, self._dynamic.tilemap.name
        )
        self._dynamic.lock_graphic_state(GraphicState.CELEBRATING)
        self.completed = True

    def finalize(self):
        self._item_sprite.kill()
        self._dynamic.unlock_graphic_state()
