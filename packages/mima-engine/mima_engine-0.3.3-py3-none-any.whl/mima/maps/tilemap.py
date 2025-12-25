from __future__ import annotations

import logging
import math
from typing import TYPE_CHECKING, Dict, List, Optional

from ..types.tile_collision import TileCollision
from .template import Template
from .tile_info import TileInfo
from .tile_layer import TileLayer
from .tileset_info import TilesetInfo

if TYPE_CHECKING:
    from ..objects.dynamic import Dynamic
    from ..types.nature import Nature
    from .tile import Tile


LOG = logging.getLogger(__name__)


class Tilemap(Template):
    def __init__(self, name: str):
        super().__init__(name)
        self.width: int = 0
        self.height: int = 0
        self.tile_width = self.engine.rtc.tile_width
        self.tile_height = self.engine.rtc.tile_height

        self._layers: List[TileLayer] = []
        self._tilesets: List[TilesetInfo] = []
        self._cache: Dict[int, TileInfo] = {}
        self._objects: List[Template] = []

    def populate_dynamics(self, dynamics: List[Dynamic]) -> bool:
        """Load all map-related objects into the game."""
        return False

    def update(self, elapsed_time: float) -> bool:
        for info in self._tilesets:
            info.tileset.update(elapsed_time)

        for layer in self._layers:
            layer.update(elapsed_time)

        return True

    def draw_self(
        self,
        ox: float,
        oy: float,
        visible_tiles_sx: int,
        visible_tiles_sy: int,
        visible_tiles_ex: int,
        visible_tiles_ey: int,
        layer_pos: int = 0,
        camera_name: str = "display",
    ):
        # Get offsets for smooth movement
        tile_ox = (ox - math.floor(ox)) * self.tile_width
        tile_oy = (oy - math.floor(oy)) * self.tile_height

        for layer in self._layers:
            if layer.layer_pos != layer_pos:
                continue

            layer_ox = (layer.layer_ox - math.floor(layer.layer_ox)) * self.tile_width
            layer_oy = (layer.layer_oy - math.floor(layer.layer_oy)) * self.tile_height

            layer_visible_tiles_sx = int(visible_tiles_sx)
            layer_visible_tiles_sy = int(visible_tiles_sy)

            if layer.speed_x != 0.0:
                layer_visible_tiles_sx -= 1
            if layer.speed_y != 0.0:
                layer_visible_tiles_sy -= 1

            # Draw visible tiles of the map
            for x in range(layer_visible_tiles_sx, int(visible_tiles_ex) + 2):
                for y in range(layer_visible_tiles_sy, int(visible_tiles_ey) + 2):
                    tile_index = layer.get_index(
                        int(x + math.floor(ox)), int(y + math.floor(oy))
                    )
                    if tile_index <= 0:
                        # Zero means the tile was not set in Tiled
                        continue

                    if tile_index not in self._cache:
                        if not self._load_to_cache(tile_index):
                            continue

                    info = self._cache[tile_index]

                    sx = info.tile.tile_id % info.tileset.columns
                    sy = info.tile.tile_id // info.tileset.columns

                    self.engine.backend.draw_partial_sprite(
                        math.floor(x * self.tile_width - tile_ox + layer_ox),
                        math.floor(y * self.tile_height - tile_oy + layer_oy),
                        info.tileset.image_name,
                        sx * self.tile_width,
                        sy * self.tile_height,
                        self.tile_width,
                        self.tile_height,
                        camera_name,
                    )
        return True

    def on_interaction(self, target: Dynamic, nature: Nature) -> bool:
        return False

    def is_solid(
        self,
        px: int,
        py: int,
        layer_pos: Optional[int] = None,
        collision: TileCollision = TileCollision.TOP,
    ) -> bool:
        if collision in (TileCollision.TOP, TileCollision.BOTTOM):
            tile = self.get_tile(
                px,
                py,
                layer_pos,
                ascending=(collision == TileCollision.BOTTOM),
            )

            if tile is not None and tile.solid:
                return True
            return False

        tiles = self.get_tiles(px, py, layer_pos)
        if collision in (TileCollision.TOP_2, TileCollision.TOP_3):
            tiles = tiles[::-1]

        for idx, tile in enumerate(self.get_tiles(px, py, layer_pos)):
            if tile.solid:
                return True
            if idx == 1 and collision in (
                TileCollision.TOP_2,
                TileCollision.BOTTOM_2,
            ):
                break
            elif idx == 2 and collision in (
                TileCollision.TOP_3,
                TileCollision.BOTTOM_3,
            ):
                break
        return False

    def get_tile(
        self,
        px: int,
        py: int,
        layer_pos: Optional[int] = None,
        ascending=False,
    ) -> Optional[Tile]:
        if ascending:
            layers = self._layers
        else:
            layers = self._layers[::-1]

        for layer in layers:
            if layer_pos is not None and layer_pos != layer.layer_pos:
                continue
            tile_index = layer.get_index(math.floor(px), math.floor(py))
            if tile_index not in self._cache:
                if not self._load_to_cache(tile_index):
                    continue

            info = self._cache[tile_index]
            if info.tile is not None:
                return info.tile

        return None

    def get_tiles(self, px: int, py: int, layer_pos: Optional[int] = None):
        tiles = []
        for layer in self._layers:
            if layer_pos is not None and layer_pos != layer.layer_pos:
                continue
            tile_index = layer.get_index(math.floor(px), math.floor(py))
            if tile_index not in self._cache:
                if not self._load_to_cache(tile_index):
                    continue
            info = self._cache[tile_index]
            if info.tile is not None:
                tiles.append(info.tile)

        return tiles

    def _load_to_cache(self, tile_index: int) -> bool:
        tileset = None
        firstgid = 0
        for tsinfo in self._tilesets:
            if tile_index < tsinfo.first_gid:
                break

            firstgid = tsinfo.first_gid
            tileset = tsinfo.tileset

        if tileset is None:
            return False

        tidx = tile_index - firstgid
        tile = tileset.get_tile(tidx)

        self._cache[tile_index] = TileInfo(tileset=tileset, tile=tile)
        return True

    def trigger_new_frame(self):
        for tsinfo in self._tilesets:
            tsinfo.tileset.trigger_new_frame()

    @property
    def objects(self) -> List[Template]:
        return []
