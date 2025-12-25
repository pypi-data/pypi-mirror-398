from typing import Optional

import pygame

from ..types.blend import Blend
from ..util.colors import BLACK, WHITE, Color, ALPHA


class PygameCamera:
    def __init__(self, width: int, height: int):
        self.px: int = 0
        self.py: int = 0
        self.render_width = width
        self.render_height = height
        self.view: pygame.Surface = pygame.Surface((width, height))
        self.filter: pygame.Surface = pygame.Surface((width, height))
        self.ui: pygame.Surface = pygame.Surface((width, height))
        self._filter_color: Color = BLACK
        self._filter_blend: Blend = Blend.DEFAULT
        self._ui_color: Color = ALPHA
        self.camera_scale: float = 1.0

    def clear(self, color: Color = BLACK):
        self.view.fill(color.getRGBA())
        self.filter.fill(self._filter_color.getRGBA())
        self.ui.fill(self._ui_color.getRGBA())
        self.ui.set_colorkey(self._ui_color.getRGBA())

    def configure_filter(
        self, color: Color = BLACK, blend_mode: Blend = Blend.DEFAULT
    ):
        self._filter_color = color
        self._filter_blend = blend_mode

    def apply_filter(self):
        if self._filter_blend != Blend.DEFAULT:
            self.view.blit(
                self.filter,
                pygame.Vector2(0, 0),
                special_flags=blend_to_pygame_flag(self._filter_blend),
            )

    def change_zoom(self, width, height):
        self.view = pygame.Surface((width, height))
        self.filter = pygame.Surface((width, height))

    def change_ui_zoom(self, width, height):
        self.ui = pygame.Surface((width, height), flags=pygame.SRCALPHA)
        self.ui.convert_alpha()
        self.ui.set_colorkey(ALPHA.getRGBA())


def blend_to_pygame_flag(blend_mode: Blend):
    if blend_mode == Blend.DEFAULT:
        return 0
    elif blend_mode == Blend.ADD:
        return pygame.BLEND_RGBA_ADD
    elif blend_mode == Blend.SUB:
        return pygame.BLEND_RGBA_SUB
    elif blend_mode == Blend.MULT:
        return pygame.BLEND_RGBA_MULT
    else:
        return 0
