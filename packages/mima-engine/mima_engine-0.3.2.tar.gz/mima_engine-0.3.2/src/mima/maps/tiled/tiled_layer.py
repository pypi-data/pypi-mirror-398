from __future__ import annotations

import csv
from io import StringIO
from typing import TYPE_CHECKING, List

from ..tile_layer import TileLayer

if TYPE_CHECKING:
    from xml.etree.ElementTree import Element


class TiledLayer(TileLayer):
    def __init__(self, l_xtree: Element):
        super().__init__()

        self.name: str = l_xtree.attrib["name"]
        self.layer_id: int = int(l_xtree.attrib["id"])
        self.type: str = l_xtree.attrib.get("class", "NormalLayer")
        if "Foreground" in self.type:
            # FIXME: Hack, propertytypes.json should be read and applied
            self.layer_pos = 1
        self.width: int = int(l_xtree.attrib["width"])
        self.height: int = int(l_xtree.attrib["height"])
        self.indices: List[int] = []

        layer_data = l_xtree.findall("data")[0]
        reader = csv.reader(StringIO(layer_data.text), delimiter=",")

        for row in reader:
            if len(row) <= 0:
                continue

            for entry in row:
                try:
                    self.indices.append(int(entry))
                except ValueError:
                    pass  # Empty string

        property_data = l_xtree.findall("properties")
        for pdata in property_data:
            properties = pdata.findall("property")

            for prop in properties:
                if prop.attrib["name"] == "layer":
                    self.layer_pos = int(prop.attrib["value"])
                if prop.attrib["name"] == "speed":
                    self.speed_x = float(prop.attrib.get("value", 0.0))
