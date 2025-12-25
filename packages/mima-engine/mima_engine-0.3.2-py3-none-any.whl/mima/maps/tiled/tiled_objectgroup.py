from __future__ import annotations

from typing import TYPE_CHECKING, List

from .tiled_object import TiledObject

if TYPE_CHECKING:
    from xml.etree.ElementTree import Element


class TiledObjectgroup:
    def __init__(self, o_xtree: Element):
        self.name: str = o_xtree.attrib["name"]
        self.layer_id: int = int(o_xtree.attrib["id"])

        self._objects: List[TiledObject] = []

        objects = o_xtree.findall("object")

        for obj in objects:
            self._objects.append(TiledObject(obj))

    @property
    def objects(self):
        return self._objects