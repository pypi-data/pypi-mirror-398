from __future__ import annotations

import logging
import os
from typing import List
from xml.etree import ElementTree

from ...util.property import Property
from ..tilemap import Tilemap
from ..tileset_info import TilesetInfo
from .tiled_layer import TiledLayer
from .tiled_objectgroup import TiledObjectgroup

# if TYPE_CHECKING:
#     from ..engine import Avare


LOG = logging.getLogger(__name__)


class TiledMap(Tilemap):
    def __init__(self, name: str, filename: str = ""):
        super().__init__(name)

        if filename == "":
            filename = f"{name}.tmx"

        if not os.path.isfile(filename):
            filename = os.path.join(
                self.engine.backend.data_path,
                "maps",
                os.path.split(filename)[-1],
            )

        self._objects: List[TiledObjectgroup] = []

        if not os.path.isfile(filename):
            filename = os.path.join(
                self.engine.backend.data_path, "maps", filename
            )

        LOG.info("Loading map %s from TMX file '%s' ...", name, filename)
        tree = ElementTree.parse(filename)
        LOG.debug("Loaded file %s successfully.", filename)
        root = tree.getroot()

        LOG.debug("Loading map properties ...")
        self.width = int(root.attrib["width"])
        self.height = int(root.attrib["height"])
        self.tile_width = int(root.attrib["tilewidth"])
        self.tile_height = int(root.attrib["tileheight"])

        LOG.debug("Loading properties ...")
        properties = root.findall("properties")
        if properties:
            properties = properties[0].findall("property")
            for p in properties:
                pname = p.attrib["name"]
                self.properties[pname] = Property(
                    name=pname,
                    dtype=p.attrib.get("type", "str"),
                    value=p.attrib["value"],
                )

        LOG.debug("Loading tilesets ...")
        tilesets = root.findall("tileset")  # Only one tileset
        for tileset in tilesets:
            tname = os.path.split(tileset.attrib["source"])[-1][:-4]
            first_gid = int(tileset.attrib["firstgid"])
            self._tilesets.append(
                TilesetInfo(
                    tileset=self.engine.assets.get_tileset(tname),
                    first_gid=first_gid,
                )
            )

        LOG.debug("Loading layers ...")
        layers = root.findall("layer")
        for layer in layers:
            self._layers.append(TiledLayer(layer))

        LOG.debug("Loading objects ...")
        objectgroups = root.findall("objectgroup")
        for objectgroup in objectgroups:
            self._objects.append(TiledObjectgroup(objectgroup))

        LOG.info("Map %s successfully loaded.", self.name)

    @property
    def objects(self):
        all_objects = []
        for group in self._objects:
            all_objects += group.objects

        return all_objects
