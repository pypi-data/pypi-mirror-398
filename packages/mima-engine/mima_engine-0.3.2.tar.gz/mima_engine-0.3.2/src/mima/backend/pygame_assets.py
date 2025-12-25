from __future__ import annotations

import csv
import logging
import os
from typing import TYPE_CHECKING, Any, Dict, Optional

import pygame

from ..maps.tiled.tiled_map import TiledMap
from ..maps.tiled.tiled_template import TiledTemplate
from ..maps.tiled.tiled_tileset import TiledTileset

if TYPE_CHECKING:
    from ..maps.tilemap import Tilemap
    from ..util import RuntimeConfig

LOG = logging.getLogger(__name__)


class PygameAssets:
    def __init__(self, rtc: RuntimeConfig, init_file: str):
        self.rtc = rtc
        self._images: Dict[str, pygame.Surface] = {}
        self._tilesets: Dict[str, TiledTileset] = {}
        self._templates: Dict[str, TiledTemplate] = {}
        self._sprite_sheets: Dict[str, Dict[Any]] = {}
        self._maps: Dict[str, TiledMap] = {}
        self._music: Dict[str, str] = {}
        self._sound: Dict[str, str] = {}
        self._csvs: Dict[str, str] = {}
        self._assets_to_load: Dict[str, str] = {}
        self._assets_to_preload: Dict[str, str] = {}
        self._paths: Dict[str, str] = {}
        self.data_path = ""
        self._preprocess_asset_file(init_file)

    def _preprocess_asset_file(self, init_file: str):
        self.data_path = os.path.dirname(init_file)
        # path = os.path.join(self._data_path, asset_file)
        current_type = "paths"

        with open(init_file) as f:
            for line in f.readlines():
                line = line.strip()
                self._assets_to_load.setdefault(current_type, [])
                self._assets_to_preload.setdefault(current_type, [])

                assets_to_load = self._assets_to_load

                if "_PRELOAD]" in line:
                    assets_to_load = self._assets_to_preload
                if "[PATHS]" in line:
                    current_type = "paths"
                elif "[GFX" in line:
                    current_type = "gfx"
                elif "[MAPS" in line:
                    current_type = "maps"
                elif "[TEMPLATES" in line:
                    current_type = "templates"
                elif "[TILESETS" in line:
                    current_type = "tilesets"
                elif "[MUSIC" in line:
                    current_type = "music"
                elif "[SFX" in line:
                    current_type = "sound"
                elif "[CSV" in line:
                    current_type = "csv"
                else:
                    if line != "" and not line.startswith("#"):
                        if current_type != "paths":
                            # print(self.data_path, current_type, line)
                            assets_to_load[current_type].append(
                                os.path.abspath(
                                    os.path.join(
                                        self.data_path,
                                        self._paths.get(current_type, "."),
                                        line,
                                    )
                                )
                            )
                        else:
                            name, p = line.split("=")
                            self._paths[name] = p

    def load(self):
        for gfx in self._assets_to_load.get("gfx", []):
            name = os.path.split(gfx)[1].split(".")[0]
            # print(gfx, name)
            self._load_sprite(name, gfx)

        for tts in self._assets_to_load.get("tilesets", []):
            try:
                LOG.debug("Attempting to load tileset %s", tts)
                name = os.path.split(tts)[1].split(".")[0]
                self._load_tileset(name, tts)
            except Exception as err:
                LOG.warning("Couldn't load tileset %s: %s", tts, err)

        for tmp in self._assets_to_load.get("templates", []):
            name = os.path.split(tmp)[1].split(".")[0]
            self._load_template(name, tmp)

        for tmap in self._assets_to_load.get("maps", []):
            name = os.path.split(tmap)[1].split(".")[0]
            self._load_map(name, tmap)

        for mus in self._assets_to_load.get("music", []):
            name = os.path.split(mus)[1].split(".")[0]
            self._load_music(name, mus)

        for snd in self._assets_to_load.get("sound", []):
            name = os.path.split(snd)[1].split(".")[0]
            self._load_sound(name, snd)

        for csvf in self._assets_to_load.get("csv", []):
            name = os.path.split(csvf)[1].split(".")[0]
            self._load_csv(name, csvf)

    def _load_csv(self, name, filename):
        if not os.path.isfile(filename):
            filename = os.path.join(
                self.data_path, "csv", os.path.split(filename)[-1]
            )

        possible_name = os.path.split(filename)[-1][:-4]
        if possible_name in self._csvs:
            LOG.warning(f"CSV '{filename}' already loaded as {possible_name}.")
        elif name in self._csvs:
            LOG.debug(f"CSV '{name}' alread loaded. Skipping.")
            return name

        with open(filename, "r") as csv_file:
            reader = csv.DictReader(csv_file, delimiter=",")
            self._csvs[name] = [row for row in reader]

    def _load_sprite(self, name, filename=None):
        if filename is None:
            filename = f"{name}.png"

        # print(filename)
        if not os.path.isfile(filename):
            filename = os.path.join(
                self.data_path, "gfx", os.path.split(filename)[-1]
            )
        # print(name, filename)

        possible_name = os.path.split(filename)[-1][:-4]
        if possible_name in self._images:
            LOG.warning(
                "Sprite '%s' is possibly already loaded with name %s.",
                filename,
                possible_name,
            )
        elif name in self._images:
            LOG.debug("Sprite '%s' already loaded. Skipping.")
            return name

        self._images[name] = self._load_sprite_from_disk(filename)

        return name

    def _load_tileset(self, name, filename=None):
        if filename is None:
            filename = f"{name}.tsx"

        if not os.path.isfile(filename):
            filename = os.path.abspath(
                os.path.join(
                    self.data_path,
                    self._paths.get("tilesets", "."),
                    os.path.split(filename)[-1],
                )
            )

        possible_name = os.path.split(filename)[-1][:-4]
        if possible_name in self._tilesets:
            LOG.warning(
                "Tileset at '%s' is possible already loaded with name %s.",
                filename,
                possible_name,
            )
        elif name in self._tilesets:
            LOG.debug("Tileset at '%s' already loaded. Skipping", filename)
            return name
        ts = TiledTileset(name, filename)
        self._tilesets[name] = ts

        # Load sprite sheets
        for tile in ts.tiles:
            if not tile.sprite_name:
                continue

            self._sprite_sheets.setdefault(tile.sprite_name, {})
            data = {
                "duration": [],
                "ox": [],
                "oy": [],
                "image": [],
                "width": [],
                "height": [],
            }
            if tile.animated:
                for frame in tile._frames:
                    data["duration"].append(frame.duration)
                    data["ox"].append(frame.frame_id % ts.columns)
                    data["oy"].append(frame.frame_id // ts.columns)
                    data["image"].append(ts.image_name)
                    data["width"].append(ts.tile_width)
                    data["height"].append(ts.tile_height)
            else:
                data["duration"].append(1000)
                data["ox"].append(tile.tile_id % ts.columns)
                data["oy"].append(tile.tile_id // ts.columns)
                data["image"].append(ts.image_name)
                data["width"].append(ts.tile_width)
                data["height"].append(ts.tile_height)

            self._sprite_sheets[tile.sprite_name].setdefault(
                tile.graphic_state, {}
            )
            self._sprite_sheets[tile.sprite_name][tile.graphic_state][
                tile.facing_direction
            ] = data
            LOG.debug(
                "%s",
                {
                    "operation": "add frames",
                    "image": ts.image_name,
                    "sprite": tile.sprite_name,
                    "graphic_state": tile.graphic_state.name,
                    "direction": tile.facing_direction.name,
                    "frame_data": data,
                },
            )

        # for sprite_name in ts.sprite_names:
        #     self._sprites[sprite_name] = {}
        return name

    def _load_template(self, name, filename=None):
        if filename is None:
            filename = f"{name}.tx"

        if not os.path.isfile(filename):
            filename = os.path.join(
                self.data_path, "templates", os.path.split(filename)[-1]
            )

        possible_name = os.path.split(filename)[-1][:-3]
        if possible_name in self._templates:
            LOG.warning(
                "Template at '%s' is possible already loaded with name %s.",
                filename,
                possible_name,
            )
        elif name in self._templates:
            LOG.debug("Template at '%s' already loaded. Skipping", filename)
            return name

        self._templates[name] = TiledTemplate(name, filename)
        return name

    def _load_map(self, name, filename=None):
        possible_name = os.path.split(filename)[-1][:-4]
        if possible_name in self._maps:
            LOG.warning(
                "Map at '%s' is possibly already loaded with name %s.",
                filename,
                possible_name,
            )
        elif name in self._maps:
            LOG.debug("Map at '%s' already loaded. Skipping", filename)
            return name
        try:
            self._maps[name] = TiledMap(name, filename)
        except KeyError:
            LOG.exception(f"Failed to load map={name}")
            raise

        return name

    def _load_music(self, name, filename=None):
        if filename is None:
            filename = f"{name}.ogg"

        if not os.path.isfile(filename):
            filename = os.path.join(
                self.data_path,
                self._paths.get("music", "."),
                os.path.split(filename)[-1],
            )
        possible_name = os.path.split(filename)[-1][:-4]
        if possible_name in self._music:
            LOG.warning(
                "Music at '%s' is possibly already loaded with name %s.",
                filename,
                possible_name,
            )
        elif name in self._music:
            LOG.debug("Music at '%s already loaded. Skipping.", filename)
            return name

        self._music[name] = filename
        return name

    def _load_sound(self, name, filename=None):
        if filename is None:
            filename = f"{name}.ogg"

        if not os.path.isfile(filename):
            filename = os.path.join(
                self.data_path,
                self._paths.get("sfx", "."),
                os.path.split(filename)[-1],
            )
        possible_name = os.path.split(filename)[-1][:-4]
        if possible_name in self._sound:
            LOG.warning(
                "Sound at '%s' is possibly already loaded with name %s.",
                filename,
                possible_name,
            )
        elif name in self._sound:
            LOG.debug("Sound at '%s already loaded. Skipping.", filename)
            return name

        self._sound[name] = pygame.mixer.Sound(filename)
        return name

    def _load_item(self, item):
        LOG.debug("Loading item %s.", item.name)
        self._items[item.name] = item

    def get_sprite(self, name) -> Optional[pygame.Surface]:
        if name is None:
            return None
        else:
            if self.rtc.flags.get("use_color", False):
                name_color = f"{name}_color"
            else:
                name_color = name
            return self._images.get(name_color, self._images[name])

    def get_sprite_data(self, sprite_id):
        if not sprite_id:
            return {}
        return self._sprite_sheets[sprite_id]

    def new_map(self, name, tilemap: Tilemap):
        self._maps[name] = tilemap

    def new_sprite(self, name, surface: pygame.Surface):
        self._images[name] = surface

    def get_tileset(self, name):
        if name not in self._tilesets:
            msg = f"Could not find tileset '{name}'."
            raise ValueError(msg)
            # LOG.warning("Could not find tileset %s.", name)
            # return self._tilesets["simple_sheet"]
        return self._tilesets[name]

    def get_template(self, name):
        if name not in self._templates:
            LOG.warning("Could not find template %s.", name)
            return self._templates["bush01"]
        return self._templates[name]

    def get_map(self, name):
        return self._maps[name]

    def get_music(self, name):
        return self._music[name]

    def get_sound(self, name):
        return self._sound[name]

    def get_csv(self, name):
        return self._csvs[name]

    def _load_sprite_from_disk(self, filename: str) -> pygame.Surface:
        if "color" in filename:
            return pygame.image.load(filename).convert_alpha()
        else:
            image = pygame.image.load(filename).convert_alpha()
            var = pygame.PixelArray(image)

            new_colors = {
                name: color
                for name, color in self.rtc.colors.items()
                if f"{name}_default" in self.rtc.colors
            }
            for name, new_color in new_colors.items():
                var.replace(
                    self.rtc.colors[f"{name}_default"].getRGBA(),
                    new_color.getRGBA(),
                )

            del var
            return image
