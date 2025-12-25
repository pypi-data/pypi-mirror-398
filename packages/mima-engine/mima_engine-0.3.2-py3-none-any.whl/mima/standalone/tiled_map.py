from __future__ import annotations

import csv
import logging
import math
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from typing import Any, Protocol, Self, TypeAlias, overload
from xml.etree import ElementTree
from xml.etree.ElementTree import Element

import pygame
from pygame import Surface, Vector2

LOG = logging.getLogger(__name__)

Property: TypeAlias = str | int | float | bool
TileCache: TypeAlias = dict[tuple[int, tuple[int, int]], tuple[int, int]]
CollisionBoxType: TypeAlias = dict[str, str | float | Vector2]
TileAnimationType: TypeAlias = dict[
    str, int | float | tuple[int, int] | Surface | list[CollisionBoxType]
]
VZERO = Vector2()


@dataclass
class _CollisionBox:
    shape: str
    pos: Vector2
    radius: float
    size: Vector2

    def as_dict(self) -> CollisionBoxType:
        return {
            "shape": self.shape,
            "pos": self.pos,
            "size": self.size,
            "radius": self.radius,
        }


@dataclass
class _TileAnimation:
    frame_id: int
    duration: float
    offset: tuple[int, int]
    size: tuple[int, int]
    image: Surface
    collision_boxes: list[_CollisionBox]

    def as_dict(self) -> TileAnimationType:
        return {
            "frame_id": self.frame_id,
            "duration": self.duration,
            "offset": self.offset,
            "size": self.size,
            "image": self.image,
            "collision": [cb.as_dict() for cb in self.collision_boxes],
        }


@dataclass
class _TilesetInfo:
    tileset: TiledTileset
    first_gid: int


@dataclass
class _TileInfo:
    tileset: TiledTileset
    tile: TiledTile


class Renderer(Protocol):
    def draw_surface(
        self,
        pos: Vector2,
        surf: Surface,
        *,
        src_pos: Vector2 | None = None,
        src_size: Vector2 | None = None,
        scale: float = 1.0,
        angle: float = 0,
        cache: bool = False,
        special_flags: int = 0,
    ) -> None: ...

    def get_tl_tile(self) -> Vector2: ...

    def get_br_tile(self) -> Vector2: ...


class _TiledBase:
    def __init__(self, mapman: MapManager, name: str = "Unnamed Object") -> None:
        self.mapman = mapman
        self.name = name
        self.props: dict[str, Property] = {}

    @overload
    def get(self, key: str, default: bool) -> bool: ...
    @overload
    def get(self, key: str, default: str) -> str: ...
    @overload
    def get(self, key: str, default: int) -> int: ...
    @overload
    def get(self, key: str, default: float) -> float: ...
    @overload
    def get(self, key: str, default: None) -> Property: ...

    def get(self, key: str, default: Property | None = None) -> Property | None:
        return self.props.get(key, default)


