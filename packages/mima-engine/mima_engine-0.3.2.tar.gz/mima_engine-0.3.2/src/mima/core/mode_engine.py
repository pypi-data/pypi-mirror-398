import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from ..states.game_state import GameState
from ..types.keys import Key as K
from ..types.mode import Mode
from ..types.nature import Nature
from ..types.player import Player
from ..view.mima_mode import MimaMode
from .engine import MimaEngine

# from .view.mima_scene import MimaScene
LOG = logging.getLogger(__name__)


class MimaModeEngine(MimaEngine):
    def __init__(
        self,
        init_file: str,
        config_path: str,
        default_config: Dict[str, Any],
        platform="PC",
        caption: str = "MimaEngine",
    ):
        super().__init__(
            init_file, config_path, default_config, platform, caption
        )

        self.modes: Dict[Mode, MimaMode] = {}
        self.mode: Optional[MimaMode] = None

        self.mode_stack: List[Mode] = []

        self.draw_chunks: bool = False
        self.draw_chunk_info: bool = False
        self.draw_dyn_ids: bool = False
        self.disable_filter: bool = False
        self._timer = 1.0

    def on_user_create(self):
        # change_mode(Mode.LOADING)
        # TODO add example modes
        return True

    def on_user_update(self, elapsed_time: float):
        self.audio.update(elapsed_time)

        # print("Update start")

        if not self.mode.update(elapsed_time):
            LOG.critical(f"Update of mode {self.mode} failed.")
            return False
        self._timer -= elapsed_time
        if self._timer <= 0.0:
            self._timer += 1.0
            LOG.debug(
                f"Updated {self.mode} (Current Stack:"
                f"{[m.name for m in self.mode_stack]})"
            )
        # print("Update end")
        return True

    def change_mode(self, mode: Mode):
        if mode in self.mode_stack:
            self.mode_stack.remove(mode)
        self.mode_stack.append(mode)
        if self.mode is not None:
            self.mode.unload()
        self.mode = self.modes[mode]
        self.mode.load()

    def return_mode(self):
        LOG.debug(
            "Returning to previous mode. Stack: %s", str(self.mode_stack)
        )
        self.mode_stack.pop()
        self.mode = self.modes[self.mode_stack[-1]]
        self.mode.load()

    def get_view(self):
        return self.mode
