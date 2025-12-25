from collections import defaultdict
from enum import Enum
from typing import Any, Generic, Protocol, TypeVar

import pygame
from pygame import Surface, Vector2

GS = TypeVar("GS", bound=Enum)
D = TypeVar("D", bound=Enum)


class Renderer(Protocol):
    def draw_surface(
        self,
        pos: Vector2,
        surf: Surface,
        *,
        src_pos: Vector2 | None = None,
        src_size: Vector2 | None = None,
        scale: float = 1.0,
        angle: float = 0,
        cache: bool = False,
        special_flags: int = 0,
    ) -> None: ...


class SpriteData:
    def __init__(self) -> None:
        self.duration: list[float] = []
        self.offset: list[Vector2] = []
        self.image: list[Surface] = []
        self.size: list[Vector2] = []
        self.frame_id: list[int] = []
        self.hitboxes: list[list[dict]] = []

    def n_frames(self) -> int:
        return len(self.duration)


class SpriteSet(Generic[D]):
    def __init__(self) -> None:
        self.data: dict[D, SpriteData] = {}

    def __getitem__(self, direction: D) -> SpriteData:
        return self.data[direction]


class AnimatedSprite(Generic[GS, D]):
    def __init__(self) -> None:
        self._last_graphic_state: GS | None = None
        self._last_direction: D | None = None

        self.sprites: dict[GS, SpriteSet] = {}
        self._timer: float = 0.0
        self._frame: int = -1
        self._src_pos: Vector2 = Vector2()
        self._src_size: Vector2 = Vector2()
        self._image: Surface | None = None
        self._scaled_image: Surface | None = None
        self._scale: float = 1.0
        self._scaled_size: tuple[int, int] = (0, 0)

    def update(self, elapsed_time: float, graphic_state: GS, direction: D) -> bool:
        if self._last_graphic_state is None:
            self._last_graphic_state = graphic_state
        if self._last_direction is None:
            self._last_direction = direction

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
            # self._scale_image()

        self._last_graphic_state = graphic_state
        self._last_direction = direction

        return update_vals

    def draw(self, pos: Vector2, ttv: Renderer, cache: bool = False) -> None:
        if self._image is None:
            return

        ttv.draw_surface(
            pos,
            self._image,
            src_pos=self._src_pos,
            src_size=self._src_size,
            scale=self._scale,
            cache=cache,
        )

    def reset(self) -> None:
        self._frame = -1
        self._timer = 0.0

    def __getitem__(self, graphic_state: GS) -> SpriteSet:
        return self.sprites[graphic_state]

    def add_frame(
        self, graphic_state: GS, direction: D, frame_data: dict[str, Any]
    ) -> None:
        sprite_set = self.sprites.setdefault(graphic_state, SpriteSet())
        sprite_data = sprite_set.data.setdefault(direction, SpriteData())
        sprite_data.duration.append(frame_data["duration"])
        sprite_data.offset.append(Vector2(frame_data["offset"]))
        sprite_data.size.append(Vector2(frame_data["size"]))
        sprite_data.image.append(frame_data["image"])
        sprite_data.frame_id.append(frame_data["frame_id"])
        hitboxes = frame_data.get("collision", [])
        sprite_data.hitboxes.append(hitboxes)

    def set_scale(self, scale: float) -> None:
        self._scale = scale
        # self._scale_image()

    def get_size(self) -> Vector2:
        if self._src_size is not None:
            return self._src_size * self._scale
        return Vector2()

    # def _scale_image(self) -> None:
    #     if self._image is None:
    #         self._scaled_image = None
    #         self._scaled_size = (0, 0)
    #         return
    #     if self._scale == 1.0:
    #         self._scaled_image = self._image
    #         self._scaled_size = self._image.get_size()
    #         return
    #     self._scaled_size = (
    #         int((size := self._image.get_size())[0] * self._scale),
    #         int(size[1] * self._scale),
    #     )
    #     self._scaled_image = pygame.transform.scale(self._image, self._scaled_size)
