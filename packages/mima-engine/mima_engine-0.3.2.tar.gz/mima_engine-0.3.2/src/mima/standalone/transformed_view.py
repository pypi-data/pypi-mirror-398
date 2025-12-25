import logging
import math
from typing import TypeAlias, Union

import pygame
from pygame import Event, Surface, Vector2

LOG = logging.getLogger(__name__)
Color: TypeAlias = Union[tuple[int, int, int], tuple[int, int, int, int]]
Cache: TypeAlias = dict[
    tuple[int, tuple[int, int, int, int], float, float], tuple[Surface, int]
]
Point: TypeAlias = Union[Vector2, tuple[float, float]]
Area: TypeAlias = tuple[Point, Point]


class TransformedView:
    """TransformedView inspired by olc PixelGameEngine."""

    def __init__(
        self,
        screen: Surface,
        view_area: Vector2,
        pixel_size: Vector2 | None = None,
        world_scale: float = 1.0,
    ) -> None:
        self._screen: Surface = screen

        self._pos: Vector2 = Vector2(0, 0)
        self._view_area: Vector2 = Vector2(view_area)
        self._world_offset: Vector2 = Vector2(0.0, 0.0)
        self._pixel_scale: Vector2 = (
            Vector2(1.0, 1.0) if pixel_size is None else pixel_size
        )
        self._world_scale: Vector2 = Vector2(world_scale, world_scale)

        self._recip_pixel_scale: Vector2 = Vector2(
            1.0 / self._pixel_scale.x, 1.0 / self._pixel_scale.y
        )
        self._start_pan: Vector2 = Vector2(0.0, 0.0)
        self._scale_max: Vector2 = Vector2(0.0, 0.0)
        self._scale_min: Vector2 = Vector2(0.0, 0.0)

        self._steps = 0.1
        self._mouse_button = 2
        self._is_panning: bool = False
        self._clamp_zoom: bool = False
        self._cache: dict = {}
        self._cache_surfaces: bool = False
        self._memory_usage: int = 0

    def enable_caching(self, enable: bool) -> None:
        self._cache_surfaces = enable

    def set_pos(self, pos: Vector2) -> None:
        self._pos = pos

    def get_pos(self) -> Vector2:
        return self._pos

    def set_view_area(self, area: Vector2) -> None:
        self._view_area = area

    def get_view_area(self) -> Vector2:
        return self._view_area

    def set_world_offset(self, offset: Vector2) -> None:
        self._world_offset = offset

    def move_world_offset(self, delta_offset: Vector2) -> None:
        self._world_offset += delta_offset

    def set_world_scale(self, scale: Vector2) -> None:
        if scale.x == 0 or scale.y == 0:
            return
        self._world_scale = scale
        if self._clamp_zoom:
            self._world_scale = clamp(
                self._world_scale, self._scale_min, self._scale_max
            )

    def get_world_tl(self) -> Vector2:
        return self.screen_to_world(Vector2(0, 0))

    def get_world_br(self) -> Vector2:
        return self.screen_to_world(self._view_area)

    def get_world_visible_area(self) -> Vector2:
        return self.get_world_br() - self.get_world_tl()

    def set_scale_extents(self, scale_min: Vector2, scale_max: Vector2) -> None:
        self._scale_max = scale_max
        self._scale_min = scale_min

    def enable_scale_clamp(self, enable: bool) -> None:
        self._clamp_zoom = enable

    def zoom_at_screen_pos(self, delta_zoom: float, pos: Vector2) -> None:
        offset_before_zoom = self.screen_to_world(pos)
        self._world_scale *= delta_zoom
        if self._clamp_zoom:
            self._world_scale = clamp(
                self._world_scale, self._scale_min, self._scale_max
            )
        offset_after_zoom = self.screen_to_world(pos)
        # msg = (
        #     f"Pos: {pos} OBZ: {offset_before_zoom} OAZ: {offset_after_zoom} "
        #     f"OFF: {self._world_offset} -- "
        # )
        self._world_offset += offset_before_zoom - offset_after_zoom
        # msg += f"{self._world_offset}"
        # print(msg)

    def start_pan(self, pos: Vector2):
        self._is_panning = True
        self._start_pan = Vector2(pos)

    def update_pan(self, pos: Vector2):
        if self._is_panning:
            delta = pos - self._start_pan
            delta.x /= self._world_scale.x
            delta.y /= self._world_scale.y
            self._world_offset -= delta
            self._start_pan = pos

    def end_pan(self, pos: Vector2):
        self.update_pan(pos)
        self._is_panning = False

    def get_world_offset(self) -> Vector2:
        return self._world_offset

    def get_world_scale(self) -> Vector2:
        return self._world_scale

    def world_to_screen(self, world_pos: Vector2) -> Vector2:
        return (world_pos - self._world_offset).elementwise() * self._world_scale

    def screen_to_world(self, screen_pos: Vector2) -> Vector2:
        return self._world_offset + screen_pos.elementwise() / self._world_scale

    def scale_to_world(self, screen_size: Vector2) -> Vector2:
        return Vector2(
            screen_size.x / self._world_scale.x, screen_size.y / self._world_scale.y
        )

    def handle_pan_and_zoom(
        self,
        mouse_button: int = 2,
        zoom_rate: float = 0.1,
        pan: bool = True,
        zoom: bool = True,
        events: list[Event] | None = None,
    ) -> list[Event]:
        if events is None:
            events = []
        if not events:
            for event in pygame.event.get():
                events.append(event)

        for event in events:
            if zoom and event.type == pygame.MOUSEWHEEL:
                if event.y == 1:
                    self.zoom_at_screen_pos(
                        1.0 + zoom_rate, Vector2(pygame.mouse.get_pos())
                    )
                if event.y == -1:
                    self.zoom_at_screen_pos(
                        1.0 - zoom_rate, Vector2(pygame.mouse.get_pos())
                    )
            if pan and event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == mouse_button:
                    self.start_pan(event.pos)
            if pan and event.type == pygame.MOUSEBUTTONUP:
                if event.button == mouse_button:
                    self.end_pan(event.pos)

        self.update_pan(Vector2(pygame.mouse.get_pos()))

        return events

    def is_rect_visible(self, pos: Vector2, size: Vector2) -> bool:
        screen_pos = self.world_to_screen(pos)
        screen_size = (size.x * self._world_scale.x, size.y * self._world_scale.y)

        return (
            screen_pos.x < self._view_area.x
            and screen_pos.x + screen_size[0] > 0
            and screen_pos.y < self._view_area.y
            and screen_pos.y + screen_size[1] > 0
        )

    def clear(self, color: Color) -> None:
        pygame.draw.rect(self._screen, color, (self._world_offset, self._view_area))

    def draw(
        self, pos: Vector2, color: tuple[int, int, int] | tuple[int, int, int, int]
    ) -> None:
        pos = self.world_to_screen(pos)
        self._screen.set_at(pos, color)

    def draw_line(
        self, pos1: Vector2, pos2: Vector2, color: Color | None = None, width: int = 1
    ) -> None:
        if color is None:
            color = (255, 255, 255)

        pygame.draw.line(
            surface=self._screen,
            color=color,
            start_pos=(self.world_to_screen(pos1) + self._pos).elementwise()
            * self._pixel_scale,
            end_pos=(self.world_to_screen(pos2) + self._pos).elementwise()
            * self._pixel_scale,
            width=width,
        )

    def draw_circle(
        self,
        pos: Vector2,
        radius: float,
        color: Color | None = None,
        *,
        width: int = 1,
        draw_top_left: bool = False,
        draw_top_right: bool = False,
        draw_bottom_left: bool = False,
        draw_bottom_right: bool = False,
    ) -> None:
        if color is None:
            color = (255, 255, 255)

        pygame.draw.circle(
            surface=self._screen,
            color=color,
            center=(self.world_to_screen(pos) + self._pos).elementwise()
            * self._pixel_scale,
            radius=radius * self._world_scale.x * self._pixel_scale.x,
            width=width,
            draw_top_left=draw_top_left,
            draw_top_right=draw_top_right,
            draw_bottom_left=draw_bottom_left,
            draw_bottom_right=draw_bottom_right,
        )

    def fill_circle(
        self,
        pos: Vector2,
        radius: float,
        color: Color | None = None,
        *,
        draw_top_left: bool = False,
        draw_top_right: bool = False,
        draw_bottom_left: bool = False,
        draw_bottom_right: bool = False,
    ) -> None:
        self.draw_circle(
            pos=pos,
            radius=radius,
            color=color,
            width=0,
            draw_top_left=draw_top_left,
            draw_top_right=draw_top_right,
            draw_bottom_left=draw_bottom_left,
            draw_bottom_right=draw_bottom_right,
        )

    def draw_rect(
        self,
        pos: Vector2,
        size: Vector2,
        color: Color | None = None,
        *,
        width: int = 1,
        border_top_left_radius: int = -1,
        border_top_right_radius: int = -1,
        border_bottom_left_radius: int = -1,
        border_bottom_right_radius: int = -1,
    ) -> None:
        if color is None:
            color = (255, 255, 255)
        pygame.draw.rect(
            surface=self._screen,
            color=color,
            rect=(
                (self.world_to_screen(pos) + self._pos).elementwise()
                * self._pixel_scale.elementwise(),
                (
                    size.elementwise()
                    * self._world_scale.elementwise()
                    * self._pixel_scale.elementwise()
                ),
            ),
            width=width,
            border_top_left_radius=border_top_left_radius,
            border_top_right_radius=border_top_right_radius,
            border_bottom_left_radius=border_bottom_left_radius,
            border_bottom_right_radius=border_bottom_right_radius,
        )

    def fill_rect(
        self,
        pos: Vector2,
        size: Vector2,
        color: Color | None = None,
        *,
        border_top_left_radius: int = -1,
        border_top_right_radius: int = -1,
        border_bottom_left_radius: int = -1,
        border_bottom_right_radius: int = -1,
    ) -> None:
        self.draw_rect(
            pos=pos,
            size=size,
            color=color,
            width=0,
            border_top_left_radius=border_top_left_radius,
            border_top_right_radius=border_top_right_radius,
            border_bottom_left_radius=border_bottom_left_radius,
            border_bottom_right_radius=border_bottom_right_radius,
        )

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
    ) -> None:
        src_size = src_size if src_size is not None else Vector2(surf.get_size())

        if not self.is_rect_visible(pos, src_size * scale):
            return

        scaling_factor = scale * (
            self._world_scale.elementwise()
            # * self._recip_pixel_scale.elementwise()
            # * src_size.elementwise()
        )
        dest = self.world_to_screen(pos)

        area = None
        if src_pos is not None:
            area = (int(src_pos.x), int(src_pos.y), int(src_size.x), int(src_size.y))

        abs_pos = vfloor((dest + self._pos).elementwise() * self._pixel_scale)
        if scaling_factor.x == 1.0 and scaling_factor.y == 0.0 and angle == 0.0:
            self._screen.blit(surf, abs_pos, area, special_flags)
            return

        src = surf.subsurface(area) if area is not None else surf
        cache_key = (surf, area, scaling_factor.x, scaling_factor.y, angle)
        if cache_key in self._cache:
            src = self._cache[cache_key]
        else:
            if angle != 0.0:
                src = pygame.transform.rotate(src, angle)
            if scaling_factor.x != 0.0 or scaling_factor.y != 0.0:
                src = pygame.transform.scale(
                    src,
                    (
                        int(src.get_width() * scaling_factor.x),
                        int(src.get_height() * scaling_factor.y),
                    ),
                )
            if self._cache_surfaces or cache:
                self._cache[cache_key] = src
                self._memory_usage += src.get_width() * src.get_height() * 4
                LOG.debug(
                    "Loaded %s to cache. Cache memory usage: %.2f MB ",
                    cache_key,
                    (self._memory_usage / 2**20),
                )

        # transformed = pygame.transform.rotozoom(src, angle, scaling_factor.x)
        self._screen.blit(src, abs_pos, special_flags=special_flags)


