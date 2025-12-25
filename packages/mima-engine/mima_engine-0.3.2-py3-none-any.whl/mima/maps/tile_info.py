from dataclasses import dataclass

from .tile import Tile
from .tileset import Tileset


@dataclass
class TileInfo:
    tileset: Tileset
    tile: Tile
