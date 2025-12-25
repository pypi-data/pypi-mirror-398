from typing import Optional

from ...objects.effects.colorize_screen import ColorizeScreen
from ...util.colors import BLACK, Color
from ..command import Command


class CommandScreenFade(Command):
    def __init__(
        self,
        duration: float = 0.5,
        color: Optional[Color] = None,
        fadein: bool = False,
        map_name: Optional[str] = None,
    ):
        super().__init__()

        self.duration: float = duration
        if color is None:
            color = self.engine.rtc.color_black

        self.color: Color = color
        self.fadein: bool = fadein
        self.time_so_far: float = 0.0
        self._start: int = 0
        self._end: int = 255
        self._iter: int = 15

        if fadein:
            self._start = 255
            self._end = 0
            self._iter = -self._iter

        self._map_name = map_name

        self._effect: Optional[ColorizeScreen] = None
        # self.duration -= 0.1

    def start(self):

        self._effect = ColorizeScreen(
            cameras=[
                self.engine.get_view().get_camera_name(p) for p in self.players
            ]
        )
        self._effect.alpha = self._start
        if self._map_name is None:
            map_names = list(
                set(
                    [
                        self.engine.get_player(p).tilemap.name
                        for p in self.players
                    ]
                )
            )
            for map_name in map_names:
                self.engine.get_view().add_effect(self._effect, map_name)
        else:
            self.engine.get_view().add_effect(self._effect, self._map_name)
        for p in self.players:
            self.engine.get_player(p).halt()

    def update(self, elapsed_time: float):
        self.time_so_far += elapsed_time

        progress = self.time_so_far / self.duration

        alpha = progress * 256
        if self.fadein:
            alpha = 255 - alpha

        self._effect.alpha = min(255, max(0, alpha))

        for p in self.players:
            self.engine.get_player(p).halt()

        if self.time_so_far >= self.duration:
            self._effect.alpha = self._end
            self.completed = True

    def finalize(self):
        self.completed = True
        self._effect.kill()