class TileTransformedView(TransformedView):
    def get_tl_tile(self) -> Vector2:
        res = vfloor(self.screen_to_world(Vector2(0, 0)), inplace=True)
        return res

    def get_br_tile(self) -> Vector2:
        res = vceil(
            self.screen_to_world(self._view_area.elementwise() / self._pixel_scale),
            inplace=True,
        )
        return res

    def get_visible_tiles(self) -> Vector2:
        return self.get_br_tile() - self.get_tl_tile()

    def get_tile_under_screen_pos(self, pos: Vector2) -> Vector2:
        return vfloor(self.screen_to_world(pos))

    def get_tile_offset(self) -> Vector2:
        return Vector2(
            int(
                (self._world_offset.x - math.floor(self._world_offset.x))
                * self._world_scale.x
            ),
            int(
                (self._world_offset.y - math.floor(self._world_offset.y))
                * self._world_scale.y
            ),
        )


def clamp(val: Vector2, low: Vector2, high: Vector2) -> Vector2:
    return Vector2(max(low.x, min(high.x, val.x), max(low.y, min(high.y, val.y))))


def vfloor(vec: Vector2, inplace: bool = False) -> Vector2:
    if inplace:
        vec.x = math.floor(vec.x)
        vec.y = math.floor(vec.y)
        return vec
    return Vector2(math.floor(vec.x), math.floor(vec.y))


def vceil(vec: Vector2, inplace: bool = False) -> Vector2:
    if inplace:
        vec.x = math.ceil(vec.x)
        vec.y = math.ceil(vec.y)
        return vec
    return Vector2(math.ceil(vec.x), math.ceil(vec.y))
