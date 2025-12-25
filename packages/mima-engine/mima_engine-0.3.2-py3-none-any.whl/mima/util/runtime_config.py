import configparser
import os
from copy import deepcopy
from typing import Any, Dict, List, Optional, Tuple

from ..types.keys import Key as K
from ..types.player import Player
from .colors import (
    BLACK,
    BLUE,
    DARK_GREY,
    DARK_RED,
    GREEN,
    RED,
    VERY_LIGHT_GREY,
    WHITE,
    Color,
)
from .constants import (
    BIG_FONT_HEIGHT,
    BIG_FONT_NAME,
    BIG_FONT_WIDTH,
    SMALL_FONT_HEIGHT,
    SMALL_FONT_NAME,
    SMALL_FONT_WIDTH,
    TILE_HEIGHT,
    TILE_WIDTH,
)
from .functions import strtobool

DEFAULT_CONFIG = {
    "keyboard_map_p1": {
        "UP": "w",
        "DOWN": "s",
        "LEFT": "a",
        "RIGHT": "d",
        "A": "e",
        "B": "q",
        "X": "x",
        "Y": "y",
        "L": "1",
        "R": "2",
        "START": "r",
        "SELECT": "c",
    },
    "keyboard_map_p2": {
        "UP": "up",
        "DOWN": "down",
        "LEFT": "left",
        "RIGHT": "right",
        "A": "6",
        "B": "2",
        "X": "8",
        "Y": "4",
        "L": "7",
        "R": "9",
        "START": "5",
        "SELECT": "0",
    },
    "joysticks": {"p1": 0, "p2": 1},
    "joystick_map_p1": {
        "UP": "up",
        "DOWN": "down",
        "LEFT": "left",
        "RIGHT": "right",
        "A": "0",
        "B": "1",
        "X": "2",
        "Y": "3",
        "L": "7",
        "R": "8",
        "START": "5",
        "SELECT": "6",
    },
    "joystick_map_p2": {
        "UP": "up",
        "DOWN": "down",
        "LEFT": "left",
        "RIGHT": "right",
        "A": "0",
        "B": "1",
        "X": "2",
        "Y": "3",
        "L": "7",
        "R": "8",
        "START": "5",
        "SELECT": "6",
    },
    "colors": {},
    "color_remaps": {},
    "flags": {},
}


