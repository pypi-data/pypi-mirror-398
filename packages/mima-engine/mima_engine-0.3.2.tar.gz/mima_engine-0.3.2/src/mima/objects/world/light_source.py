from typing import Optional

from ...maps.tilemap import Tilemap
from ...types.direction import Direction
from ...types.graphic_state import GraphicState
from ...types.nature import Nature
from ...types.object import ObjectType
from ..animated_sprite import AnimatedSprite
from ..dynamic import Dynamic
from ..effects.light import Light
from ..projectile import Projectile


class LightSource(Dynamic):
    def __init__(
        self,
        px: float,
        py: float,
        name: str = "LightSource",
        *,
        sprite_name: str = "",
        tilemap: Optional[Tilemap] = None,
        dyn_id: int = -1,
        graphic_state: GraphicState = GraphicState.ON,
        max_size: int = 32,
    ):
        if graphic_state not in [GraphicState.OFF, GraphicState.ON]:
            msg = (
                f"graphic_state of LightSource {name}{dyn_id} must be either "
                f"'off' or 'on', but it is {graphic_state}"
            )
            raise ValueError(msg)

        super().__init__(
            px,
            py,
            name,
            sprite_name=sprite_name,
            tilemap=tilemap,
            dyn_id=dyn_id,
        )

        self.type = ObjectType.LIGHT_SOURCE
        self.graphic_state = graphic_state
        self._max_size = max_size
        self.active = self.graphic_state == GraphicState.ON
        self._light: Optional[Projectile] = None

        self.hitbox_px = 0.0
        self.hitbox_py = 0.0
        self.hitbox_width = 1.0
        self.hitbox_height = 1.0
        self.solid_vs_dyn = True
        self.solid_vs_map = False
        self._state_changed = True

    def update(self, elapsed_time: float, target: Optional[Dynamic] = None):
        if self._state_changed:
            # self._set_sprite_state()
            self._state_changed = False

        if self.active:
            if self._light is None:
                self._light = Light(self, self._max_size)
                self.engine.get_view().add_effect(
                    self._light, self.tilemap.name
                )
        else:
            if self._light is not None:
                self._light.kill()
                self._light = None

        self.graphic_state = (
            GraphicState.ON if self.active else GraphicState.OFF
        )
        self.sprite.update(
            elapsed_time, self.facing_direction, self.graphic_state
        )

    def on_interaction(self, target: Dynamic, nature: Nature):
        if nature == Nature.SIGNAL:
            self.active = True
            self._state_changed = True
            return True

        if nature == Nature.NO_SIGNAL:
            self.active = False
            self._state_changed = True
            return True

        if nature == Nature.TALK:
            self.active = not self.active
            self._state_changed = True
            return True

    def draw_self(self, ox: float, oy: float, camera_name: str = "display"):
        self.sprite.draw_self(self.px - ox, self.py - oy, camera_name)

    def on_death(self) -> bool:
        self._light.kill()
        return True

    @staticmethod
    def load_from_tiled_object(obj, px, py, width, height, tilemap):
        light = LightSource(
            px=px,
            py=py,
            name=obj.name,
            sprite_name=obj.get_string("sprite_name"),
            tilemap=tilemap,
            dyn_id=obj.object_id,
            graphic_state=GraphicState[
                obj.get_string("graphic_state", "on").upper()
            ],
            max_size=obj.get_int("max_size", 32),
        )

        # light.sprite.width = int(width * LightSource.engine.rtc.tile_width)
        # light.sprite.height = int(height * LightSource.engine.rtc.tile_height)

        return [light]
