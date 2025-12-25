from typing import Optional

from ...maps.tilemap import Tilemap
from ...objects.dynamic import Dynamic
from ...types.direction import Direction
from ...types.graphic_state import GraphicState
from ...types.nature import Nature
from ...types.object import ObjectType
from ...types.terrain import Terrain
from ...usables.item import Item
from ...util.colors import BLACK
from ..animated_sprite import AnimatedSprite
from ..effects.walking_on_grass import WalkingOnGrass
from ..effects.walking_on_water import WalkingOnWater


class Pickup(Dynamic):
    def __init__(
        self,
        px: float,
        py: float,
        item: Item,
        *,
        tilemap: Optional[Tilemap] = None,
        dyn_id=0,
    ):
        super().__init__(
            px,
            py,
            f"Pickup({item.name})",
            sprite_name=item.sprite_name,
            tilemap=tilemap,
            dyn_id=dyn_id,
        )
        self.type: ObjectType = ObjectType.PICKUP
        self.item = item
        # if not sprite_name:
        #     sprite_name = self.item.sprite_name

        self.collected = False
        self.solid_vs_dyn = False
        self.moves_on_collision = True
        # self.sprite = AnimatedSprite(
        #     self.item.tileset_name,
        #     self.item.image_name,
        #     self.item.sprite_name,
        #     graphic_state,
        #     facing_direction,
        # )

    def update(self, elapsed_time: float, target=None):
        if self.collected:
            self.kill()
        else:
            self._handle_terrain(elapsed_time)
            self.sprite.update(
                elapsed_time, self.facing_direction, self.graphic_state
            )

    def on_interaction(self, target: Dynamic, nature: Nature):
        if self.collected:
            return False

        pl = target.get_player()
        if pl.value > 0:
            if self.item.on_interaction(target):
                if self.engine.give_item(self.item, pl):
                    self.collected = True
                    return True
            else:
                self.collected = True

        return False

    def draw_self(
        self,
        ox: float,
        oy: float,
        camera_name: str = "display",
        draw_to_ui: bool = False,
    ):
        if self.collected:
            return

        if self.pz != 0:

            # print("Draw item circle")
            self.engine.backend.fill_circle(
                (self.px - ox + 0.5) * self.sprite.width,
                (self.py - oy + 0.7) * self.sprite.height,
                0.2875 * self.sprite.width,
                BLACK,
                camera_name,
            )
        self.sprite.draw_self(
            self.px - ox,
            self.py - oy - self.pz,
            camera_name,
            draw_to_ui=draw_to_ui,
        )
        # self.engine.backend.draw_partial_sprite(
        #     (self.px - ox) * self.item.sprite_width,
        #     (self.py - oy - self.pz) * self.item.sprite_height,
        #     self.item.sprite_name,
        #     self.item.sprite_ox * self.item.sprite_width,
        #     self.item.sprite_oy * self.item.sprite_height,
        #     self.item.sprite_width,
        #     self.item.sprite_height,
        #     camera_name,
        # )

    def _handle_terrain(self, elapsed_time: float):
        """Method is duplicated."""
        e2rm = []
        for effect in self.effects:
            if isinstance(effect, WalkingOnGrass):
                if self.walking_on == Terrain.DEFAULT:
                    e2rm.append(effect)

        for effect in e2rm:
            self.effects.remove(effect)

        if self.walking_on in [Terrain.GRASS, Terrain.SHALLOW_WATER]:
            # self.attributes.speed_mod = 0.7
            effect_active = False
            for effect in self.effects:
                if isinstance(effect, (WalkingOnGrass, WalkingOnWater)):
                    effect_active = True
                    effect.renew = True
                    break

            if not effect_active:
                if self.walking_on == Terrain.GRASS:
                    eff = WalkingOnGrass(self)
                else:
                    eff = WalkingOnWater(self)
                self.effects.append(eff)
                self.engine.get_view().add_effect(eff, self.tilemap.name)
        # else:
        #     self.attributes.speed_mod = 1.0

    @staticmethod
    def load_from_tiled_object(obj, px, py, width, height, tilemap):
        item = Pickup.engine.get_item(obj.get_string("usable_id"))

        pickup = Pickup(
            px,
            py,
            item,
            tilemap=tilemap,
            dyn_id=obj.object_id,
        )

        # pickup.sprite.width = int(width * Pickup.engine.rtc.tile_width)
        # pickup.sprite.height = int(height * Pickup.engine.rtc.tile_height)

        return [pickup]
