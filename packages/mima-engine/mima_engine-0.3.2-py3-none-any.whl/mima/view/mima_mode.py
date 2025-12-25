from __future__ import annotations

import logging
import math
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from ..core.collision import (
    _chunk_index,
    add_to_collision_chunk,
    check_object_to_map_collision,
    check_object_to_object_collision,
)
from ..objects.effects.debug_box import DynamicDebugBox, StaticDebugBox
from ..objects.loader import ObjectLoader
from ..types.nature import Nature
from ..types.player import Player
from ..types.position import Position
from ..types.tile_collision import TileCollision
from ..util.colors import (
    TRANS_LIGHT_CYAN,
    TRANS_LIGHT_GREEN,
    TRANS_LIGHT_PURPLE,
    TRANS_LIGHT_YELLOW,
)
from .mima_scene import MimaScene
from .mima_view import MimaView
from .mima_window import MimaWindow

if TYPE_CHECKING:
    from ..maps.tilemap import Tilemap
    from ..objects.dynamic import Dynamic
    from ..objects.projectile import Projectile
    from ..types.window import Window

LOG = logging.getLogger(__name__)


class MimaMode(MimaView):
    """Base class for game modes"""

    def __init__(self) -> None:
        self.scenes: Dict[Player, MimaScene] = {}
        self.dynamics: Dict[str, List[Dynamic]] = {}
        self.projectiles: Dict[str, List[Projectile]] = {}
        self.effects: Dict[str, List[Projectile]] = {}
        self.maps: Dict[Player, Tilemap] = {}
        self.players_on_map: Dict[str, List[Player]] = {}
        self.dialog_to_show: Dict[Player, List[str]] = {}
        self.collision_targets: Dict[str, Dict[int, List[Dynamic]]] = {}
        self.colliders: Dict[str, Dict[int, List[Dynamic]]] = {}
        self.chunk_size = 4

        self._clear_color = self.engine.rtc.color_black
        self._loader = ObjectLoader({}, {})
        self.tile_collision = TileCollision.TOP

    def load(self) -> bool:
        """Load the scenes for this mode.

        Overwrite this if needed!
        """
        self.scenes[Player.P1] = MimaScene(Player.P1, Position.CENTER)
        self.populate_scenes(MimaWindow)

        return True

    def unload(self) -> None:
        pass

    def update(self, elapsed_time: float) -> bool:
        self.housekeeping(elapsed_time)
        self.handle_user_input()

        self.update_maps(elapsed_time)
        self.update_objects(elapsed_time)
        self.update_scenes(elapsed_time)

        self.engine.cameras = [s.camera.name for s in self.scenes.values()]

        self.draw_map_and_objects()
        if not self.engine.disable_filter:
            self.engine.backend.apply_filter("all")

        self.draw_scenes()

        self.display_dialog()

        return True

    def get_camera_name(self, player: Player = Player.P1):
        return self.scenes[player].camera.name

    def unload_map(
        self, player: Player = Player.P1, player_only: bool = False
    ) -> None:
        p_obj = self.engine.memory.player[player]
        map_name = p_obj.tilemap.name

        if player in self.players_on_map[map_name]:
            self.players_on_map[map_name].remove(player)

        if p_obj in self.dynamics[map_name]:
            # Is not the case on Game Over
            self.dynamics[map_name].remove(p_obj)
        self.maps[player] = None

        if not player_only and not self.players_on_map[map_name]:
            # No more players on the map
            for obj in self.dynamics[map_name]:
                obj.kill()
            for obj in self.projectiles[map_name] + self.effects[map_name]:
                obj.cancel()

            del self.players_on_map[map_name]
            del self.dynamics[map_name]
            del self.projectiles[map_name]
            del self.effects[map_name]
            self._unload_collision_chunks(map_name)
        else:
            for chid in p_obj.chunks:
                if p_obj in self.collision_targets[map_name][chid]:
                    self.collision_targets[map_name][chid].remove(p_obj)

    def prepare_object_lists(
        self,
        map_name: str,
        player: Player = Player.P1,
        p_obj: Optional[Dynamic] = None,
    ):
        self.maps[player] = self.engine.assets.get_map(map_name)
        self.players_on_map[map_name] = [player]
        self.dynamics[map_name] = []
        self.projectiles[map_name] = []
        self.effects[map_name] = []

        if p_obj is not None:
            self.dynamics[map_name].append(p_obj)

    def load_map(
        self, map_name: str, px: float, py: float, player: Player = Player.P1
    ) -> None:
        p_obj = self.engine.get_player(player)
        p_obj.stop_shining()
        p_obj.on_exit_map()

        if map_name not in self.players_on_map:
            # Map not loaded
            self.prepare_object_lists(map_name, player, p_obj)

            self._loader.populate_dynamics(
                self.maps[player], self.dynamics[map_name]
            )

            for quest in self.engine.memory.quests:
                quest.populate_dynamics(self.dynamics[map_name], map_name)
            self._load_collision_targets(map_name)
        else:
            # Map already loaded
            self.maps[player] = self.engine.assets.get_map(map_name)
            if player not in self.players_on_map[map_name]:
                self.players_on_map[map_name].append(player)
            if p_obj not in self.dynamics[map_name]:
                idx = len(self.players_on_map[map_name]) - 1
                self.dynamics[map_name].insert(idx, p_obj)

        p_obj.tilemap = self.maps[player]
        p_obj.px = px
        p_obj.py = py
        p_obj.on_enter_map()
        self.engine.memory.last_spawn_px[player] = px
        self.engine.memory.last_spawn_py[player] = py

    def _unload_collision_chunks(self, map_name):
        del self.collision_targets[map_name]
        del self.colliders[map_name]

    def _load_collision_targets(self, map_name):
        self.collision_targets[map_name] = {}
        tilemap = self.engine.get_map(map_name)
        chunks_per_row = math.ceil(tilemap.width / self.chunk_size) + 1

        for obj in self.dynamics[map_name]:
            if obj.moves_on_collision:
                continue
            else:
                # self.collision_targets[map_name]
                obj.chunks = add_to_collision_chunk(
                    self.collision_targets[map_name],
                    obj,
                    self.chunk_size,
                    chunks_per_row,
                )
                if self.engine.draw_chunk_info:
                    self.add_effect(
                        DynamicDebugBox(obj, n_frames=-1), map_name
                    )

    def handle_user_input(self):
        for player, scene in self.scenes.items():
            scene.handle_user_input()

    def housekeeping(self, elapsed_time: float) -> None:
        self.engine.script.process_command(elapsed_time)
        self.delete_redundant_objects()
        self.save_to_game_state()

        self.engine.backend.clear()

    def save_to_game_state(self):
        for quest in self.engine.memory.quests:
            for map_name in self.players_on_map:
                for obj in self.dynamics[map_name]:
                    try:
                        quest.on_interaction(obj, Nature.SAVE, obj.player)
                    except Exception:
                        if quest is not None and hasattr(quest, "name"):
                            msg = (
                                f"Error for quest {quest.name} "
                                f"({type(quest)}) while interacting with "
                            )
                            if obj is None:
                                msg += "None-object."
                            else:
                                msg += f"object {obj.name} ({obj.dyn_id})"
                        else:
                            msg = (
                                "Trying to interact with a quest that is None"
                            )

                        LOG.exception(msg)
                        raise

                quest.save_state()

    def delete_redundant_objects(self):
        # TODO Handle player game over
        # Find and erase redundant dynamics
        for map_name in self.players_on_map:
            d2rm = [d for d in self.dynamics[map_name] if d.redundant]
            for dyn in d2rm:
                for quest in self.engine.quests:
                    quest.on_interaction(dyn, Nature.KILLED, Player.P0)
                dyn.on_death()
                for chid in dyn.chunks:
                    self.collision_targets[map_name][chid].remove(dyn)
                self.dynamics[map_name].remove(dyn)

            # Find and erase redundant projectiles
            p2rm = [p for p in self.projectiles[map_name] if p.redundant]
            for pro in p2rm:
                pro.on_death()
                for chid in pro.chunks:
                    self.collision_targets[map_name][chid].remove(pro)
                self.projectiles[map_name].remove(pro)

            # Find and erase redundant effects
            e2rm = [e for e in self.effects[map_name] if e.redundant]
            for eff in e2rm:
                eff.on_death()
                self.effects[map_name].remove(eff)

        # Find and erase completed quests
        q2rm = [q for q in self.engine.quests if q.completed]
        for quest in q2rm:
            self.engine.quests.remove(quest)

    def update_maps(self, elapsed_time: float) -> None:
        for tmap in list(set(self.maps.values())):
            if tmap is not None:
                tmap.trigger_new_frame()
        for tmap in list(set(self.maps.values())):
            if tmap is not None:
                tmap.update(elapsed_time)

    def update_objects(self, elapsed_time: float) -> None:
        self.update_dynamics(elapsed_time)
        # print(collision_lists)
        self.handle_collisions(elapsed_time)
        self.update_effects(elapsed_time)

    def update_dynamics(self, elapsed_time):
        colors = [
            [TRANS_LIGHT_YELLOW, TRANS_LIGHT_GREEN],
            [TRANS_LIGHT_CYAN, TRANS_LIGHT_PURPLE],
        ]
        for map_name, players in self.players_on_map.items():
            # if not players:
            #     continue
            # self.colliders[map_name] = {}
            tilemap = self.engine.get_map(map_name)
            chunks_per_row = math.ceil(tilemap.width / self.chunk_size) + 1
            if self.engine.draw_chunks:
                for py in range(
                    -self.chunk_size // 2,
                    tilemap.height + self.chunk_size // 2,
                    self.chunk_size,
                ):
                    for px in range(
                        -self.chunk_size // 2,
                        tilemap.width + self.chunk_size // 2,
                        self.chunk_size,
                    ):
                        chidx = _chunk_index(
                            px, py, self.chunk_size, chunks_per_row
                        )
                        # collision_lists[map_name][chidx] = []
                        self.add_effect(
                            StaticDebugBox(
                                px,
                                py,
                                self.chunk_size,
                                self.chunk_size,
                                colors[(py // self.chunk_size) % 2][
                                    (px // self.chunk_size) % 2
                                ],
                                ids=[chidx],
                            ),
                            map_name,
                        )
            # print((py // chunk_size) % 2, (px // chunk_size) % 2)
            self.colliders[map_name] = []
            for obj in self.dynamics[map_name] + self.projectiles[map_name]:
                if obj.occupied:
                    continue
                target = self._determine_target(obj, players)
                # if obj.update_skippable and dist_to_target > max_dist:
                #      continue

                self._update_velocity_z(obj, elapsed_time)
                obj.update(elapsed_time, target)
                self._update_position_z(obj, elapsed_time)

                if obj.moves_on_collision:  # or dist_to_target < max_dist:
                    obj.chunks = add_to_collision_chunk(
                        self.collision_targets[map_name],
                        obj,
                        self.chunk_size,
                        chunks_per_row,
                    )
                    self.colliders[map_name].append(obj)

                if self.engine.draw_chunk_info:
                    self.add_effect(DynamicDebugBox(obj), map_name)

        # return collision_lists

    def _determine_target(self, obj, players) -> Dynamic:
        players = [
            p for p in players if not self.engine.get_player(p).occupied
        ]
        if not players:
            return None
        dists = [
            [
                p,
                abs(obj.px - self.engine.memory.player[p].px)
                + abs(obj.py - self.engine.memory.player[p].py),
            ]
            for p in players
        ]
        dists.sort(key=lambda x: x[1])

        if len(players) > 1:
            target = self.engine.memory.player[dists[0][0]]
        else:
            target = self.engine.memory.player[players[0]]

        return target  # , skip

    def _update_velocity_z(self, obj: Dynamic, elapsed_time: float) -> None:
        if obj.pz > 0.0:
            obj.vz -= obj.attributes.gravity_vz * elapsed_time
        # else:
        # obj.vz = 0.0

    def _update_position_z(self, obj: Dynamic, elapsed_time: float) -> None:
        if obj.gravity:
            obj.pz = obj.pz + obj.vz * elapsed_time
            if obj.pz <= 0.0:
                obj.pz = 0.0
                obj.vz = 0.0

    def handle_collisions(self, elapsed_time: float) -> None:
        screen_width = (
            self.engine.backend.render_width // self.engine.rtc.tile_width
        )
        screen_height = (
            self.engine.backend.render_height // self.engine.rtc.tile_height
        )
        max_dist = screen_width + screen_height

        for map_name, players in self.players_on_map.items():
            # print(f"Collisions for {map_name}: {self.colliders[map_name]}")
            for obj in self.colliders[map_name]:
                if obj.occupied:
                    continue
                objects = []
                for chid in obj.chunks:
                    objects.extend(self.collision_targets[map_name][chid])
                objects = list(set(objects))
                objects.remove(obj)
                objects.insert(0, obj)

                if self._check_collision_skippable(obj, players, max_dist):
                    continue

                new_px, new_py = self.update_position(obj, elapsed_time)
                new_px, new_py = check_object_to_map_collision(
                    elapsed_time,
                    obj,
                    self.maps[self.players_on_map[map_name][0]],
                    new_px,
                    new_py,
                    collision=self.tile_collision,
                )
                if self.check_tile_properties(obj, map_name, new_px, new_py):
                    # If true, something happened to the object
                    continue
                if len(objects) > 1:  # and obj.moves_on_collision:
                    for other in objects:
                        if other == obj:
                            continue
                        args = [
                            obj,
                            new_px,
                            new_py,
                            other,
                            self.deal_damage,
                            self.engine.memory.quests,
                        ]
                        if self._probe_p2p_collision(obj, other):
                            new2_px, new2_py = (
                                check_object_to_object_collision(*args)
                            )

                            if new2_px == new_px and new2_py == new_py:
                                # No change = no collision
                                self.engine.trigger_player_collision(
                                    True, obj.player
                                )
                        else:
                            new_px, new_py = check_object_to_object_collision(
                                *args
                            )
                obj.px = new_px
                obj.py = new_py

    def _probe_p2p_collision(self, obj, other):
        return (
            obj.player.value > 0
            and other.player.value > 0
            and (
                not self.engine.is_player_collision_active(obj.player)
                or not self.engine.is_player_collision_active(other.player)
            )
        )

    def update_position(self, obj: Dynamic, elapsed_time: float):
        vx, vy = min(1, max(-1, obj.vx)), min(1, max(-1, obj.vy))

        # Diagonal movement
        if obj.vx != 0 and obj.vy != 0:
            vx, vy = vx * 0.707, vy * 0.707

        obj.real_vx = (
            vx
            if vx == obj.real_vx
            else calculate(obj, vx, obj.real_vx, elapsed_time)
        )
        obj.real_vy = (
            vy
            if vy == obj.real_vy
            else calculate(obj, vy, obj.real_vy, elapsed_time)
        )

        new_px = (
            obj.px
            + obj.real_vx * obj.speed * obj.attributes.speed_mod * elapsed_time
        )
        new_py = (
            obj.py
            + obj.real_vy * obj.speed * obj.attributes.speed_mod * elapsed_time
        )

        return new_px, new_py

    def _check_collision_skippable(self, obj, players, max_dist) -> bool:
        # if not obj.moves_on_collision:
        #     return True
        # dists = [
        #     [
        #         p,
        #         abs(obj.px - self.engine.memory.player[p].px)
        #         + abs(obj.py - self.engine.memory.player[p].py),
        #     ]
        #     for p in players
        # ]
        # dists.sort(key=lambda x: x[1])

        # if obj.offscreen_collision_skippable and dists[0][1] > max_dist:
        #     return True

        return False

    def check_tile_properties(self, obj, map_name, new_px, new_py):
        return False

    def update_effects(self, elapsed_time: float) -> None:
        for map_name in self.players_on_map:
            for effect in self.effects[map_name]:
                effect.update(elapsed_time)
                effect.px, effect.py = self.update_position(
                    effect, elapsed_time
                )

    def update_scenes(self, elapsed_time: float) -> None:
        for player, scene in self.scenes.items():
            if self.maps[player] is None:
                map_width = map_height = 0
            else:
                map_width = self.maps[player].width
                map_height = self.maps[player].height

            scene.update(
                elapsed_time,
                target=self.engine.get_player(player),
                map_width=map_width,
                map_height=map_height,
            )

    def add_dynamic(self, dynamic: Dynamic, map_name: str):
        self.dynamics[map_name].append(dynamic)
        if (
            map_name in self.collision_targets
            and not dynamic.moves_on_collision
        ):
            dynamic.chunks = add_to_collision_chunk(
                self.collision_targets[map_name],
                dynamic,
                self.chunk_size,
                _chunks_per_row(
                    self.chunk_size, self.engine.get_map(map_name).width
                ),
            )

    def add_projectile(self, projectile: Projectile, map_name: str):
        self.projectiles[map_name].append(projectile)

    def add_effect(self, projectile: Projectile, map_name: str):
        self.effects[map_name].append(projectile)

    def draw_map_and_objects(self):
        # print(self.dynamics)
        for player, scene in self.scenes.items():
            tmap = self.maps[player]
            if tmap is None:
                continue

            scene.draw_map_and_objects(
                player,
                scene.camera,
                tmap,
                self.dynamics[tmap.name],
                self.projectiles[tmap.name],
                self.effects[tmap.name],
            )

    def draw_scenes(self):
        for scene in self.scenes.values():
            scene.draw_ui()
            scene.draw_camera_border()

    def deal_damage(self, aggressor: Projectile, victim: Dynamic) -> None:
        pass

    def show_dialog(self, lines: List[str], player: Player):
        if player == Player.P0:
            for p in self.scenes:
                self.dialog_to_show[p] = lines
                self.engine.trigger_dialog(True, p)
        else:
            self.dialog_to_show[player] = lines
            self.engine.trigger_dialog(True, player)

    def display_dialog(self):
        for player, scene in self.scenes.items():
            if self.engine.is_dialog_active(player):
                scene.display_dialog(self.dialog_to_show[player])

    def add_window(self, window: Window, player: Player, additional_data=None):
        self.scenes[player].window_stack.append(window)
        self.scenes[player].windows[window].additional_data = additional_data

    def populate_scenes(self, *windows: List[MimaWindow]):
        for scene in self.scenes.values():
            for idx, window_class in enumerate(windows):
                window = window_class(self, scene)
                scene.windows[window.wtype] = window
                if idx == 0:
                    scene.window_stack.append(window.wtype)


def calculate(obj, v, real_v, elapsed_time):
    if v == 0 and obj.use_friction:
        mod = obj.attributes.friction
    elif v != 0 and obj.use_acceleration:
        mod = obj.attributes.acceleration
    else:
        return v

    dif = v - real_v
    if abs(dif) < 0.01:
        return v
    return real_v + (v - real_v) * mod


def _chunks_per_row(chunk_size, map_width):
    return math.ceil(map_width / chunk_size) + 1
