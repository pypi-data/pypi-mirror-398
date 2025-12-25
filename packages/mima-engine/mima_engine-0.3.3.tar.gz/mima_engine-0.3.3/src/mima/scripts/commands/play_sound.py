from ..command import Command


class CommandPlaySound(Command):
    def __init__(self, sound: str, delay: float = 0.0):
        super().__init__()

        self._sound_to_play: str = sound
        self._delay: float = delay

    def start(self):
        self.engine.audio.play_sound(self._sound_to_play, self._delay)
        self.completed = True
