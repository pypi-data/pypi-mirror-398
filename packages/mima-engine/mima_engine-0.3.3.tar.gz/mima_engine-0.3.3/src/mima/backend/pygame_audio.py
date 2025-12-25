from __future__ import annotations

import logging
from typing import TYPE_CHECKING, List, Tuple

import pygame

if TYPE_CHECKING:
    from .pygame_assets import PygameAssets

LOG = logging.getLogger(__name__)


class PygameAudio:
    def __init__(self, assets: PygameAssets):
        self.assets = assets
        self.current_track: str = ""
        self.is_playing: bool = False
        self.sound_schedule: List[Tuple[float, str]] = []
        self._time_so_far: float = 0.0

    def update(self, elapsed_time: float):
        self._time_so_far += elapsed_time

        sounds_to_remove = []
        for sound_tuple in self.sound_schedule:
            if self._time_so_far >= sound_tuple[0]:
                self._play_sound(sound_tuple[1])
                sounds_to_remove.append(sound_tuple)

        for sound in sounds_to_remove:
            self.sound_schedule.remove(sound)

        if self._time_so_far >= 10.0:
            self._time_so_far -= 10.0
            for idx in range(len(self.sound_schedule)):
                self.sound_schedule[idx] = (
                    self.sound_schedule[idx][0] - 10.0,
                    self.sound_schedule[idx][1],
                )

    def play_music(self, name: str, repeat: int = -1):
        if self.is_playing and name == self.current_track:
            return

        else:
            try:
                self._play_music(name)
                self.current_track = name
                self.is_playing = True
            except Exception:
                LOG.exception(f"Could not load {name}.")

    def _play_music(self, name: str, repeat: int = -1):
        pygame.mixer.music.load(self.assets.get_music(name))
        pygame.mixer.music.play(repeat)

    def _play_sound(self, name: str):
        snd = self.assets.get_sound(name)
        snd.set_volume(100)
        snd.play()

    def stop(self):
        if self.is_playing:
            pygame.mixer.music.pause()
            self.is_playing = False

    def stop_sound(self, sound_to_stop: str):
        self.assets.get_sound(sound_to_stop).set_volume(0)

    def set_music_volume(self, vol: float):
        pygame.mixer.music.set_volume(vol)

    def set_sound_volume(self, vol: float):
        pass

    def play_sound(self, sound_to_play: str, delay: float = 0.0):
        self.sound_schedule.append((self._time_so_far + delay, sound_to_play))
