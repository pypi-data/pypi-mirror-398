import logging
import os
from xml.etree import ElementTree

from ...util.property import Property
from ..template import Template

LOG = logging.getLogger(__name__)


class TiledTemplate(Template):
    def __init__(self, name: str, filename: str):
        super().__init__(name)

        LOG.info(
            "Loading template %s from TX file at '%s' ...",
            name,
            filename,
        )

        tree = ElementTree.parse(filename)
        LOG.debug("Loaded file %s successfully.", filename)

        root = tree.getroot()
        tileset = root.findall("tileset")[0]
        LOG.debug("Loading tileset properties ...")
        self.first_gid = int(tileset.attrib["firstgid"])
        self.tileset_name = os.path.split(tileset.attrib["source"])[-1].split(
            "."
        )[0]

        obj = root.findall("object")[0]
        self.oname = obj.attrib.get("name", "Unnamed")
        self.otype = obj.attrib.get("type", obj.attrib.get("class", "Untyped"))
        self.gid = int(obj.attrib["gid"])
        self.width = int(obj.attrib["width"])
        self.height = int(obj.attrib["height"])

        props = obj.findall("properties")
        if props:
            props = props[0].findall("property")

            for p in props:
                pname = p.attrib["name"]
                self.properties[pname] = Property(
                    name=pname,
                    dtype=p.attrib.get("type", "str"),
                    value=p.attrib["value"],
                )
