from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from ...types.alignment import Alignment
from ..projectile import Projectile

if TYPE_CHECKING:
    from ...maps.tilemap import Tilemap
    from ..sprite import Sprite


class ShowSprite(Projectile):
    def __init__(
        self,
        px: float,
        py: float,
        name: str = "ShowSprite",
        *,
        sprite_name: str = "",
        tilemap: Optional[Tilemap] = None,
        dyn_id: int = 0,
        layer: int = 0,
    ):
        super().__init__(
            px,
            py,
            name,
            sprite_name=sprite_name,
            tilemap=tilemap,
            dyn_id=dyn_id,
            vx=0.0,
            vy=0.0,
            duration=0.0,
            alignment=Alignment.NEUTRAL,
        )

        self.layer = layer
        self.draw_to_ui: bool = False

    def update(self, elapsed_time: float):
        self.sprite.update(
            elapsed_time, self.facing_direction, self.graphic_state
        )

    def draw_self(self, ox: float, oy: float, camera_name: str):
        if self.sprite is None:
            return

        self.sprite.draw_self(self.px - ox, self.py - oy, camera_name)
