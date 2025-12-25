from __future__ import annotations

from typing import TYPE_CHECKING

from ..types.alignment import Alignment
from ..types.damage import Damage
from ..types.object import ObjectType
from .dynamic import Dynamic

if TYPE_CHECKING:
    from ..maps.tilemap import Tilemap


class Projectile(Dynamic):
    def __init__(
        self,
        px: float,
        py: float,
        name: str = "Projectile",
        *,
        sprite_name: str = "",
        tilemap: Tilemap = None,
        dyn_id: int = 1000,
        vx: float = 0.0,
        vy: float = 0.0,
        duration: float,
        alignment: Alignment,
    ):
        super().__init__(
            px,
            py,
            name,
            sprite_name=sprite_name,
            tilemap=tilemap,
            dyn_id=dyn_id,
        )

        self.type = ObjectType.PROJECTILE
        self.vx = vx
        self.vy = vy
        self.pz = 0.5
        self.duration = duration
        self.alignment = alignment

        self.solid_vs_dyn = False
        self.solid_vs_map = True
        self.is_projectile = True  # redundant
        self.attackable = False
        self.one_hit = False
        self.inherit_pos = False
        self.gravity = False
        self.moves_on_collision = True
        self.change_solid_vs_map_timer = 0
        self.dtype = Damage.BODY
        self.damage = 0

    def update(self, elapsed_time: float, target: Dynamic = None):
        self.duration -= elapsed_time
        if self.duration <= 0.0:
            self.kill()

        if self.change_solid_vs_map_timer > 0:
            self.change_solid_vs_map_timer -= elapsed_time
            if self.change_solid_vs_map_timer <= 0:
                self.solid_vs_map = not self.solid_vs_map
                self.change_solid_vs_map_timer = 0

        self.speed = self.attributes.speed
        # if "body" not in self.name:
        #     print(self.name, self.pz)
        self.sprite.update(
            elapsed_time, self.facing_direction, self.graphic_state
        )

    def draw_self(self, ox: float, oy: float, camera_name: str = "display"):
        if (
            self.sprite.name is None
            or self.sprite.name == ""
            or self.redundant
        ):
            return

        self.sprite.draw_self(self.px - ox, self.py - oy, camera_name)

    def on_death(self) -> bool:
        if self.spawn_on_death:
            for do in self.spawn_on_death:
                if do.type == ObjectType.PROJECTILE:
                    if self.inherit_pos:
                        do.px = self.px
                        do.py = self.py
                    self.engine.get_view().add_projectile(
                        do, self.tilemap.name
                    )
                else:
                    self.engine.get_view().add_dynamic(do, self.tilemap.name)

        return False

    def cancel(self):
        if self.spawn_on_death:
            for do in self.spawn_on_death:
                if do.type == ObjectType.PROJECTILE:
                    do.cancel()  # Projectile will kill itself
                else:
                    do.kill()
        self.kill()
        return True

    def __str__(self):
        return f"P({self.name}, {self.dyn_id})"
