from __future__ import annotations

from typing import TYPE_CHECKING

from ...scripts.command import Command

if TYPE_CHECKING:
    from ...objects.dynamic import Dynamic


class CommandMoveTo(Command):
    def __init__(
        self,
        obj: Dynamic,
        target_px: float,
        target_py: float,
        duration: float = 0.0,
    ):
        super().__init__()

        self.obj: Dynamic = obj
        self.start_px: float = 0.0
        self.start_py: float = 0.0
        self.target_px: float = target_px
        self.target_py: float = target_py

        self.duration: float = max(duration, 0.001)
        self.time_so_far: float = 0.0

    def start(self):
        self.start_px = self.obj.px
        self.start_py = self.obj.py

    def update(self, elapsed_time: float):
        self.time_so_far += elapsed_time
        relatime = min(1.0, self.time_so_far / self.duration)

        self.obj.px = (self.target_px - self.start_px) * relatime + self.start_px
        self.obj.py = (self.target_py - self.start_py) * relatime + self.start_py
        self.obj.vx = (self.target_px - self.start_px) / self.duration
        self.obj.vy = (self.target_py - self.start_py) / self.duration

        if self.time_so_far >= self.duration:
            self.completed = True

    def finalize(self):
        self.obj.px = self.target_px
        self.obj.py = self.target_py
        self.obj.vx = self.obj.vy = 0.0
