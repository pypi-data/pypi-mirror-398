import math
from typing import List


class TileLayer:
    def __init__(self):
        self.name: str = "Unnamed Layer"
        self.layer_id: int = 0
        self.width: int = 0
        self.height: int = 0
        self.layer_pos: int = 0
        self.speed_x: float = 0.0
        self.speed_y: float = 0.0
        self.layer_ox: float = 0.0
        self.layer_oy: float = 0.0
        self.parallax_x: float = 0.0  # Not used yet
        self.parallax_y: float = 0.0  # Not used yet

        self.indices: List[int] = []

    def update(self, elapsed_time: float):
        self.layer_ox += self.speed_x * elapsed_time
        self.layer_oy += self.speed_y * elapsed_time

        if self.layer_ox > self.width:
            self.layer_ox -= self.width
        if self.layer_ox < 0:
            self.layer_ox += self.width
        if self.layer_oy > self.height:
            self.layer_oy -= self.height
        if self.layer_oy < 0:
            self.layer_oy += self.height

    def get_index(self, px: float, py: float) -> int:
        if self.layer_ox != 0.0:
            px = math.floor(px - self.layer_ox)
            if px > self.width:
                px -= self.width
            while px < 0:
                px += self.width

        if self.layer_oy != 0.0:
            py = math.floor(py - self.layer_oy)
            if py > self.height:
                py -= self.height
            while py < 0:
                py += self.height

        if 0 <= px < self.width and 0 <= py < self.height:
            return self.indices[py * self.width + px]
        else:
            return 0
