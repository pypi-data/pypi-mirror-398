from __future__ import annotations

import logging
from typing import List, Optional

from ...maps.tilemap import Tilemap
from ...scripts.commands.give_item import CommandGiveItem
from ...scripts.commands.give_resource import CommandGiveResource
from ...scripts.commands.parallel import CommandParallel
from ...scripts.commands.present_item import CommandPresentItem
from ...scripts.commands.show_dialog import CommandShowDialog
from ...types.direction import Direction
from ...types.graphic_state import GraphicState
from ...types.nature import Nature
from ...types.object import ObjectType
from ..animated_sprite import AnimatedSprite
from ..dynamic import Dynamic

LOG = logging.getLogger(__name__)


class Container(Dynamic):
    def __init__(
        self,
        px: float,
        py: float,
        name: str = "Container",
        *,
        sprite_name: str = "",
        tilemap: Optional[Tilemap] = None,
        dyn_id: int = -1,
        graphic_state: GraphicState = GraphicState.CLOSED,
        item_name: str = "",
    ):
        if graphic_state not in [
            GraphicState.OPEN,
            GraphicState.CLOSED,
        ]:
            msg = (
                f"graphic_state of Container {name}{dyn_id} must be either "
                f"'open' or 'closed', but it is {graphic_state}"
            )
            raise ValueError(msg)
        super().__init__(
            px,
            py,
            name,
            tilemap=tilemap,
            sprite_name=sprite_name,
            dyn_id=dyn_id,
        )

        self.type = ObjectType.CONTAINER
        self.graphic_state = graphic_state
        self.closed: bool = self.graphic_state != GraphicState.OPEN

        self.item_name: str = item_name
        self.item = self.engine.get_item(item_name)
        self.solid_vs_dyn: bool = True
        self.solid_vs_map: bool = True
        self.visible: bool = True

        self.is_resource: bool = False
        self.amount: int = 1

        self._gs_map = {False: GraphicState.OPEN, True: GraphicState.CLOSED}

    def update(self, elapsed_time: float, target: Optional[Dynamic] = None):
        if self.visible:
            self.solid_vs_dyn = True
        else:
            self.solid_vs_dyn = False

        self.graphic_state = (
            GraphicState.CLOSED if self.closed else GraphicState.OPEN
        )

        self.sprite.update(
            elapsed_time, self.facing_direction, self.graphic_state
        )

    def draw_self(self, ox: float, oy: float, camera_name: str = "display"):
        if not self.visible:
            return

        self.sprite.draw_self(self.px - ox, self.py - oy, camera_name)

    def on_interaction(self, target: Dynamic, nature: Nature):
        if nature == Nature.SIGNAL:
            self.visible = True
            return True

        if nature == Nature.NO_SIGNAL:
            self.visible = False
            return True

        if not self.visible:
            return False

        if nature == Nature.TALK:
            if self.closed:
                if self.is_resource:
                    text = "You received "
                    if self.amount > 1:
                        text += f"{self.amount} {self.item.name}s!"
                    elif self.amount == 1:
                        text += f"one {self.item.name}!"
                    else:
                        text += "nothing. The chest was empty!"

                    if self.item_name == "coin":
                        cgr = CommandGiveResource(target, coins=self.amount)
                    elif self.item_name == "bomb_refill":
                        cgr = CommandGiveResource(target, bombs=self.amount)
                    elif self.item_name == "arrow_refill":
                        cgr = CommandGiveResource(target, arrows=self.amount)
                    elif self.item_name == "key":
                        cgr = CommandGiveResource(target, keys=self.amount)
                    else:
                        LOG.error(f"Invalid resource type: {self.item_name}")
                        return False

                    self.engine.script.add_command(
                        CommandParallel(
                            [
                                CommandShowDialog([text]),
                                CommandPresentItem(self.item_name, target),
                                cgr,
                            ],
                            CommandParallel.FIRST_COMPLETED,
                        ),
                        players=[target.get_player()],
                    )

                else:

                    self.engine.script.add_command(
                        CommandParallel(
                            [
                                CommandShowDialog(
                                    [f"You received {self.item.name}"],
                                ),
                                CommandPresentItem(self.item_name, target),
                                CommandGiveItem(self.item_name, target),
                            ],
                            CommandParallel.FIRST_COMPLETED,
                        ),
                        players=[target.get_player()],
                    )
                self.closed = False
                self.state_changed = True
                return True

        return False

    @staticmethod
    def load_from_tiled_object(
        obj, px, py, width, height, tilemap
    ) -> List[Container]:
        container = Container(
            px=px,
            py=py,
            name=obj.name,
            sprite_name=obj.get_string("sprite_name"),
            tilemap=tilemap,
            dyn_id=obj.object_id,
            graphic_state=GraphicState[
                obj.get_string("graphic_state", "closed").upper()
            ],
            item_name=obj.get_string("item_name"),
        )
        container.is_resource = obj.get_bool("is_resource", False)
        container.amount = obj.get_int("amount", 1)

        return [container]
