from __future__ import annotations

import math
from typing import TYPE_CHECKING

from ...scripts.command import Command
from ...util.constants import ONEWAY_SPEED_BOOST

if TYPE_CHECKING:
    from ...objects.dynamic import Dynamic
    from ...types.player import Player


class CommandOnewayMove(Command):
    def __init__(self, obj: Dynamic, vx: float, vy: float, player: Player):
        super().__init__([player])

        self.obj: Dynamic = obj
        self.vx: float = vx
        self.vy: float = vy
        self.start_px: float = 0.0
        self.start_py: float = 0.0
        self.target_px: float = 0.0
        self.target_py: float = 0.0
        self.distance: float = 0.0

    def start(self):
        self.obj.solid_vs_map = False
        self.obj.solid_vs_dyn = False
        self.obj.vx = self.obj.vy = 0.0
        self.obj.vz = 7.5

        self.start_px = self.obj.px
        self.start_py = self.obj.py
        self.target_px = self.obj.px + self.vx
        self.target_py = self.obj.py + self.vy

        dx = self.target_px - self.start_px
        dy = self.target_py - self.start_py
        self.distance = math.sqrt(dx * dx + dy * dy)

    def update(self, elapsed_time):
        self.obj.px += self.vx * elapsed_time * ONEWAY_SPEED_BOOST
        self.obj.py += self.vy * elapsed_time * ONEWAY_SPEED_BOOST

        dx = self.obj.px - self.start_px
        dy = self.obj.py - self.start_py
        distance = math.sqrt(dx * dx + dy * dy)

        if distance >= self.distance:
            self.completed = True

    def finalize(self):
        self.obj.px = self.target_px
        self.obj.py = self.target_py
        self.obj.vx = self.obj.vy = 0.0
        self.obj.solid_vs_dyn = True
        self.obj.solid_vs_map = True
