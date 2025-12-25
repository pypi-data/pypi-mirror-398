from __future__ import annotations

import math
from itertools import product
from typing import TYPE_CHECKING, Callable, Dict, List, Optional, Tuple

from ..maps.tilemap import Tilemap
from ..types.direction import Direction
from ..types.graphic_state import GraphicState, Until
from ..types.nature import Nature
from ..types.object import ObjectType
from ..types.tile_collision import TileCollision

if TYPE_CHECKING:
    # from .engine import MimaEngine
    from ..objects.dynamic import Dynamic
    from ..states.quest import Quest

    # from .view.view import View


def check_object_to_map_collision(
    elapsed_time: float,
    obj: Dynamic,
    tilemap: Tilemap,
    new_px: float,
    new_py: float,
    *,
    layer: int = 0,
    collision: TileCollision = TileCollision.TOP,
) -> Tuple[float, float]:
    left = new_px + obj.hitbox_px
    right = left + obj.hitbox_width
    top = obj.py + obj.hitbox_py
    bottom = top + obj.hitbox_height

    collided_with_map = False
    if obj.solid_vs_map:
        if collision_with_map(
            tilemap, left, right, top, bottom, layer, collision
        ):
            # On rare occasions, the object might be pushed towards
            # the wall, i.e. old and new pos are equal
            # Decide depending on the decimal part of the position
            # where to push the object
            if new_px == obj.px:
                decimal_dif = new_px - int(new_px)
                if abs(decimal_dif) > 0.5:
                    new_px += 0.0001
                else:
                    new_px -= 0.0001

            # Did the object move from right to left?
            if new_px < obj.px:
                new_px += int(left) + 1.0 - left
            else:
                new_px -= right - int(right) + 0.001

            obj.vx = 0
            collided_with_map = True
            if (
                obj.facing_direction in [Direction.WEST, Direction.EAST]
                and obj.can_push
            ):
                obj.lock_graphic_state(GraphicState.PUSHING, Until.NEXT_UPDATE)

        left = new_px + obj.hitbox_px
        right = left + obj.hitbox_width
        top = new_py + obj.hitbox_py
        bottom = top + obj.hitbox_height

        if collision_with_map(
            tilemap, left, right, top, bottom, layer, collision
        ):
            # See comment above
            if new_py == obj.py:
                decimal_dif = new_py - int(new_py)
                if abs(decimal_dif) > 0.5:
                    new_py += 0.0001
                else:
                    new_py -= 0.0001

            if new_py < obj.py:
                new_py += int(top) + 1.0 - top
            else:
                new_py -= bottom - int(bottom) + 0.001

            obj.vy = 0
            collided_with_map = True
            if (
                obj.facing_direction in [Direction.NORTH, Direction.SOUTH]
                and obj.can_push
            ):
                obj.lock_graphic_state(GraphicState.PUSHING, Until.NEXT_UPDATE)

        if obj.type == ObjectType.PROJECTILE and collided_with_map:
            obj.kill()

    return new_px, new_py


def collision_with_map(
    tilemap: Tilemap,
    left: float,
    right: float,
    top: float,
    bottom: float,
    layer: int = 0,
    collision: TileCollision = TileCollision.TOP,
) -> bool:
    if tilemap.is_solid(left, top, layer, collision):
        return True
    if tilemap.is_solid(left, bottom, layer, collision):
        return True
    if tilemap.is_solid(right, top, layer, collision):
        return True
    if tilemap.is_solid(right, bottom, layer, collision):
        return True

    return False


def check_object_to_object_collision(
    obj: Dynamic,
    new_px: float,
    new_py: float,
    other: Dynamic,
    deal_damage: Optional[Callable[Dynamic, Dynamic]] = None,
    quests: Optional[List[Quest]] = None,
) -> Tuple[float, float]:
    quests = quests if quests is not None else []
    deal_damage = deal_damage if deal_damage is not None else lambda x, y: None

    pxys = {}
    pxys["left1"] = new_px + obj.hitbox_px
    pxys["right1"] = pxys["left1"] + obj.hitbox_width
    pxys["top1"] = obj.py + obj.hitbox_py
    pxys["bottom1"] = pxys["top1"] + obj.hitbox_height

    pxys["left2"] = other.px + other.hitbox_px
    pxys["right2"] = pxys["left2"] + other.hitbox_width
    pxys["top2"] = other.py + other.hitbox_py
    pxys["bottom2"] = pxys["top2"] + other.hitbox_height

    if obj.solid_vs_dyn and other.solid_vs_dyn:  # and obj.moves_on_collision:
        new_px, new_py = _check_solid_objects(obj, other, new_px, new_py, pxys)

    else:
        if obj.type == ObjectType.PLAYER:
            _check_player_with_non_solid(obj, other, pxys, quests)

        else:
            _check_non_solid_objects(obj, other, pxys, deal_damage)

    return new_px, new_py