class RuntimeConfig:
    def __init__(
        self,
        config_path: str = "",
        default_config: Optional[Dict[str, Any]] = None,
    ):
        if default_config is None:
            default_config = DEFAULT_CONFIG

        self._loaded: Dict[str, Any] = deepcopy(default_config)

        self._converted: Dict[str, Any] = {}

        if not config_path:
            config_path = os.path.abspath(os.path.join(os.getcwd(), "mima.ini"))

        self._config_path = config_path
        config = configparser.ConfigParser()

        if os.path.exists(config_path):
            config.read(config_path)

            if config.sections():
                self._read_config(config)
            else:
                self._write_config(config)
        else:
            self._write_config(config)

        # Per-game constants
        ## Colors
        self.color_black = BLACK
        self.color_white = WHITE
        self.color_red = RED
        self.color_blue = BLUE
        self.color_green = GREEN
        self.color_dark_red = DARK_RED
        self.color_dark_grey = DARK_GREY
        self.color_very_light_grey = VERY_LIGHT_GREY

        self.tile_width = TILE_WIDTH
        self.tile_height = TILE_HEIGHT

        ## Font
        self.big_font_name = BIG_FONT_NAME
        self.big_font_width = BIG_FONT_WIDTH
        self.big_font_height = BIG_FONT_HEIGHT
        self.small_font_name = SMALL_FONT_NAME
        self.small_font_width = SMALL_FONT_WIDTH
        self.small_font_height = SMALL_FONT_HEIGHT

        ## Locale
        self.locale = "en"

    def _read_config(self, config: configparser.ConfigParser):
        mappings = [
            "keyboard_map_p1",
            "keyboard_map_p2",
            "joystick_map_p1",
            "joystick_map_p2",
        ]
        for m in mappings:
            for key, mapping in config[m].items():
                vals = mapping.strip().split(",")
                self._loaded[m][key.upper()] = vals
        self._loaded["joysticks"] = {
            "p1": int(config["joysticks"].get("p1", 0)),
            "p2": int(config["joysticks"].get("p2", 1)),
        }

        default_colors = {}
        for color_name, color in self._loaded["colors"].items():
            default_colors[f"{color_name}_default"] = color
            self._loaded["colors"][color_name] = config["colors"][color_name]
        self._loaded["colors"].update(default_colors)

        for flag in self._loaded["flags"]:
            self._loaded["flags"][flag] = config["flags"][flag]

    def save_config(self):
        config = configparser.ConfigParser()
        self._write_config(config)

    def _write_config(self, config: configparser.ConfigParser):
        mappings = [
            "keyboard_map_p1",
            "keyboard_map_p2",
            "joystick_map_p1",
            "joystick_map_p2",
        ]
        for m in mappings:
            config[m] = {}
            for key, mapping in self._loaded[m].items():
                config[m][key.lower()] = ",".join(mapping)
        # config["keyboard_map_p1"] = {}
        # config["keyboard_map_p2"] = {}
        config["joysticks"] = {
            "p1": self._loaded["joysticks"].get("p1", 0),
            "p2": self._loaded["joysticks"].get("p2", 1),
        }
        # config["joystick_map_p1"] = {}
        # config["joystick_p2"] =
        # config["joystick_map_p2"] = {}
        config["colors"] = {}
        config["flags"] = {}

        # for key, mapping in self._loaded["keyboard_map_p1"].items():

        for color_name, color in self._loaded["colors"].items():
            if color_name.endswith("_default"):
                continue
            config["colors"][color_name] = color

        for flag_name, flag in self._loaded["flags"].items():
            config["flags"][flag_name] = flag

        with open(self._config_path, "w") as cfg_file:
            config.write(cfg_file)

    def update_keyboard_map(self, kbmap: Dict[K, List[str]]):
        mappings = [
            "keyboard_map_p1",
            "keyboard_map_p2",
            # "joystick_map_p3",
            # "keyboard_map_p4",
        ]
        mip = 1
        for idx, (key, mapping) in enumerate(kbmap.items()):
            mip = idx // 12
            if mip < 1 or mip > 2:
                continue
            key_name = key.name.split("_")[1]
            self._loaded[mappings[mip - 1]][key_name] = mapping

    def update_joystick_map(self, jsmap: Dict[K, List[str]]):
        mappings = [
            # "keyboard_map_p1",
            # "keyboard_map_p2",
            "joystick_map_p1",
            "keyboard_map_p2",
        ]
        mip = 1
        for idx, (key, mapping) in enumerate(jsmap.items()):
            mip = idx // 12
            if mip < 1 or mip > 2:
                continue
            key_name = key.name.split("_")[1]
            self._loaded[mappings[mip - 1]][key_name] = mapping

    def update_joysticks(self, reassign: List[Tuple[int, Player]]):
        self._loaded["joysticks"] = {}
        for item in reassign:
            self._loaded["joysticks"][item[1].name.lower()] = item[0]

    def get_keyboard_map(self) -> Dict[K, List[str]]:
        kbmap = {}
        for but in K:
            if but.value < 12:
                kbmap[but] = []
            elif but.value < 24:
                kbmap[but] = self._loaded["keyboard_map_p1"][but.name.split("_")[1]]

            elif but.value < 36:
                kbmap[but] = self._loaded["keyboard_map_p2"][but.name.split("_")[1]]

            else:
                kbmap[but] = []
        return kbmap

    def get_joystick_map(self) -> Dict[K, List[str]]:
        jsmap = {}

        for but in K:
            if but.value < 12:
                jsmap[but] = []
            elif but.value < 24:
                jsmap[but] = self._loaded["joystick_map_p1"][but.name.split("_")[1]]

            elif but.value < 36:
                jsmap[but] = self._loaded["joystick_map_p2"][but.name.split("_")[1]]

            else:
                jsmap[but] = []
        return jsmap

    def get_joy_to_player(self) -> Dict[int, Player]:
        joy2p = {}
        for p, j in self._loaded["joysticks"].items():
            joy2p[j] = Player[p.upper()]
        return joy2p

    def get_player_to_joy(self) -> Dict[Player, int]:
        p2joy = {}
        for p, j in self._loaded["joysticks"].items():
            p2joy[Player[p.upper()]] = j
        return p2joy

    # @property
    # def keymap(self):
    #     if "keymap" in self._converted:
    #         return self._converted["keymap"]
    #     else:
    #         self._converted["keymap"] = {}
    #         for but in K:
    #             self._converted["keymap"][but] = self._loaded["keymap"][
    #                 but.name
    #             ]

    #     return self._converted["keymap"]

    @property
    def colors(self) -> Dict[str, Color]:
        if "colors" in self._converted:
            return self._converted["colors"]
        else:
            self._converted["colors"] = {}
            for key, val in self._loaded["colors"].items():
                self._converted["colors"][key] = Color(
                    *[int(p) for p in val.strip().split(",")]
                )

            return self._converted["colors"]

    @property
    def flags(self) -> Dict[str, bool]:
        if "flags" in self._converted:
            return self._converted["flags"]
        else:
            self._converted["flags"] = {}
            for flag, value in self._loaded["flags"].items():
                self._converted["flags"][flag] = strtobool(value)

            return self._converted["flags"]
