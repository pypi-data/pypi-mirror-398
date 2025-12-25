from __future__ import annotations

import logging
from typing import List, Optional

from ...maps.tilemap import Tilemap
from ...scripts.commands.change_map import CommandChangeMap
from ...scripts.commands.move_map import CommandMoveMap
from ...scripts.commands.parallel import CommandParallel
from ...scripts.commands.screen_fade import CommandScreenFade
from ...scripts.commands.serial import CommandSerial
from ...scripts.commands.set_facing_direction import CommandSetFacingDirection
from ...types.direction import Direction
from ...types.graphic_state import GraphicState
from ...types.nature import Nature
from ...types.object import ObjectType
from ...types.player import Player
from ..animated_sprite import AnimatedSprite
from ..dynamic import Dynamic

LOG = logging.getLogger(__name__)


class Teleport(Dynamic):
    def __init__(
        self,
        px: float,
        py: float,
        name="Teleport",
        *,
        sprite_name: str = "str",
        tilemap: Optional[Tilemap] = None,
        dyn_id: int = -1,
        facing_direction: Direction,
        graphic_state: GraphicState,
        dst_map_name: str,
        dst_px: float,
        dst_py: float,
        direction: Direction,
        invert_exit_direction: bool = False,
        relative: bool = False,
        sliding: bool = False,
        vertical: bool = False,
    ):
        super().__init__(
            px,
            py,
            name,
            sprite_name=sprite_name,
            tilemap=tilemap,
            dyn_id=dyn_id,
        )

        # self.sprite = AnimatedSprite(
        #     tileset_name,
        #     image_name,
        #     sprite_name,
        #     graphic_state,
        #     facing_direction,
        # )

        self.type = ObjectType.TELEPORT
        self.graphic_state = graphic_state
        self.facing_direction = facing_direction
        self.solid_vs_dyn = False
        self.solid_vs_map = False

        self.dst_px: float = dst_px
        self.dst_py: float = dst_py
        self.dst_map_name: str = dst_map_name
        self.has_sprite = self.sprite.name != ""
        self.teleport_direction: Direction = direction

        self.visible = True
        self.invert_exit_direction = invert_exit_direction
        self.relative = relative
        self.sliding = sliding
        self.vertical = vertical
        self.triggered = False
        self.sfx_on_trigger: str = ""

    def update(self, elapsed_time: float, target: Optional[Dynamic] = None):
        self.triggered = False
        self.sprite.update(
            elapsed_time, self.facing_direction, self.graphic_state
        )

    def on_interaction(self, target: Dynamic, nature: Nature):
        if nature == Nature.SIGNAL:
            self.visible = True
            return True
        if nature == Nature.NO_SIGNAL:
            self.visible = False
            return True

        if self.has_sprite and not self.visible:
            return False

        pt = target.get_player()
        if (
            nature == Nature.WALK
            and pt != Player.P0
            and not self.engine.is_teleport_active(pt)
        ):
            self.engine.trigger_teleport(True, pt)
            dst_px = self.dst_px
            dst_py = self.dst_py
            dst_vx = 0
            dst_vy = 0

            dst_vx, dst_vy = Direction.to_velocity(self.teleport_direction)
            # self.sliding = False
            if self.sliding:
                if dst_vx != 0:
                    dst_py = target.py
                elif dst_vy != 0:
                    dst_px = target.px

            #     self.engine.script.add_command(
            #         CommandMoveMap(
            #             new_map_name=self.dst_map_name,
            #             obj=target,
            #             target_px=dst_px,
            #             target_py=dst_py,
            #             vx=dst_vx,
            #             vy=dst_vy,
            #             players=[pt],
            #         )
            #     )
            # else:
            if self.triggered:
                return False

            new_direction = target.facing_direction
            if self.invert_exit_direction:
                new_direction = Direction(
                    (target.facing_direction.value + 2) % 4
                )

            cmd = CommandSerial(
                [
                    CommandScreenFade(),
                    CommandParallel(
                        [
                            CommandChangeMap(
                                self.dst_map_name, dst_px, dst_py
                            ),
                            CommandSetFacingDirection(target, new_direction),
                            CommandScreenFade(
                                fadein=True, map_name=self.dst_map_name
                            ),
                        ]
                    ),
                ]
            )
            cmd.set_players([pt])
            self.engine.script.add_command(cmd)

            if self.sfx_on_trigger:
                self.engine.audio.play_sound(self.sfx_on_trigger)

            self.triggered = True
            return True

        return False

    def draw_self(self, ox: float, oy: float, camera_name: str = "display"):
        if not self.visible:
            self.engine.backend.draw_circle(
                (self.px + 0.5 - ox) * self.engine.rtc.tile_width,
                (self.py + 0.5 - oy) * self.engine.rtc.tile_height,
                0.5 * self.engine.rtc.tile_width,
                self.engine.rtc.color_red,
                camera_name,
            )
            return

        if self.has_sprite:
            self.sprite.draw_self(self.px - ox, self.py - oy, camera_name)

    @staticmethod
    def load_from_tiled_object(
        obj, px, py, width, height, tilemap
    ) -> List[Teleport]:
        sprite_name = obj.get_string("sprite_name")
        graphic_state = GraphicState[
            obj.get_string("graphic_state", "closed").upper()
        ]
        facing_direction = Direction[
            obj.get_string("facing_direction", "south").upper()
        ]
        target_map = obj.get_string("target_map", "map1_c1")
        invert_exit_direction = obj.get_bool("invert_exit_direction")
        relative = obj.get_bool("relative", False)
        sliding = obj.get_bool("sliding", False)
        vertical = obj.get_bool("vertical", False)
        layer = obj.get_int("layer", 1)
        target_px = obj.get_float("target_px")
        target_py = obj.get_float("target_py")
        direction = Direction[obj.get_string("direction", "south").upper()]
        teleports = []
        if width > height and int(width) > 1:
            num_horizontal = int(width)
            for idx in range(num_horizontal):
                from_px = px + idx
                from_py = py
                to_px = target_px + idx
                to_py = target_py

                LOG.debug(
                    "Adding a teleport at (%f, %f) to map %s (%f, %f).",
                    from_px,
                    from_py,
                    target_map,
                    to_px,
                    to_py,
                )
                teleports.append(
                    Teleport(
                        px=from_px,
                        py=from_py,
                        sprite_name=sprite_name,
                        graphic_state=graphic_state,
                        facing_direction=facing_direction,
                        dst_map_name=target_map,
                        dst_px=to_px,
                        dst_py=to_py,
                        direction=direction,
                        invert_exit_direction=invert_exit_direction,
                        relative=relative,
                        sliding=sliding,
                        vertical=False,
                        tilemap=tilemap,
                        dyn_id=obj.object_id,
                        name=obj.name,
                    )
                )
                teleports[-1].layer = layer
        elif height > width and int(height) > 1:
            num_vertical = int(height)
            for idx in range(num_vertical):
                from_px = px
                from_py = py + idx
                to_px = target_px
                to_py = target_py if relative else from_py

                LOG.debug(
                    "Adding a teleport at (%f, %f) to map %s (%f, %f).",
                    from_px,
                    from_py,
                    target_map,
                    to_px,
                    to_py,
                )
                teleports.append(
                    Teleport(
                        px=from_px,
                        py=from_py,
                        sprite_name=sprite_name,
                        graphic_state=graphic_state,
                        facing_direction=facing_direction,
                        dst_map_name=target_map,
                        dst_px=to_px,
                        dst_py=to_py,
                        direction=direction,
                        invert_exit_direction=invert_exit_direction,
                        relative=relative,
                        sliding=sliding,
                        vertical=True,
                        tilemap=tilemap,
                        dyn_id=obj.object_id,
                        name=obj.name,
                    )
                )
                teleports[-1].layer = layer
        else:
            LOG.debug(
                "Adding a teleport at (%f, %f) to map %s (%f, %f).",
                px,
                py,
                target_map,
                target_px,
                target_py,
            )
            teleports.append(
                Teleport(
                    px=px,
                    py=py,
                    sprite_name=sprite_name,
                    graphic_state=graphic_state,
                    facing_direction=facing_direction,
                    dst_map_name=target_map,
                    dst_px=target_px,
                    dst_py=target_py,
                    direction=direction,
                    invert_exit_direction=invert_exit_direction,
                    relative=relative,
                    sliding=sliding,
                    vertical=vertical,
                    tilemap=tilemap,
                    dyn_id=obj.object_id,
                    name=obj.name,
                )
            )
            teleports[-1].sfx_on_trigger = obj.get_string("sfx_name")
            teleports[-1].layer = layer

        return teleports
