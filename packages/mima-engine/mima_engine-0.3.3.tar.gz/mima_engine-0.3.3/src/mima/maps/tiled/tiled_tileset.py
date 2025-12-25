from __future__ import annotations

import logging
import os
from xml.etree import ElementTree

from ..tileset import Tileset
from .tiled_tile import TiledTile

LOG = logging.getLogger(__name__)


class TiledTileset(Tileset):
    def __init__(self, name: str, filename: str):
        super().__init__()

        self.name = name

        LOG.info(
            "Loading tileset %s from TSX file at '%s' ...",
            name,
            filename,
        )
        tree = ElementTree.parse(filename)
        LOG.debug("Loaded file %s successfully.", filename)

        root = tree.getroot()
        LOG.debug("Loading tileset properties ...")
        self.tile_width: int = int(root.attrib["tilewidth"])
        self.tile_height: int = int(root.attrib["tileheight"])
        self.tile_count: int = int(root.attrib["tilecount"])
        self.columns: int = int(root.attrib["columns"])

        LOG.debug("Loading image properties ...")
        image = root.findall("image")[0]
        self.image_name: str = os.path.split(image.attrib["source"])[-1][:-4]
        self.sprite_width: int = int(image.attrib["width"])
        self.sprite_height: int = int(image.attrib["height"])

        LOG.debug("Loading tiles ...")
        tiles = root.findall("tile")

        for tile in tiles:
            t_obj = TiledTile(tile)
            self.tiles.append(t_obj)
            if t_obj.animated:
                self.animated_tiles.append(t_obj)
            if t_obj.sprite_name:
                self.sprite_names.setdefault(t_obj.sprite_name, []).append(
                    t_obj.tile_id
                )