def _check_solid_objects(
    obj: Dynamic,
    other: Dynamic,
    new_px: float,
    new_py: float,
    pxys: Dict[str, float],
) -> None:
    collided_with_dyn = False
    if collision_with_dyn(**pxys):
        collided_with_dyn = True
        if pxys["left1"] < pxys["left2"]:
            new_px -= pxys["right1"] - pxys["left2"] + 0.001
        else:
            new_px += pxys["right2"] - pxys["left1"] + 0.001

    pxys["left1"] = new_px + obj.hitbox_px
    pxys["right1"] = pxys["left1"] + obj.hitbox_width
    pxys["top1"] = new_py + obj.hitbox_py
    pxys["bottom1"] = pxys["top1"] + obj.hitbox_height

    if collision_with_dyn(**pxys):
        collided_with_dyn = True
        if pxys["top1"] < pxys["top2"]:
            new_py -= pxys["bottom1"] - pxys["top2"] + 0.001
        else:
            new_py += pxys["bottom2"] - pxys["top1"] + 0.001

    if collided_with_dyn:
        # print(f"Collision: {obj.get_player()} -> {other.dyn_id}")
        other.on_interaction(obj, Nature.WALK)

    return new_px, new_py


def _check_player_with_non_solid(
    obj: Dynamic, other: Dynamic, pxys: Dict[str, float], quests: List[Quest]
):
    if collision_with_dyn(**pxys):
        for quest in quests:
            if quest.on_interaction(other, Nature.WALK, obj.get_player()):
                break
        obj.tilemap.on_interaction(other, Nature.WALK)
        other.on_interaction(obj, Nature.WALK)


def _check_non_solid_objects(
    obj: Dynamic,
    other: Dynamic,
    pxys: Dict[str, float],
    deal_damage: Callable[Dynamic, Dynamic],
):
    if collision_with_dyn(**pxys):
        if obj.type == ObjectType.PROJECTILE:
            if other.alignment != obj.alignment:
                # We know object is a projectile
                if other.attackable and not other.invincible:
                    deal_damage(obj, other)
                else:
                    other.on_interaction(obj, Nature.WALK)
        else:
            other.on_interaction(obj, Nature.WALK)


def collision_with_dyn(
    left1: float,
    right1: float,
    top1: float,
    bottom1: float,
    left2: float,
    right2: float,
    top2: float,
    bottom2: float,
) -> bool:
    if left1 < right2 and right1 > left2 and top1 < bottom2 and bottom1 > top2:
        return True

    return False


def add_to_collision_chunk(
    collision_chunks: Dict[int, List[Dynamic]],
    obj: Dynamic,
    chunk_size: int,
    chunks_per_row: int,
) -> List[int]:
    chunk_ids = []
    # chidx = _chunk_index(obj.px, obj.py, chunk_size, chunks_per_row)
    # collision_chunks.setdefault(chidx, [])

    # if obj not in collision_chunks[chidx]:
    #     if obj.get_player().value > 0:
    #         collision_chunks[chidx].insert(0, obj)
    #     else:
    #         collision_chunks[chidx].append(obj)
    centerx = obj.px + (obj.hitbox_px + obj.hitbox_width) / 2
    centery = obj.py + (obj.hitbox_py + obj.hitbox_height) / 2
    # chid = _test_chunk_position(
    #     collision_chunks, obj, centerx, centery, chunk_size, chunks_per_row
    # )
    offsets = [[0, 0]] + [
        list(p) for p in product([-1, 0, 1], repeat=2) if p != (0, 0)
    ]
    for x, y in offsets:
        chunk_ids.append(
            _test_chunk_position(
                collision_chunks,
                obj,
                centerx + x,
                centery + y,
                chunk_size,
                chunks_per_row,
            )
        )
    chunk_ids = list(dict.fromkeys(chunk_ids))
    # chid_right = _test_chunk_position(
    #     collision_chunks, obj, obj.px + 1, obj.py, chunk_size, chunks_per_row
    # )

    # chid_bottom = _test_chunk_position(
    #     collision_chunks, obj, obj.px, obj.py + 1, chunk_size, chunks_per_row
    # )

    # chunk_ids.append(chid)
    # if chid != chid_right:
    #     chunk_ids.append(chid_right)
    # if chid != chid_bottom:
    #     chunk_ids.append(chid_bottom)
    # if chid != chid_right and chid != chid_bottom:
    #     chunk_ids.append(
    #         _test_chunk_position(
    #             collision_chunks,
    #             obj,
    #             obj.px + 1,
    #             obj.py + 1,
    #             chunk_size,
    #             chunks_per_row,
    #         )
    #     )

    for chid in obj.chunks:
        if (
            chid not in chunk_ids
            and chid in collision_chunks
            and obj in collision_chunks[chid]
        ):
            collision_chunks[chid].remove(obj)
    return chunk_ids


def _test_chunk_position(
    collision_chunks, obj, px, py, chunk_size, chunks_per_row
):
    chidx = _chunk_index(px, py, chunk_size, chunks_per_row)
    collision_chunks.setdefault(chidx, [])

    if obj not in collision_chunks[chidx]:
        if obj.get_player().value > 0:
            collision_chunks[chidx].insert(0, obj)
        else:
            collision_chunks[chidx].append(obj)
    return chidx


def _chunk_index(px, py, chunk_size, chunks_per_row):
    hc = chunk_size // 2
    return math.floor((px + hc) / chunk_size) + chunks_per_row * math.floor(
        (py + hc) / chunk_size
    )
