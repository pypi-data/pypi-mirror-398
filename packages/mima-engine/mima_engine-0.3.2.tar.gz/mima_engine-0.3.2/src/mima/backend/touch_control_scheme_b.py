import time

import pygame

from ..types.keys import Key as K
from ..util.constants import DOUBLE_TAP_SPEED
from ..util.input_defaults import ALT_TOUCHSCREEN_MAP, BUTTONS


class TouchControlSchemeB:

    def __init__(self):

        self.move_start_pos = pygame.Vector2()
        self.move_pos = pygame.Vector2()
        self.move_sy = 0.0
        self.move_px = 0.0
        self.move_py = 0.0
        self._left_finger_tap_pos = 0.0
        self._right_finger_tap_pos = 0.0

        self._last_left_tap = 0.0
        self._last_right_tap = 0.0
        self._keys_active = {k: False for k in K}
        self._state = {}
        for key, conf in ALT_TOUCHSCREEN_MAP.items():
            px, py = conf["pos"]
            w, h = conf["size"]
            self._state[key] = {
                "rpx": px,
                "rpy": py,
                "rwidth": w,
                "rheight": h,
                "active": False,
            }

    def handle_touch(self, event, width=1.0, height=1.0):
        set_keys = []
        unset_keys = []

        tap_pos = pygame.Vector2(event.x * width, event.y * height)
        keys_active = {k: False for k in K}
        # print(f"{event.x:.2f}, {event.y:.2f}", end="")
        for key, conf in ALT_TOUCHSCREEN_MAP.items():
            px, py = conf["pos"]
            w, h = conf["size"]
            area = [[px, py], [px + w, py + h]]

            if (
                area[0][0] <= event.x < area[1][0]
                and area[0][1] <= event.y < area[1][1]
            ):
                if key == K.P1_UP:
                    if event.type == pygame.FINGERDOWN:
                        self.move_start_pos = pygame.Vector2(tap_pos)
                        self.move_pos = pygame.Vector2(tap_pos)
                        self._state[key]["rsx"] = event.x
                        self._state[key]["rsy"] = event.y
                        self._state[key]["rpx"] = event.x
                        self._state[key]["rpy"] = event.y
                    elif event.type == pygame.FINGERMOTION:
                        self.move_pos = tap_pos
                        self._state[key]["rpx"] = event.x
                        self._state[key]["rpy"] = event.y

                        vd = self.move_pos - self.move_start_pos
                        if abs(vd.x) > 2 * abs(vd.y):
                            # Horizontal
                            if vd.x > 5.0:
                                keys_active[K.P1_RIGHT] = True
                                # print("..>", end="")
                            elif vd.x < -5.0:
                                keys_active[K.P1_LEFT] = True
                                # print("..<", end="")
                        elif abs(vd.x) * 2 < abs(vd.y):
                            # Vertical
                            if vd.y > 5.0:
                                keys_active[K.P1_DOWN] = True
                                # print("..v", end="")
                            elif vd.y < -5.0:
                                keys_active[K.P1_UP] = True
                                # print("..^", end="")
                        elif abs(vd.x) * 1.05 > abs(vd.y) or abs(
                            vd.x
                        ) < 1.05 * abs(vd.y):
                            # Diagonal
                            if vd.x < 0:
                                keys_active[K.P1_LEFT] = True
                                # print("..<", end="")
                            elif vd.x > 0:
                                keys_active[K.P1_RIGHT] = True
                                # print("..>", end="")
                            if vd.y < 0:
                                keys_active[K.P1_UP] = True
                                # print("..^", end="")
                            elif vd.y > 0:
                                keys_active[K.P1_DOWN] = True
                                # print("..v", end="")
                    # elif event.type == pygame.FINGERUP:
                    #     unset_keys.append(K.P1_RIGHT)
                    #     unset_keys.append(K.P1_LEFT)
                    #     unset_keys.append(K.P1_UP)
                    #     unset_keys.append(K.P1_DOWN)
                else:
                    if event.type == pygame.FINGERDOWN:
                        keys_active[key] = True
                        # print(f"..{key.name}", end="")
                    if event.type == pygame.FINGERMOTION:
                        keys_active[key] = True
                        # print(f"..{key.name}", end="")
        # print()
        for k, val in keys_active.items():
            if val:
                set_keys.append(k)
                # self._state.setdefault(k, {})["active"] = True
                if k in self._state:
                    self._state[k]["active"] = True
                if k in [K.P1_LEFT, K.P1_RIGHT, K.P1_DOWN]:
                    self._state[K.P1_UP]["active"] = True
            else:
                unset_keys.append(k)
                if k in self._state:
                    self._state[k]["active"] = False
        return set_keys, unset_keys

    def get_touch_state(self):
        state = {}
        for key, conf in self._state.items():
            nkey = K(key.value - 12)
            state[nkey] = conf

        return state
