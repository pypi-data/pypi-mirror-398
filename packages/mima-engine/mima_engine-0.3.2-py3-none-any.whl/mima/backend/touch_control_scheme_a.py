import time

import pygame

from ..types.keys import Key as K
from ..util.constants import DOUBLE_TAP_SPEED
from ..util.input_defaults import BUTTONS, DEFAULT_TOUCHSCREEN_MAP


class TouchControlSchemeA:

    def __init__(self):

        self._left_finger_tap_pos = 0.0
        self._right_finger_tap_pos = 0.0

        self._last_left_tap = 0.0
        self._last_right_tap = 0.0

    def handle_touch(self, event, width=1.0, height=1.0):
        set_keys = []
        unset_keys = []

        tap_pos = pygame.Vector2(event.x * width, event.y * height)

        if event.type == pygame.FINGERDOWN:
            tap_time = time.time()
            for key, area in DEFAULT_TOUCHSCREEN_MAP.items():

                if (
                    area[0][0] <= event.x < area[1][0]
                    and area[0][1] <= event.y < area[1][1]
                ):
                    if key == K.P1_UP:
                        self._left_finger_tap_pos = tap_pos
                        if tap_time - self._last_left_tap < DOUBLE_TAP_SPEED:
                            # print("Left Double Tap")
                            set_keys.append(K.P1_SELECT)
                        self._last_left_tap = tap_time
                    elif key == K.P1_L:
                        set_keys.append(K.P1_L)
                    else:
                        set_keys.append(key)
                        self._right_finger_tap_pos = tap_pos
                        self._last_right_tap = tap_time

        if event.type == pygame.FINGERUP:
            # release = time.time()
            # finger_dist = (finger_pos - self._left_finger_tap_pos).length()

            if event.x < 0.5:
                # print(f"Left Finger Up: {finger_pos}")
                # if (
                #     SINGLE_TAP_MIN
                #     < release - self._last_left_tap
                #     < SINGLE_TAP_MAX
                # ) and finger_dist < 2.5:
                #     print("Left Single Tap")
                #     # set_keys.append(K.START)

                unset_keys.append(K.P1_SELECT)
                unset_keys.append(K.P1_RIGHT)
                unset_keys.append(K.P1_LEFT)
                unset_keys.append(K.P1_UP)
                unset_keys.append(K.P1_DOWN)
                unset_keys.append(K.P1_L)
                # print(
                #     f"Left Finger moved {finger_dist} "
                #     f"({release - self._last_left_tap} s)"
                # )
            else:
                unset_keys.append(K.P1_START)
                unset_keys.append(K.P1_A)
                unset_keys.append(K.P1_B)
                unset_keys.append(K.P1_Y)
                unset_keys.append(K.P1_X)
                unset_keys.append(K.P1_R)

        if event.type == pygame.FINGERMOTION:
            if event.x < 0.5:
                vd = tap_pos - self._left_finger_tap_pos
                unset_keys.append(K.P1_RIGHT)
                unset_keys.append(K.P1_LEFT)
                unset_keys.append(K.P1_UP)
                unset_keys.append(K.P1_DOWN)
                if abs(vd.x) > 2 * abs(vd.y):
                    # Horizontal
                    if vd.x > 5.0:
                        set_keys.append(K.P1_RIGHT)
                        unset_keys.append(K.P1_LEFT)
                        unset_keys.append(K.P1_UP)
                        unset_keys.append(K.P1_DOWN)
                    elif vd.x < -5.0:
                        set_keys.append(K.P1_LEFT)
                        unset_keys.append(K.P1_RIGHT)
                        unset_keys.append(K.P1_UP)
                        unset_keys.append(K.P1_DOWN)
                elif abs(vd.x) * 2 < abs(vd.y):
                    # Vertical
                    if vd.y > 5.0:
                        unset_keys.append(K.P1_RIGHT)
                        unset_keys.append(K.P1_LEFT)
                        unset_keys.append(K.P1_UP)
                        set_keys.append(K.P1_DOWN)
                    elif vd.y < -5.0:
                        unset_keys.append(K.P1_LEFT)
                        unset_keys.append(K.P1_RIGHT)
                        set_keys.append(K.P1_UP)
                        unset_keys.append(K.P1_DOWN)
                elif abs(vd.x) * 1.05 > abs(vd.y) or abs(vd.x) < 1.05 * abs(
                    vd.y
                ):
                    if vd.x < 0:
                        set_keys.append(K.P1_LEFT)
                    elif vd.x > 0:
                        set_keys.append(K.P1_RIGHT)
                    if vd.y < 0:
                        set_keys.append(K.P1_UP)
                    elif vd.y > 0:
                        set_keys.append(K.P1_DOWN)
                self.vd = vd

        return set_keys, unset_keys

    def get_touch_state(self):
        return {}
