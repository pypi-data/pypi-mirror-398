from typing import Protocol

from pygame import BLEND_RGBA_MIN, Surface, Vector2

TRANSPARENT_COLOR = (254, 252, 253)


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
        special_flags: int = 0,
    ) -> None: ...


class PixelFont:
    def __init__(self, image: Surface, font_size: tuple[int, int]):
        self._image = image
        self._font_size = font_size

        self._colorized: dict[tuple[int, int, int, int], Surface] = {
            (255, 255, 255, 255): self._image
        }

    def draw_text(
        self,
        pos: Vector2,
        text: str,
        display: Renderer | Surface,
        color: tuple[int, int, int, int] | None = None,
    ):
        if color is None:
            color = (255, 255, 255, 255)
        font = self._colorized.get(color)
        if font is None:
            font = self._image.copy()
            font.fill(color, special_flags=BLEND_RGBA_MIN)
            self._colorized[color] = font

        surf = Surface((len(text) * self._font_size[0], self._font_size[1]))
        surf.fill(TRANSPARENT_COLOR)
        for i, c in enumerate(text):
            sx = ((ord(c) - 32) % 16) * self._font_size[0]
            sy = ((ord(c) - 32) // 16) * self._font_size[1]
            surf.blit(font, (i * self._font_size[0], 0), ((sx, sy), self._font_size))
        surf.set_colorkey(TRANSPARENT_COLOR)
        if isinstance(display, Surface):
            display.blit(surf, pos)
        else:
            display.draw_surface(pos, surf)

    @property
    def width(self) -> int:
        return self._font_size[0]

    @property
    def height(self) -> int:
        return self._font_size[1]
