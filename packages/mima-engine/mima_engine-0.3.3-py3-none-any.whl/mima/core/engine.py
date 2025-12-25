from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from ..backend.pygame_assets import PygameAssets
from ..backend.pygame_audio import PygameAudio
from ..backend.pygame_backend import PygameBackend
from ..backend.pygame_events import PygameUserInput
from ..maps.template import Template
from ..maps.tilemap import Tilemap
from ..objects.animated_sprite import AnimatedSprite
from ..objects.creature import Creature
from ..objects.dynamic import Dynamic
from ..objects.loader import ObjectLoader
from ..objects.sprite import Sprite
from ..scripts import Command, ScriptProcessor
from ..states.memory import Memory
from ..states.quest import Quest
from ..types.gate_color import GateColor
from ..types.mode import Mode
from ..types.player import Player
from ..usables.item import Item
from ..usables.weapon import Weapon
from ..util import RuntimeConfig
from ..util.logging import install_trace_logger
from ..view.camera import Camera
from ..view.mima_view import MimaView
from .database import Database

if TYPE_CHECKING:
    from .states.game_state import GameState

LOG = logging.getLogger(__name__)


class MimaEngine(ABC):
    def __init__(
        self,
        init_file: str,
        config_path: str,
        default_config: Dict[str, Any],
        platform: str = "PC",
        caption: str = "MimaEngine",
    ):
        self.rtc = RuntimeConfig(config_path, default_config)
        install_trace_logger()

        self.backend: PygameBackend = PygameBackend(
            self.rtc, init_file, platform
        )
        self.db: Database
        self._caption: str = caption
        self.seconds_total: float = 0.0
        self.app_fps: float = 0.0
        self.game_fps: float = 0.0
        self.elapsed_time: float = 0.00022
        self._app_time: float = 0.0

        self.enable_touch_controls: bool = False
        self.show_touch_controls: bool = False

        self.mode: Mode = Mode.LOADING
        self.gate_color: GateColor = GateColor.RED
        self.n_gate_colors = 2
        self.script: ScriptProcessor = None
        self.memory: Memory = Memory()
        self.all_games: Dict[str, GameState] = {}
        self.current_game: str = ""
        self.cameras: List[str] = []

    def construct(
        self,
        width: int,
        height: int,
        pixel_size: int,
        fullscreen: bool = False,
        target_fps: int = 60,
        resizable: bool = False,
        no_scaled_flag: bool = False,
        kb_map=None,
    ):
        """Initialize backend and create a window."""
        AnimatedSprite.engine = self
        Camera.engine = self
        Command.engine = self
        Database.engine = self
        Dynamic.engine = self
        # GameMode.engine = self
        Item.engine = self
        PygameBackend.engine = self
        ObjectLoader.engine = self
        Quest.engine = self
        # Scene.engine = self
        ScriptProcessor.engine = self
        Sprite.engine = self
        Template.engine = self
        Tilemap.engine = self
        MimaView.engine = self

        self.script = ScriptProcessor()
        self.db = Database()
        self.backend.init(
            keyboard_map=self.rtc.get_keyboard_map(),
            joystick_map=self.rtc.get_joystick_map(),
            joy_to_player=self.rtc.get_joy_to_player(),
        )
        self.backend.construct(
            width,
            height,
            pixel_size,
            fullscreen,
            target_fps,
            resizable,
            no_scaled_flag,
        )
        self.backend.user_input.enable_touch_controls = (
            self.enable_touch_controls
        )

        return True

    def start(self):
        """Start the main loop"""
        app_frames = 0
        game_frames = 0
        app_seconds = 0.0
        game_seconds = 0.0
        app_frames_total = 0
        game_frames_total = 0
        self.seconds_total = 0.0

        if self.on_user_create():
            while self.backend.keep_running():
                self.backend.set_caption(
                    f"{self._caption} ({self.game_fps:.2f}/"
                    f"{self.app_fps:.2f} fps)"
                )
                self.backend.process_events()

                if not self.backend.keep_running():
                    break

                self.cameras = ["display"]
                if not self.on_user_update(self.elapsed_time):
                    print("Error in on_user_update")
                    break

                self.backend.update_display(*self.cameras)

                self._app_time = self.backend.tick()
                self.elapsed_time = min(self._app_time, 1.0 / 30.0)

                app_seconds += self._app_time
                game_seconds += self.elapsed_time
                app_frames += 1
                game_frames += 1

                if game_seconds >= 1.0:
                    game_frames_total += game_frames
                    self.game_fps = game_frames
                    game_frames = 0
                    game_seconds -= 1.0
                if app_seconds >= 1.0:
                    app_frames_total += app_frames
                    self.seconds_total += app_seconds
                    self.app_fps = app_frames
                    app_frames = 0
                    app_seconds -= 1.0

            print(
                f"App/Game Frames total: {app_frames_total}/"
                f"{game_frames_total}"
            )
            print(f"Seconds total: {self.seconds_total:.3f}")
            print(
                "Average App/Game FPS: "
                f"{app_frames_total/self.seconds_total:.3f}/"
                f"{game_frames_total/self.seconds_total:.3f}"
            )

        self.backend.shutdown()

    @abstractmethod
    def on_user_update(self, elapsed_time: float) -> bool:
        """Update."""
        raise NotImplementedError()

    @abstractmethod
    def on_user_create(self) -> bool:
        raise NotImplementedError()

    def on_user_terminate(self) -> bool:
        self.backend.terminate = True
        return True

    @property
    def assets(self) -> PygameAssets:
        return self.backend.assets

    @property
    def audio(self) -> PygameAudio:
        return self.backend.audio

    @property
    def keys(self) -> PygameUserInput:
        return self.backend.user_input

    def get_map(self, map_name: str):
        return self.backend.assets.get_map(map_name)

    def load_usable(self, item: Item, item_id) -> None:
        LOG.debug("Loading usable %s.", item_id)
        item.init(self.db.get_usable_data(item_id))
        self.memory.items[item_id] = item

    # def load_weapon(self, weapon: Weapon, weapon_id: str) -> None:
    #     LOG.debug("Loading weapon %s.", weapon_id)
    #     weapon.init(self.db.get_weapon_data(weapon_id))
    #     self.memory.items[weapon_id] = weapon

    # def load_item(self, item: Item, item_id: str) -> None:
    #     LOG.debug("Loading item %s.", item_id)
    #     item.init(self.db.get_item_data(item_id))
    #     self.memory.items[item_id] = item

    # def load_item(self, item: Item):
    #     LOG.debug(f"Loading item  {item.name}.")
    #     self.memory.items[item.name] = item

    def get_item(self, item_id: str):
        try:
            return self.memory.items[item_id]
        except KeyError:
            LOG.exception(f"Item '{item_id}' is not defined!")
            raise
        except TypeError:
            print(type(self.memory.items), item_id)
            raise

    def give_item(self, item: Union[str, Item], player: Player = Player.P1):
        if isinstance(item, str):
            item = self.get_item(item)
        self.memory.bag[player].append(item)
        # self.items.append(item)
        return True

    def take_item(self, item: Union[str, Item], player: Player = Player.P1):
        if isinstance(item, str):
            item = self.get_item(item)

        if item in self.memory.bag[player]:
            self.memory.bag[player].remove(item)
            return True
        return False

    def has_item(self, item: Union[str, Item], player: Player = Player.P1):
        if isinstance(item, str):
            item = self.get_item(item)

        return item in self.memory.bag[player]
        # return False

    def progress_quest(self, quest_name: str, new_state: int):
        for quest in self.quests:
            if quest.name == quest_name:
                quest.state = new_state

    def on_enter_background(self):
        LOG.debug("About to enter background")

    def on_entered_background(self):
        LOG.debug("Entered background")

    def on_enter_foreground(self):
        LOG.debug("About to enter foreground")

    def on_entered_foreground(self):
        LOG.debug("Entered foreground")

    def get_player(self, player: Player = Player.P1):
        if player in self.memory.player:
            return self.memory.player[player]
        else:
            return None

    def set_player(self, creature: Creature, player: Player = Player.P1):
        self.memory.player[player] = creature

    def trigger_teleport(
        self, active: bool = True, player: Player = Player.P1
    ):
        self.memory.teleport_active[player] = active

    def is_teleport_active(self, player: Player = Player.P1):
        return self.memory.teleport_active[player]

    def trigger_dialog(self, active: bool = True, player=Player.P1):
        self.memory.dialog_active[player] = active

    def is_dialog_active(self, player: Player = Player.P1):
        return self.memory.dialog_active[player]

    def trigger_script(
        self, active: bool = True, player: Player = Player.P1
    ) -> None:
        self.memory.script_active[player] = active

    def is_script_active(self, player: Player = Player.P1) -> bool:
        return self.memory.script_active[player]

    def trigger_player_collision(
        self, active: bool = True, player: Player = Player.P1
    ) -> None:
        self.memory.player_collision_active[player] = active

    def is_player_collision_active(self, player: Player = Player.P1) -> bool:
        return self.memory.player_collision_active[player]

    @property
    def player(self):
        print("Deprecated access to player. Use 'get_player' instead!")
        return self.memory.player

    @player.setter
    def player(self, val):
        print("Deprecated access to player. Use 'get_player' instead!")
        self.memory.player = val

    @property
    def items(self):
        # raise TypeError()
        return self.memory.items

    @items.setter
    def items(self, val):
        raise TypeError(f"Items cannot be set to type {type(val)}")
        # self.memory.items = val

    @property
    def quests(self):
        return self.memory.quests

    @quests.setter
    def quests(self, val):
        self.memory.quests = val

    @property
    def dialog_active(self):
        print("dialog_active is deprecated; use 'is_dialog_active()' instead.")
        return self.memory.dialog_active

    @dialog_active.setter
    def dialog_active(self, val):
        print(
            "dialog_active is deprecated; use "
            "'trigger_dialog(active)' instead."
        )
        self.memory.dialog_active = val

    @property
    def game_state(self) -> GameState:
        return self.all_games[self.current_game]

    def get_view(self):
        return None
