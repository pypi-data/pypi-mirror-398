from dataclasses import dataclass

from .tileset import Tileset


@dataclass
class TilesetInfo:
    tileset: Tileset
    first_gid: int
