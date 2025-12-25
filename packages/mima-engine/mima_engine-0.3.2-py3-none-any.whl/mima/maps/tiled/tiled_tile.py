from __future__ import annotations

from typing import TYPE_CHECKING, List

from ...types.direction import Direction
from ...types.graphic_state import GraphicState
from ...types.terrain import Terrain
from ...util.functions import strtobool
from ..tile import Tile
from ..tile_animation import TileAnimation

if TYPE_CHECKING:
    from xml.etree.ElementTree import Element


class TiledTile(Tile):
    def __init__(self, t_xtree: Element):
        super().__init__()

        self.tile_type: str = t_xtree.attrib.get(
            "class", t_xtree.attrib.get("type", "tile")
        )

        self.basic_tile_id: int = int(t_xtree.attrib["id"])
        self.tile_id: int = self.basic_tile_id

        self._frames: List[TileAnimation] = []
        self._frame: int = 0
        self._num_frames: int = 0
        self._frame_timer: float = 0.0

        animation = t_xtree.findall("animation")

        if animation:
            frames = animation[0].findall("frame")
            for frame in frames:
                self._frames.append(
                    TileAnimation(
                        frame_id=int(frame.attrib["tileid"]),
                        duration=int(frame.attrib["duration"]) / 1000.0,
                    )
                )
            self.animated = True
        else:
            self._frames.append(
                TileAnimation(frame_id=self.basic_tile_id, duration=0.0)
            )

        self._num_frames = len(self._frames)

        self.tile_id = self._frames[0].frame_id
        self._frame_timer = self._frames[0].duration

        properties = t_xtree.findall("properties")
        if properties:
            properties = properties[0].findall("property")
            for prop in properties:
                if prop.attrib["name"] == "solid":
                    self.solid = strtobool(prop.attrib["value"])
                if prop.attrib["name"] == "ground_type":
                    try:
                        self.terrain = Terrain[prop.attrib["value"].upper()]
                    except:
                        self.terrain = Terrain.DEFAULT
                if prop.attrib["name"] == "z_height":
                    self.z_height = float(prop.attrib["value"])
                if prop.attrib["name"] == "facing_direction":
                    self.facing_direction = Direction[
                        prop.attrib.get("value", "south").upper()
                    ]
                if prop.attrib["name"] == "graphic_state":
                    self.graphic_state = GraphicState[
                        prop.attrib.get("value", "standing").upper()
                    ]
                if prop.attrib["name"] == "sprite_name":
                    self.sprite_name = prop.attrib.get("value", "")

    def update(self, elapsed_time: float) -> bool:
        if self._num_frames <= 1:
            return False

        self._frame_timer -= elapsed_time
        if self._frame_timer <= 0:
            self._frame = (self._frame + 1) % self._num_frames
            self.tile_id = self._frames[self._frame].frame_id
            self._frame_timer += self._frames[self._frame].duration

            return True

        return False
