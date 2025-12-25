from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from .engine import MimaEngine
from .states.game_state import GameState
from .types.keys import Key as K
from .types.mode import Mode
from .types.nature import Nature
from .types.player import Player
from .view.scene import Scene


class MimaSceneEngine(MimaEngine):
    def __init__(
        self,
        init_file: str,
        config_path: str,
        default_config: Dict[str, Any],
        platform: str = "PC",
        caption: str = "MimaEngine",
    ):
        super().__init__(init_file, config_path, default_config, platform, caption)

        self.scene_stack: List[str] = []
        self._scenes: Dict[str, Scene] = {}
        self._current_scene: Scene

        self.save_timer_reset = 1.0
        self._save_timer = self.save_timer_reset
        # self.teleport_triggered: bool = False
        # self.dialog_active: bool = False

    def on_user_create(self):
        return True

    def on_user_update(self, elapsed_time: float):
        self.audio.update(elapsed_time)
        self._current_scene = self._scenes[self.scene_stack[-1]]

        # self._current_scene = self.mode.name.lower()

        self._save_timer -= elapsed_time
        if self._save_timer <= 0.0:
            self._save_timer += self.save_timer_reset
            if self._current_scene.autosave:
                for quest in self.quests:
                    for obj in self.scene.dynamics:
                        quest.on_interaction(self.scene.dynamics, obj, Nature.SAVE)
                    quest.save_state()
        if self.keys.new_key_press(K.SELECT):
            self.game_state.save_to_disk()

        self.scene.update(elapsed_time)

        return True

    def load_scene(self):
        self.scene_stack

    # def load_scene(self, map_name: str, px: float, py: float):
    #     type_string = (
    #         self.get_map(map_name).get_string("type", "local").upper()
    #     )
    #     if type_string == "WORLD":
    #         type_string = "WORLD_MAP"
    #     if type_string == "LOCAL":
    #         type_string = "LOCAL_MAP"
    #     mode = Mode[type_string]

    #     self.scene_stack.append(mode)
    #     self._scenes[self.scene_stack[-1]].load_scene()
    #     # self._scenes[self.scene_stack[-1]].change_map(map_name, px, py)
    #     # print(self.scene_stack)

    @property
    def scene(self) -> Scene:
        # return self._scenes[self._current_scene]
        return self._current_scene

    @property
    def previous_scene(self) -> Scene:
        return self._scenes[self.scene_stack[-2]]
