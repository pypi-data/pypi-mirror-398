from typing import Dict, List

from .tile import Tile


class Tileset:
    def __init__(self):
        self.name: str = "Unnamed Tileset"
        self.image_name: str = ""
        # self.filename: str = ""
        self.image_width: int = 0
        self.image_height: int = 0
        self.tile_width: int = 0
        self.tile_height: int = 0
        self.tile_count: int = 0
        self.columns: int = 0

        self.tiles: List[Tile] = []
        self.animated_tiles: List[Tile] = []
        self.sprite_names: Dict[str, List[int]] = {}
        self._is_new_frame: bool = False

    def update(self, elapsed_time: float) -> bool:
        if self._is_new_frame:
            for tile in self.animated_tiles:
                tile.update(elapsed_time)
            self._is_new_frame = False

        return True

    def get_tile(self, tile_id: int) -> Tile:
        for tile in self.tiles:
            if tile.basic_tile_id == tile_id:
                return tile

        return self.tiles[0]

    def trigger_new_frame(self):
        self._is_new_frame = True
