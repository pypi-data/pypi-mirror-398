import logging
import math
from typing import Any, Dict, Optional

from ..types.direction import Direction
from ..types.graphic_state import GraphicState

LOG = logging.getLogger(__name__)


class AnimatedSprite:
    engine = None
    sprite_sets = {}

    def __init__(
        self,
        # tileset_name: str,
        # image_name: str,
        sprite_name: str,
        graphic_state: GraphicState = GraphicState.STANDING,
        facing_direction: Direction = Direction.SOUTH,
    ):

        self.name = sprite_name
        self._last_direction: Direction = facing_direction
        self._last_graphic_state: GraphicState = graphic_state
        self.sprite_sheet = self.engine.assets.get_sprite_data(sprite_name)

        if self.name:
            data = self._get_data(
                self._last_graphic_state, self._last_direction
            )
            self._frame_index: int = 0
            self._timer: float = data["duration"][0]
            self._ox = data["ox"][0]
            self._oy = data["oy"][0]
            self._image_name = data["image"][0]
            self.width = data["width"][0]
            self.height = data["height"][0]
        else:
            self.width = self.engine.rtc.tile_width
            self.height = self.engine.rtc.tile_height
        # # TODO: Handle ""
        # if tileset_name and image_name and self._sprite_name:
        #     LOG.info(
        #         {
        #             "operation": "load sprite",
        #             "tileset": tileset_name,
        #             "image": image_name,
        #             "sprite": self._sprite_name,
        #         }
        #     )
        #     tileset = self.engine.assets.get_tileset(tileset_name)

        #     self.width = tileset.tile_width
        #     self.height = tileset.tile_height

        #     self._sprites: Dict[GraphicState, Dict[Direction, Dict[str, Any]]] = (
        #         self._load_sprites_from_tileset(tileset, self._sprite_name)
        #     )

        # else:
        #     LOG.debug(
        #         "Sprite information uncomplete. Tileset=%s, Image=%s, Sprite="
        #         "%s. Will continue without sprite.",
        #         tileset_name,
        #         image_name,
        #         self._sprite_name,
        #     )
        #     self.name = self._tileset_name = self._sprite_name = ""

    def update(
        self,
        elapsed_time: float,
        direction: Direction = Direction.SOUTH,
        graphic_state: GraphicState = GraphicState.STANDING,
    ):
        if not self.name:
            return

        data = self._get_data(graphic_state, direction)

        if (
            direction == self._last_direction
            and graphic_state == self._last_graphic_state
        ):
            # No changes, normal case
            self._timer -= elapsed_time
            if self._timer <= 0.0:
                self._frame_index = (self._frame_index + 1) % len(
                    data["duration"]
                )
                self._timer += data["duration"][self._frame_index]
                self._ox = data["ox"][self._frame_index]
                self._oy = data["oy"][self._frame_index]
                self._image_name = data["image"][self._frame_index]
                self.width = data["width"][self._frame_index]
                self.height = data["height"][self._frame_index]
        else:
            self._frame_index = 0
            # Something changed
            # if graphic_state != self._last_graphic_state:
            # State changed

            self._timer = data["duration"][0]
            self._ox = data["ox"][0]
            self._oy = data["oy"][0]
            self._image_name = data["image"][0]
            self.width = data["width"][0]
            self.height = data["height"][0]

        self._last_direction = direction
        self._last_graphic_state = graphic_state

    def draw_self(
        self,
        px: float,
        py: float,
        camera_name: str = "display",
        absolute_position: bool = False,
        draw_to_ui: bool = False,
    ):
        if not self.name:
            return

        if not absolute_position:
            px *= self.engine.rtc.tile_width
            py *= self.engine.rtc.tile_height
        px, py = math.floor(px), math.floor(py)

        self.engine.backend.draw_partial_sprite(
            px,
            py,
            self._image_name,
            self._ox * self.width,
            self._oy * self.height,
            self.width,
            self.height,
            camera_name,
            draw_to_ui=draw_to_ui,
        )

    def _load_sprites_from_tileset(self, tileset, sprite_name):
        if sprite_name in AnimatedSprite.sprite_sets:
            # Caching
            return AnimatedSprite.sprite_sets[sprite_name]

        sprites = {}

        for tile in tileset.tiles:
            if tile.sprite_name != sprite_name:
                continue

            if tile.animated:
                data = {"duration": [], "ox": [], "oy": []}
                for frame in tile._frames:
                    data["duration"].append(frame.duration)
                    data["ox"].append(frame.frame_id % tileset.columns)
                    data["oy"].append(frame.frame_id // tileset.columns)
            else:
                data = {
                    "duration": [1000],
                    "ox": [tile.tile_id % tileset.columns],
                    "oy": [tile.tile_id // tileset.columns],
                }

            sprites.setdefault(tile.graphic_state, {})
            sprites[tile.graphic_state][tile.facing_direction] = data
            LOG.debug(
                {
                    "operation": "add frames",
                    "image": self.name,
                    "sprite": sprite_name,
                    "graphic_state": tile.graphic_state.name,
                    "direction": tile.facing_direction.name,
                    "frame_data": data,
                }
            )

        AnimatedSprite.sprite_sets[sprite_name] = sprites
        return sprites
        # for tile in tileset.tiles
        # Check non-animated tiles if necessary

    def reset(self):
        self._frame_index = 0
        self._timer = 0.0

    def _get_data(self, graphic_state, direction):
        if graphic_state == GraphicState.DEFEATED:
            graphic_state = graphic_state.DEAD

        data = self.sprite_sheet.get(
            graphic_state, self.sprite_sheet.get(GraphicState.STANDING, {})
        )
        data = data.get(direction, data.get(Direction.SOUTH, {}))
        if not data:
            try:
                LOG.debug(
                    "Animation of sprite %s is empty for %s, %s ",
                    self.name,
                    graphic_state.name,
                    direction.name,
                )
            except Exception:
                # print(graphic_state, direction)
                LOG.exception(graphic_state, direction)
                raise
            data = {
                "ox": [0],
                "oy": [0],
                "duration": [1.0],
                "image": [""],
                "width": [0],
                "height": [0],
            }
        return data