class TiledTile(_TiledBase):
    def __init__(
        self,
        mapman: MapManager,
        image: Surface,
        width: int = 0,
        height: int = 0,
        ts_cols: int = 0,
    ) -> None:
        super().__init__(mapman, "TiledTile")

        self.image = image
        self.size: tuple[int, int] = (width, height)
        self.ts_cols: int = ts_cols
        self.basic_tile_id: int = 0
        self.current_tile_id: int = 0
        self.animated: bool = False
        self._tile_type: str = "tile"
        self.frames: list[_TileAnimation]
        self._frame: int = 0
        self._n_frames: int = 0
        self._frame_timer: float = 0.0
        self._collision_objects: list[_CollisionBox] = []
        self._groups: list[_TiledObjectGroup] = []
        self.z_height: float = 0.01

    def load_from_xml(self, t_xtree: Element, path: Path) -> Self:
        self._tile_type = t_xtree.attrib.get(
            "class", t_xtree.attrib.get("type", "tile")
        )
        self.basic_tile_id = int(t_xtree.attrib["id"])

        self._groups = [
            _TiledObjectGroup(self.mapman).load_from_xml(og, path)
            for og in t_xtree.findall("objectgroup")
        ]

        tile_size = Vector2(self.size)
        for group in self._groups:
            for obj in group._objects:
                pos = obj.pos.elementwise() / tile_size.elementwise()
                size = obj.size.elementwise() / tile_size.elementwise()
                if obj.type == "circle":
                    shape = "circle"
                    radius = obj.size.x / tile_size.x / 2.0
                    pos = pos.elementwise() + radius
                else:
                    shape = "rect"
                    radius = 0
                self._collision_objects.append(
                    _CollisionBox(shape=shape, pos=pos, radius=radius, size=size)
                )

        def pos_from_id(tile_id: int) -> tuple[int, int]:
            sx = (tile_id % self.ts_cols) * self.size[0]
            sy = (tile_id // self.ts_cols) * self.size[1]
            return int(sx), int(sy)

        animation = t_xtree.findall("animation")

        if animation:
            frames = animation[0].findall("frame")
            self.frames = [
                _TileAnimation(
                    frame_id=int(f.attrib["tileid"]),
                    duration=int(f.attrib["duration"]) / 1000.0,
                    offset=pos_from_id(int(f.attrib["tileid"])),
                    size=self.size,
                    image=self.image,
                    collision_boxes=(
                        self._collision_objects
                        if int(f.attrib["tileid"]) == self.basic_tile_id
                        else []
                    ),
                )
                for f in frames
            ]
            self.animated = True
        else:
            self.frames = [
                _TileAnimation(
                    frame_id=self.basic_tile_id,
                    duration=0.0,
                    offset=pos_from_id(self.basic_tile_id),
                    size=self.size,
                    image=self.image,
                    collision_boxes=self._collision_objects,
                )
            ]

        self._n_frames = len(self.frames)
        self.current_tile_id = self.frames[0].frame_id
        self._frame_timer = self.frames[0].duration

        self.props = read_properties_to_dict(t_xtree)
        self.z_height = self.get("z_height", 0.01)
        return self

    def update(self, elapsed_time: float) -> bool:
        """Update tile and return True on new frame."""
        if self._n_frames <= 1:
            return False

        self._frame_timer -= elapsed_time
        if self._frame_timer <= 0:
            self._frame = (self._frame + 1) % self._n_frames
            self.current_tile_id = self.frames[self._frame].frame_id
            self._frame_timer += self.frames[self._frame].duration
            return True

        return False

    def current_offset(self):
        return self.frames[self._frame].offset

    def get_frame(self) -> _TileAnimation:
        return self.frames[self._frame]

    def get_collision_boxes(self) -> list[_CollisionBox]:
        frame_cb = self.frames[self._frame].collision_boxes
        if frame_cb:
            return frame_cb
        return self._collision_objects

    def reset(self) -> None:
        self._frame = 0
        self._frame_timer = self.frames[self._frame].duration
        self.current_tile_id = self.frames[self._frame].frame_id


class TiledTemplate(_TiledBase):
    def __init__(self, mapman: MapManager, name: str) -> None:
        super().__init__(mapman, "TiledTemplate")
        self.name = name
        self.tileset: TiledTileset
        self.first_gid: int = 0
        self.template_name: str = "Unnamed"
        self.template_type: str = "Untyped"
        self.gid: int = 0
        self.size: Vector2 = Vector2()

    def load_from_path(self, path: Path) -> Self:
        path = Path(path)
        t_xtree = ElementTree.parse(path).getroot()
        tileset = t_xtree.findall("tileset")[0]
        self.tileset = self.mapman.get_tileset(path.parent / tileset.attrib["source"])
        self.first_gid = int(tileset.attrib["firstgid"])

        obj = t_xtree.findall("object")[0]
        self.template_name = obj.attrib.get("name", "Unnamed")
        self.template_type = obj.attrib.get("type", obj.attrib.get("class", "Untyped"))
        self.gid = int(obj.attrib["gid"])
        self.size = Vector2(int(obj.attrib["width"]), int(obj.attrib["height"]))

        self.props = read_properties_to_dict(obj)

        return self


class TiledObject(_TiledBase):
    def __init__(self, mapman: MapManager) -> None:
        super().__init__(mapman, "TiledObject")

        self.object_id: int = 0
        self.type: str = ""
        self.pos: Vector2 = Vector2()
        self.size: Vector2 = Vector2()
        self.tileset: TiledTileset | None = None
        self.gid: int = 0

    def load_from_xml(self, o_xtree: Element, path: Path) -> Self:
        self.object_id = int(o_xtree.attrib["id"])
        self.pos = Vector2(float(o_xtree.attrib["x"]), float(o_xtree.attrib["y"]))

        tsource = o_xtree.attrib.get("template", "")
        if tsource:
            tpl = self.mapman.get_template(path.parent / tsource)
            self.name = tpl.template_name
            self.type = tpl.template_type
            self.size = tpl.size
            self.tileset = tpl.tileset
            self.gid = tpl.gid - tpl.first_gid
            self.props = tpl.props.copy()
            # Templates' y positions are bottom instead of top
            self.pos.y -= self.size.y
        else:
            self.size = Vector2(
                float(o_xtree.attrib["width"]), float(o_xtree.attrib.get("height", 0.0))
            )

        self.name = o_xtree.attrib.get("name", self.name)
        self.type = o_xtree.attrib.get("type", o_xtree.attrib.get("class", self.type))
        self.props.update(read_properties_to_dict(o_xtree))
        return self


class _TiledObjectGroup(_TiledBase):
    def __init__(self, mapman: MapManager):
        super().__init__(mapman, "TiledObjectGroup")

        self._layer_id: int = 0
        self._objects: list[TiledObject] = []

    def load_from_xml(self, o_xtree: Element, path: Path) -> Self:
        self._layer_id = int(o_xtree.attrib["id"])
        objects = o_xtree.findall("object")
        for obj in objects:
            self._objects.append(TiledObject(self.mapman).load_from_xml(obj, path))

        return self


class TiledTileset:
    """Represents a Tiled tileset normally stored in a .tsx file."""

    def __init__(self, mapman: MapManager, name: str = "") -> None:
        self._mapman = mapman
        self.name: str = name
        self.image: Surface = Surface((0, 0))
        self._image_width: int = 0
        self._image_height: int = 0
        self._tile_width: int = 0
        self._tile_height: int = 0
        self._tile_count: int = 0
        self.n_cols: int = 0

        self.tiles: dict[int, TiledTile] = {}
        self._anim_tiles: list[TiledTile] = []
        self._is_new_frame: bool = False

    def load_from_path(self, path: str | Path) -> Self:
        """Load tileset information from tsx file.

        Args:
            path: File path to the tsx file to load.

        Returns:
            A reference to this object.

        """
        path = Path(path)
        t_xtree = ElementTree.parse(path).getroot()

        self._tile_width = int(t_xtree.attrib["tilewidth"])
        self._tile_height = int(t_xtree.attrib["tileheight"])
        self._tile_count = int(t_xtree.attrib["tilecount"])
        self.n_cols = int(t_xtree.attrib["columns"])

        image = t_xtree.findall("image")[0]
        image_path = path.parent / image.attrib["source"]
        self._image_width = int(image.attrib["width"])
        self._image_height = int(image.attrib["height"])
        self.image = self._mapman.get_image(image_path)

        tiles = t_xtree.findall("tile")

        for tile in tiles:
            t_obj = TiledTile(
                self._mapman,
                self.image,
                self._tile_width,
                self._tile_height,
                self.n_cols,
            ).load_from_xml(tile, path)
            self.tiles[t_obj.basic_tile_id] = t_obj
            if t_obj.animated:
                self._anim_tiles.append(t_obj)

        return self

    def update(self, elapsed_time: float) -> bool:
        """Update all animated tiles in this tileset.

        Args:
            elapsed_time: How many seconds to progress the simulation.

        Returns:
            True if any of the tiles reached a new state.
        """
        if self._is_new_frame:
            changed = False
            for tile in self._anim_tiles:
                changed = tile.update(elapsed_time) or changed
            self._is_new_frame = False
            return changed

        return False

    def get_tile(self, tile_id: int) -> TiledTile:
        """Return tile at index ``tile_id``."""
        return self.tiles[tile_id]

    def start_new_frame(self):
        """Notify tileset about a new frame starting.

        Tilesets should not update more than once per frame, which can happen if
        multiple maps with the same tileset are active at the same time.
        Tilesets will only update if a new frame was triggered manually.
        """
        self._is_new_frame = True

    def reset(self) -> None:
        """Reset the animation state of all animated tiles."""
        for tile in self._anim_tiles:
            tile.reset()


class TiledLayerRenderable:
    def __init__(self, image: Surface, layer: int = 0, elevation: int = 0) -> None:
        self.image = image
        self.layer = layer
        self.elevation = elevation
        self.duration: float = 1.0
        self.pos: Vector2 = Vector2()

    def draw(self, ttv: Renderer, cache: bool = False) -> None:
        ttv.draw_surface(self.pos, self.image, cache=cache)

    def get_pos(self) -> Vector2:
        return self.pos


class _TiledLayer(_TiledBase):
    def __init__(self, mapman: MapManager) -> None:
        super().__init__(mapman, "Unnamed Layer")
        self._layer_id: int = 0
        self._width: int = 0
        self._height: int = 0
        self._layer_type: str = "layer"
        self.offset: Vector2 = Vector2(0, 0)
        self.speed: Vector2 = Vector2(0, 0)
        self.elevation: int = 0
        self.is_wall_layer: bool = False
        self._is_prerendered: bool = False
        self._prerendered_frames: list[TiledLayerRenderable] = []
        self._durations: list[float] = []
        self._timer: float = 0.25
        self._frame: int = 0

        self._indices: list[int] = []

    def load_from_xml(self, l_xtree: Element) -> Self:
        self._name = l_xtree.attrib["name"]
        self._layer_id = int(l_xtree.attrib["id"])
        self._layer_type = l_xtree.attrib.get(
            "class", l_xtree.attrib.get("type", "Layer")
        )
        self._width = int(l_xtree.attrib["width"])
        self._height = int(l_xtree.attrib["height"])

        data = l_xtree.findall("data")[0]
        reader = csv.reader(StringIO(data.text), delimiter=",")
        for row in reader:
            if len(row) <= 0:
                continue
            self._indices.extend([int(c) for c in row if c])

        self.props = read_properties_to_dict(l_xtree)
        self.elevation = self.get("elevation", 0)
        self.is_wall_layer = self.get("is_wall_layer", False)
        return self

    def update(self, elapsed_time: float) -> bool:
        if self._is_prerendered:
            self._timer -= elapsed_time
            if self._timer <= 0.0:
                self._frame = (self._frame + 1) % len(self._prerendered_frames)
                self._timer += self._durations[self._frame]

        if self.speed == 0.0:
            return False

        self.offset += self.speed * elapsed_time
        if self.offset.x > self._width:
            self.offset.x -= self._width
        if self.offset.x < 0:
            self.offset.x += self._width
        if self.offset.y > self._height:
            self.offset.y -= self._height
        if self.offset.y < 0:
            self.offset.y += self._height

        return True

    def get_index(self, px: int, py: int) -> int:
        if self.offset.x != 0.0:
            px = math.floor(px - self.offset.x)
            if px > self._width:
                px -= self._width
            while px < 0:
                px += self._width
        if self.offset.y != 0.0:
            py = math.floor(py - self.offset.y)
            if py > self._height:
                py -= self._height
            while py < 0:
                py += self._height

        if 0 <= px < self._width and 0 <= py < self._height:
            return self._indices[py * self._width + px]
        else:
            return 0

    def get_all_indices(self) -> list[int]:
        return self._indices

    def add_prerendered_frame(self, renderable: TiledLayerRenderable) -> None:
        self._prerendered_frames.append(renderable)
        self._durations.append(renderable.duration)

    def get_pre_rendered_frame(self) -> TiledLayerRenderable | None:
        if not self._is_prerendered:
            return None
        frame = self._prerendered_frames[self._frame]
        frame.pos = Vector2() + self.offset
        return frame


class TiledTilemap:
    """Represents an orthogonal Tiled tilemap."""

    def __init__(self, mapman: MapManager, name: str = "") -> None:
        self._mapman: MapManager = mapman
        self.name = name

        self._width: int = 0
        self._height: int = 0
        self._tile_width = 1
        self._tile_height = 1
        self.world_size: Vector2 = Vector2(0, 0)
        self.tile_size: Vector2 = Vector2(0, 0)

        self._layers: list[_TiledLayer] = []
        self._floor_layer_map: dict[int, list[_TiledLayer]] = {}
        self._wall_layers: list[_TiledLayer] = []
        self._decor_layers: list[_TiledLayer] = []
        self._tilesets: list[_TilesetInfo] = []
        self._groups: list[_TiledObjectGroup] = []
        self._cache: dict[int, _TileInfo] = {}
        self._tile_source_cache: TileCache = {}
        self.debug_draws: list[dict[str, Any]] = []
        self.br = Vector2()
        self.tl = Vector2()

        # Prerendering
        self._is_pre_rendered: bool = False
        self._rendered_layers: dict[int, list[tuple[Surface, float]]] = {}

    def load_from_path(self, path: str | Path) -> None:
        path = Path(path)
        m_xtree = ElementTree.parse(path).getroot()

        self._width = int(m_xtree.attrib["width"])
        self._height = int(m_xtree.attrib["height"])
        self.world_size = Vector2(self._width, self._height)
        self._tile_width = int(m_xtree.attrib["tilewidth"])
        self._tile_height = int(m_xtree.attrib["tileheight"])
        self.tile_size = Vector2(self._tile_width, self._tile_height)

        self._props = read_properties_to_dict(m_xtree)

        # TODO allow to load embedded tilesets
        self._tilesets = [
            _TilesetInfo(
                tileset=self._mapman.get_tileset(
                    (path.parent / ts.attrib["source"]).resolve()
                ),
                first_gid=int(ts.attrib["firstgid"]),
            )
            for ts in m_xtree.findall("tileset")
        ]

        self._layers = [
            _TiledLayer(self._mapman).load_from_xml(layer)
            for layer in m_xtree.findall("layer")
        ]

        for layer in self._layers:
            if layer.is_wall_layer:
                self._wall_layers.append(layer)
            else:
                self._floor_layer_map.setdefault(layer.elevation, []).append(layer)

        self._groups = [
            _TiledObjectGroup(self._mapman).load_from_xml(og, path)
            for og in m_xtree.findall("objectgroup")
        ]

    def update(self, elapsed_time: float) -> bool:
        changed = True
        for info in self._tilesets:
            changed = info.tileset.update(elapsed_time) and changed

        for layer in self._layers:
            changed = layer.update(elapsed_time) and changed

        return changed

    def draw(self, ttv: Renderer, layers: list[int] | None = None) -> None:
        tl = vmax(ttv.get_tl_tile(), VZERO)
        br = vmin(ttv.get_br_tile(), self.world_size)
        self.tl = tl
        self.br = br
        if layers is None or not layers:
            layers = [x for x in range(len(self._layers))]

        self.debug_draws = []

        for lid in layers:
            if lid >= len(self._layers):
                continue
            layer = self._layers[lid]

            for y in range(int(tl.y), int(br.y) + 1):
                for x in range(int(tl.x), int(br.x) + 1):
                    tid = layer.get_index(x, y)
                    if tid <= 0:
                        continue

                    info = self._cache.get(tid)
                    if info is None:
                        if not self._load_to_cache(tid):
                            continue
                        info = self._cache[tid]

                    tile_position = Vector2(x, y)
                    src_pos = Vector2(info.tile.current_offset())

                    ttv.draw_surface(
                        tile_position,
                        info.tileset.image,
                        src_pos=src_pos,
                        src_size=self.tile_size,
                    )

                    for obj in info.tile.get_collision_boxes():
                        self.debug_draws.append(
                            {
                                "is_circle": obj.shape == "circle",
                                "pos": obj.pos + tile_position,
                                "size": obj.size,
                                "radius": obj.radius,
                            }
                        )

        return

    def draw_to_surface(
        self,
        surf: Surface,
        offset: Vector2,
        visible_tiles_tl: Vector2 | None = None,
        visible_tiles_br: Vector2 | None = None,
        special_flags: int = 0,
    ) -> None:
        visible_tiles_tl = (
            Vector2(0, 0) if visible_tiles_tl is None else visible_tiles_tl
        )
        visible_tiles_br = (
            Vector2(surf.get_size()) if visible_tiles_br is None else visible_tiles_br
        )

        # Get offsets for smooth movement
        tile_offset = offset - vfloor(offset)
        tile_offset.x *= self._tile_width
        tile_offset.y *= self._tile_height

        for layer in self._layers:
            layer_offset = layer.offset - vfloor(layer.offset)
            layer_offset.x *= self._tile_width
            layer_offset.y *= self._tile_height

            layer_vtiles_sx = int(visible_tiles_tl.x)
            layer_vtiles_sy = int(visible_tiles_tl.y)
            if layer.speed.x != 0.0:
                layer_vtiles_sx -= 1
            if layer.speed.y != 0.0:
                layer_vtiles_sy -= 1

            # Draw visible tiles of the map
            for y in range(layer_vtiles_sy, int(visible_tiles_br.y) + 2):
                for x in range(layer_vtiles_sx, int(visible_tiles_br.x) + 2):
                    tid = layer.get_index(
                        int(x + math.floor(offset.x)), int(y + math.floor(offset.y))
                    )
                    if tid <= 0:
                        # Zero means the tile was not set in Tiled
                        continue
                    if tid not in self._cache:
                        if not self._load_to_cache(tid):
                            continue
                    info = self._cache[tid]
                    sx = int(
                        (info.tile.current_tile_id % info.tileset.n_cols)
                        * self._tile_width
                    )
                    sy = int(
                        (info.tile.current_tile_id // info.tileset.n_cols)
                        * self._tile_height
                    )

                    px = int(x * self._tile_width - tile_offset.x + layer_offset.x)
                    py = int(y * self._tile_height - tile_offset.y + layer_offset.y)

                    surf.blit(
                        info.tileset.image,
                        (px, py),
                        ((sx, sy), (self._tile_width, self._tile_height)),
                        special_flags,
                    )

    def get_rendered_layers(self) -> list[TiledLayerRenderable]:
        layers = [
            layer_frame
            for layer in self._layers
            if (layer_frame := layer.get_pre_rendered_frame()) is not None
        ]

        return layers

    def _load_to_cache(self, tid: int) -> bool:
        tileset: TiledTileset | None = None
        first_gid: int = 0
        for tsinfo in self._tilesets:
            if tid < tsinfo.first_gid:
                break

            first_gid = tsinfo.first_gid
            tileset = tsinfo.tileset

        if tileset is None:
            return False

        tidx = tid - first_gid
        tile = tileset.get_tile(tidx)
        self._cache[tid] = _TileInfo(tileset=tileset, tile=tile)
        return True

    def start_new_frame(self) -> None:
        for tsinfo in self._tilesets:
            tsinfo.tileset.start_new_frame()

    def get_tiles(self, x: int, y: int, z: int = 0) -> list[TiledTile]:
        tiles = []
        for layer in self._floor_layer_map.get(z, []):
            tile = self._collect_tile(layer, x, y)
            if tile is None:
                continue
            tiles.append(tile)

        for layer in self._wall_layers:
            if layer.elevation <= z:
                tile = self._collect_tile(layer, x, y)
                if tile is None:
                    continue
                if z < layer.elevation + tile.z_height:
                    tiles.append(tile)
        return tiles

    def get_tiles_in_area(
        self, pos: Vector2, area: Vector2, z: int = 0
    ) -> list[TiledTile]:
        tiles = []
        tl = vfloor(pos)
        br = tl + vfloor(area.elementwise() + 1)

        for y in range(int(tl.y), int(br.y)):
            for x in range(int(tl.x), int(br.x)):
                tiles.extend(self.get_tiles(x, y, z))

        return tiles

    def _collect_tile(self, layer: _TiledLayer, x: int, y: int) -> TiledTile | None:
        tid = layer.get_index(x, y)
        if tid <= 0:
            return None

        info = self._cache.get(tid)
        if info is None:
            if not self._load_to_cache(tid):
                return None
            info = self._cache[tid]

        return info.tile

    def get_objects(self) -> list[TiledObject]:
        all_objects = []
        for group in self._groups:
            all_objects.extend(group._objects)

        return all_objects

    def prerender_layers(self) -> None:
        """Compute possible animation states for all layers.

        Prerendered means that the tile layers will be drawn to a surface once.
        During the simulation, the full layer image will be drawn instead of
        each tile individually. Normally, this results in a noticable speed-up.
        However, when using animated tiles, those animations have to be pre-
        computed as well.

        The current implementation will find every possible combination of tile
        animations and render an image for that combination. This works well and
        accurate if the frame times of the animated tiles are equal or multiples
        of each other. Otherwise, the number of frame to precompute will grow
        exponentially.

        """
        for layer in self._layers:
            layer._is_prerendered = True
            indices = layer.get_all_indices()

            data = build_frame_table(self, layer)
            schedule = build_prerender_schedule(data)

            for idx in range(len(schedule)):
                renderable = TiledLayerRenderable(
                    Surface(self.world_size.elementwise() * self.tile_size),
                    layer.get("layer", 0),
                    layer.elevation,
                )
                renderable.image.fill((254, 253, 252))

                # Draw current frame state to surface
                for y in range(int(self.world_size.y)):
                    for x in range(int(self.world_size.x)):
                        tid = indices[int(y * self.world_size.x + x)]
                        if (info := self._cache.get(tid)) is None:
                            continue
                        tile_position = Vector2(x, y).elementwise() * self.tile_size
                        src_pos = Vector2(info.tile.current_offset())
                        renderable.image.blit(
                            info.tileset.image,
                            tile_position,
                            ((src_pos, self.tile_size)),
                        )
                renderable.image.set_colorkey((254, 253, 252))

                # Compute next animation state
                frame_t = schedule[idx][0]
                renderable.duration = frame_t
                layer.add_prerendered_frame(renderable)
                if len(schedule) > 1:
                    for tsinfo in self._tilesets:
                        tsinfo.tileset.start_new_frame()
                        tsinfo.tileset.update(frame_t)

            for tsinfo in self._tilesets:
                tsinfo.tileset.reset()


class MapManager:
    def __init__(self) -> None:
        self._tilemaps: dict[str, TiledTilemap] = {}
        self._tilesets: dict[str, TiledTileset] = {}
        self._templates: dict[str, TiledTemplate] = {}
        self._images: dict[str, Surface] = {}
        self._loaded_paths: dict[str, str] = {}

    def load(self, files: list[str | Path]) -> None:
        for f in files:
            fp = Path(f).resolve()

            if not fp.exists():
                LOG.warning("File path '%s' does not exist! Skipping", fp)
                continue

            if fp.is_dir():
                self._load_dir(fp)
            else:
                self._load_file(fp)

    def _load_file(self, fp: Path, skip_invalid: bool = False) -> None:
        if str(fp) in self._loaded_paths:
            return

        _, suf = fp.parts[-1].rsplit(".")
        if suf.lower() == "tmx":
            self._load_tilemap(fp)
        elif suf.lower() == "tsx":
            self._load_tileset(fp)
        elif suf.lower() == "tx":
            pass  # Template
        elif not skip_invalid:
            msg = (
                f"File {fp} has an unsupported file ending {suf} . "
                "Please provide .tmx, .tsx, or .tx"
            )
            raise ValueError(msg)

    def _load_dir(self, fp: Path) -> None:
        pass

    def _load_tilemap(self, path: Path) -> str:
        name = Path(path).parts[-1].rsplit(".", 1)[0]
        if name in self._tilemaps:
            return name

        tm = TiledTilemap(self, name)

        LOG.info("Attempting to load tilemap '%s' from TMX file '%s' ...", name, path)
        tm.load_from_path(path)
        LOG.info("Map '%s' successfully loaded.", name)

        self._tilemaps[name] = tm
        self._loaded_paths[str(path)] = name
        return name

    def _load_tileset(self, path: Path) -> str:
        name = Path(path).parts[-1].rsplit(".", 1)[0]
        if name in self._tilesets:
            return name

        ts = TiledTileset(self, name)

        LOG.info("Attempting to load tileset '%s' from TSX file '%s' ...", name, path)
        ts.load_from_path(path)
        LOG.info("Tileset '%s' successfully loaded.", name)

        self._tilesets[name] = ts
        self._loaded_paths[str(path)] = name
        return name

    def _load_template(self, path: Path) -> str:
        name = Path(path).parts[-1].rsplit(".", 1)[0]
        if name in self._templates:
            return name

        tpl = TiledTemplate(self, name)

        LOG.info("Attempting to load template '%s' from TX file '%s' ...", name, path)
        tpl.load_from_path(path)

        self._templates[name] = tpl
        self._loaded_paths[str(path)] = name
        return name

    def _load_image(self, path: Path) -> str:
        name = Path(path).parts[-1].rsplit(".", 1)[0]
        if name in self._images:
            return name
        self._images[name] = pygame.image.load(path).convert_alpha()
        self._loaded_paths[str(path)] = name
        return name

    def get_map(self, name: str | Path) -> TiledTilemap:
        name = str(name)
        if name in self._tilemaps:
            return self._tilemaps[name]

        if name in self._loaded_paths:
            return self._tilemaps[self._loaded_paths[name]]

        LOG.info("Tilemap '%s' not found. Attempting to read from disk ...", name)
        try:
            self._load_tilemap(Path(name))
        except ValueError:
            LOG.exception(
                "Invalid tilemap name format '%s. File should end with .tmx", name
            )
            raise

        return self._tilemaps[self._loaded_paths[name]]

    def get_tileset(self, name: str | Path) -> TiledTileset:
        name = str(name)
        if name in self._tilesets:
            return self._tilesets[name]

        if name in self._loaded_paths:
            return self._tilesets[self._loaded_paths[name]]

        LOG.info("Tileset '%s' not found. Attempting to read from disk ...", name)
        try:
            self._load_tileset(Path(name))
        except ValueError:
            LOG.exception(
                "Invalid tileset name format '%s'. File should end with .tsx", name
            )
            raise

        return self._tilesets[self._loaded_paths[name]]

    def get_template(self, name: str | Path) -> TiledTemplate:
        name = str(name)
        if name in self._templates:
            return self._templates[name]
        if name in self._loaded_paths:
            return self._templates[self._loaded_paths[name]]

        LOG.info("Template '%s' not found. Attempt to read from disk ...", name)
        try:
            self._load_template(Path(name))
        except ValueError:
            LOG.exception(
                "Invalid template name format '%s'. File should end with .tx", name
            )
            raise

        return self._templates[self._loaded_paths[name]]

    def get_image(self, name: str | Path) -> Surface:
        name = str(name)
        if name in self._images:
            return self._images[name]
        if name in self._loaded_paths:
            return self._images[self._loaded_paths[name]]

        LOG.info("Image '%s' not found. Attempting to read from disk ...", name)
        self._load_image(Path(name))

        return self._images[self._loaded_paths[name]]


def read_properties_to_dict(xtree: Element):
    return {
        p.attrib["name"]: convert_from_str(
            p.attrib["value"], p.attrib.get("type", "str")
        )
        for pd in xtree.findall("properties")
        for p in pd.findall("property")
    }


def build_frame_table(
    tm: TiledTilemap, layer: _TiledLayer
) -> dict[int, dict[int, float]]:
    """Build the frame table as preprocessing step for the prerender schedule.

    Args:
        tm: The tilemap object.
        layer: The currently processed layer.

    Returns:
        The frame table containing the frame durations for each tile ID.
    """
    data = {}
    indices = layer.get_all_indices()

    for y in range(int(tm.world_size.y)):
        for x in range(int(tm.world_size.x)):
            tid = indices[int(y * tm.world_size.x + x)]
            info = tm._cache.get(tid)
            if info is None:
                if not tm._load_to_cache(tid):
                    continue
                info = tm._cache[tid]
            if not info.tile.animated:
                continue

            frame_ticks = {}
            for idx, frame in enumerate(info.tile.frames):
                frame_ticks[idx] = frame.duration
            data[tid] = frame_ticks
    return data


def build_prerender_schedule(
    frame_table: dict[int, dict[int, float]],
) -> list[tuple[float, dict[int, int]]]:
    """Build the prerender schedule that combines frame durations of all tiles.

    Args:
        frame_table: The frame table for the current layer, computed by
            :func:`build_frame_table`.

    Returns:
        The prerender schedule that contains the durations that are required to
        capture all possible tile state combinations.
    """
    if not frame_table:
        return [(0.0, {})]

    tiles: dict[int, dict[str, Any]] = {}
    for tile_id, frames in frame_table.items():
        tiles[tile_id] = {
            "frames": list(frames.items()),
            "frame_idx": 0,
            "remaining": frames[0],
        }

    def snapshot():
        return tuple(
            (tile_id, state["frames"][state["frame_idx"]][0])
            for tile_id, state in sorted(tiles.items())
        )

    seen_states = set()
    schedule = []

    while True:
        state = snapshot()
        if state in seen_states:
            break
        seen_states.add(state)

        # Find next event
        dt = min(state["remaining"] for state in tiles.values())

        schedule.append((dt, state))

        # Update tiles
        for state in tiles.values():
            state["remaining"] -= dt
            if state["remaining"] == 0:
                state["frame_idx"] = (state["frame_idx"] + 1) % len(state["frames"])
                state["remaining"] = state["frames"][state["frame_idx"]][1]
    return schedule


def convert_from_str(val: str, vtype: str):
    if vtype == "bool":
        return strtobool(val)
    elif vtype == "float":
        return float(val)
    elif vtype == "int":
        return int(val)
    return val


def strtobool(val: str) -> bool:
    """Convert a string representation of truth to true (1) or false (0).

    True values are 'y', 'yes', 't', 'true', 'on', and '1'; false values
    are 'n', 'no', 'f', 'false', 'off', and '0'.  Raises ValueError if
    'val' is anything else.
    """
    val = val.lower()
    if val in ("y", "yes", "t", "true", "on", "1"):
        return True
    elif val in ("n", "no", "f", "false", "off", "0", ""):
        return False
    else:
        msg = f"Invalid truth value {val}"
        raise ValueError(msg)


def vfloor(vec: Vector2, inplace: bool = False) -> Vector2:
    if inplace:
        vec.x = math.floor(vec.x)
        vec.y = math.floor(vec.y)
        return vec
    return Vector2(math.floor(vec.x), math.floor(vec.y))


def vclamp(val: Vector2, low: Vector2, high: Vector2) -> Vector2:
    return Vector2(max(low.x, min(high.x, val.x)), max(low.y, min(high.y, val.y)))


def vmax(val: Vector2, other: Vector2) -> Vector2:
    return Vector2(max(val.x, other.x), max(val.y, other.y))


def vmin(val: Vector2, other: Vector2) -> Vector2:
    return Vector2(min(val.x, other.x), min(val.y, other.y))
