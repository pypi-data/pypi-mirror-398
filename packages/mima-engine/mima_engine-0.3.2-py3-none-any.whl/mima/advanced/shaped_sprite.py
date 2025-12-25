from typing import Any, Generic

from pygame import Vector2

from mima.advanced.shape import ShapeCollection
from mima.standalone.geometry import shape_from_dict
from mima.standalone.sprite import GS, AnimatedSprite, D


class SpriteWithShape(AnimatedSprite[GS, D], Generic[GS, D]):
    def __init__(self) -> None:
        super().__init__()

        self.hitbox: ShapeCollection | None = None
        self.shapes: dict[tuple[GS, D, int], ShapeCollection] = {}

    def add_frame(
        self, graphic_state: GS, direction: D, frame_data: dict[str, Any]
    ) -> None:
        super().add_frame(graphic_state, direction, frame_data)

        sprite_data = self.sprites[graphic_state][direction]
        for i, hb in enumerate(sprite_data.hitboxes):
            shapes = []
            for s in hb:
                shapes.append(shape_from_dict(s))

            if not shapes:
                continue

            sc = ShapeCollection(Vector2(), *shapes)

            self.shapes[(graphic_state, direction, i)] = sc
            if self.hitbox is None:
                self.hitbox = sc

    def update(self, elapsed_time: float, graphic_state: GS, direction: D) -> bool:
        if self._last_graphic_state is None:
            self._last_graphic_state = graphic_state
        if self._last_direction is None:
            self._last_direction = direction
        if not self.sprites:
            return False

        data = self.sprites[graphic_state][direction]
        update_vals = True
        if (
            graphic_state == self._last_graphic_state
            and direction == self._last_direction
        ):
            self._timer -= elapsed_time
            if self._timer <= 0.0:
                self._frame = (self._frame + 1) % data.n_frames()
                self._timer += data.duration[self._frame]
            else:
                update_vals = False

        else:
            # Something changed
            self._frame = 0
            self._timer = data.duration[self._frame]

        if update_vals:
            self._src_pos = data.offset[self._frame]
            self._src_size = data.size[self._frame]
            self._image = data.image[self._frame]
            new_hitbox = self.shapes.get((graphic_state, direction, self._frame))
            self.hitbox = new_hitbox if new_hitbox is not None else self.hitbox

        self._last_graphic_state = graphic_state
        self._last_direction = direction

        return update_vals
