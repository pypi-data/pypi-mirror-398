from __future__ import annotations

import os
from typing import TYPE_CHECKING

from ...util.property import Property
from ..template import Template

if TYPE_CHECKING:
    from xml.etree.ElementTree import Element

    from .tiled_template import TiledTemplate
    from .tiled_tileset import TiledTileset


class TiledObject(Template):
    def __init__(self, o_xtree: Element):
        super().__init__("TiledObject")
        self.object_id: int = int(o_xtree.attrib["id"])

        self.name: str = o_xtree.attrib.get("name", "Unnamed")
        self.type: str = o_xtree.attrib.get(
            "type", o_xtree.attrib.get("class", "Untyped")
        )
        self.px: float = float(o_xtree.attrib["x"])
        self.py: float = float(o_xtree.attrib["y"])

        tsource = o_xtree.attrib.get("template", None)
        if tsource is not None:
            tname = os.path.split(tsource)[-1].split(".")[0]
            tpl: TiledTemplate = self.engine.assets.get_template(tname)

            self.name = tpl.oname
            self.type = tpl.otype
            self.width = tpl.width
            self.height = tpl.height
            # Templates' y positions are bottom instead of top
            self.py -= self.height

            for key, prop in tpl.properties.items():
                self.properties[key] = Property(
                    name=prop.name, dtype=prop.dtype, value=prop.value
                )

            ts: TiledTileset = self.engine.assets.get_tileset(tpl.tileset_name)
            self.properties["tileset_name"] = Property(
                name="tileset_name", dtype="str", value=tpl.tileset_name
            )
            self.properties["image_name"] = Property(
                name="image_name", dtype="str", value=""
            )
            self.properties["sprite_offset_x"] = Property(
                name="sprite_offset_x",
                dtype="int",
                value=f"{(tpl.gid - tpl.first_gid) % ts.columns}",
            )

            self.properties["sprite_offset_y"] = Property(
                name="sprite_offset_y",
                dtype="int",
                value=f"{(tpl.gid - tpl.first_gid) // ts.columns}",
            )
        else:
            self.width = float(o_xtree.attrib["width"])
            self.height = float(o_xtree.attrib["height"])

        if self.type == "container":
            self.engine.total_chests += 1
        props = o_xtree.findall("properties")
        if props:
            props = props[0].findall("property")

            for p in props:
                pname = p.attrib["name"]
                self.properties[pname] = Property(
                    name=pname,
                    dtype=p.attrib.get("type", "str"),
                    value=p.attrib["value"],
                )
