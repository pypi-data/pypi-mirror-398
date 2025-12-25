import json
import logging
import os
from os import PathLike
from pathlib import Path
from typing import Any, Dict, Union

# from typing_extensions import overload
from ..util.constants import SAVE_FILE_NAME
from ..util.functions import strtobool

LOG = logging.getLogger(__name__)


class GameState:
    def __init__(self, save_path: PathLike, state_name: str = "autosave.json"):
        self.state_name = state_name
        self._save_path = save_path
        self._state: Dict[str, Any] = {}

    def save_value(
        self, key: str, value: Union[int, float, bool, str, dict, list]
    ):
        parts = key.split("__")
        state = self._state
        for idx, part in enumerate(parts):
            if idx < len(parts) - 1:
                state = state.setdefault(part, {})
            else:
                state[part] = value

    # @overload
    # def load_value(
    #     self, key: str, default: str, astype: str | None
    # ) -> str | None: ...

    # @overload
    # def load_value(
    #     self, key: str, default: int, astype: str | None
    # ) -> int | None: ...

    def load_value(
        self,
        key: str,
        default: int | float | bool | str | dict | list | None = None,
        astype: str | None = None,
    ) -> int | float | bool | str | dict | list | None:
        parts = key.split("__")
        state = self._state
        for idx, part in enumerate(parts):
            if idx >= len(parts) - 1:
                # state = state.get(part)
                if state is None:
                    return default
                else:
                    state = state.get(part)
                    if state is None:
                        return default
                    if astype is not None:
                        return convert(state, astype)
                    return state

            state = state.get(part)

    def load_group(self, key: str, *more_keys: str):
        data = self._state.get(key, {})
        for key in more_keys:
            data = data.get(key, {})
        return data

    def load_from_disk(self, autosave: bool = False):
        # filename = self.filename
        # if autosave:
        #     filename = os.path.join(self._save_path, "autosave.json")
        # else:
        filename = Path(self._save_path) / self.state_name
        try:
            with open(filename, "r") as fp:
                self._state = json.load(fp)
        except FileNotFoundError:
            LOG.info("No saved state found!")
        except json.decoder.JSONDecodeError:
            LOG.info("No saved state found or state corrupted.")

        if autosave:
            self.state_name = self.load_value("savefile_name", "")
        # if autosave:
        #     self.filename = os.path.join(
        #         os.path.split(filename)[0],
        #         f"{self._state['savefile_name']}.json",
        #     )

    def save_to_disk(self, autosave: bool = False):
        # filename = self.filename
        if autosave:
            filename = Path(self._save_path) / "autosave.json"
            self.save_value("savefile_name", self.state_name)
            self.save_value("player__pos_x", 5.0)
            self.save_value("player__pos_y", 5.0)
            self.save_value(
                "player__map_name", self.load_value("player__spawn_map")
            )
        else:
            if self.state_name == "autosave.json":
                self.state_name = chose_filename(self._save_path)
                self.save_value("savefile_name", self.state_name)
            filename = Path(self._save_path) / self.state_name
            self._state["savefile_name"] = self.state_name

            # Auto save file will be removed after a successful save
            try:
                os.remove(Path(self._save_path) / "autosave.json")
            except FileNotFoundError:
                pass

        with open(filename, "w") as fp:
            json.dump(self._state, fp, sort_keys=False, indent=4)

    def delete_keys(self, scope, keypart, exceptions):
        k2d = []
        for k in self._state[scope]:
            if keypart in k and k not in exceptions:
                k2d.append(k)
        for k in k2d:
            del self._state[scope][k]


def chose_filename(save_path: PathLike):

    files = os.listdir(save_path)
    game_idx = 0
    while True:
        savegame = f"{SAVE_FILE_NAME}_{game_idx:03d}.json"
        if savegame not in files:
            return savegame
        game_idx += 1


def convert(value, astype):
    if astype == "int":
        try:
            return int(value)
        except TypeError:
            return value
    if astype == "float":
        try:
            return float(value)
        except TypeError:
            return value
    if astype == "bool":
        try:
            return strtobool(value)
        except AttributeError:
            value
    return value


def load_saved_games(save_path, save_file_name):
    os.makedirs(save_path, exist_ok=True)
    all_games = {}
    if not os.path.isdir(save_path):
        LOG.warning(f"Save folder does not exist: {save_path}")
        return all_games

    files = os.listdir(save_path)
    if not files:
        LOG.info(f"No save files found at {save_path}")
        return all_games

    if "autosave.json" in files:
        all_games["autosave.json"] = GameState(save_path)
        all_games["autosave.json"].load_from_disk(autosave=True)
        LOG.debug(
            "Loading saved game from autosave.json (%s)",
            all_games["autosave.json"].state_name,
        )

    game_idx = 0
    while True:
        savegame = f"{save_file_name}_{game_idx:03d}.json"
        if savegame in files:
            all_games[savegame] = GameState(save_path, savegame)
            all_games[savegame].load_from_disk()
            LOG.debug(f"Loading saved game from {savegame}")
        game_idx += 1
        if game_idx >= len(files):
            break

    return all_games
