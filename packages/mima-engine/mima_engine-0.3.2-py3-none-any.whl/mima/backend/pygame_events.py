import logging
import time
from typing import Any, Dict, List, Optional, Tuple, Union

import pygame

from ..types.keys import Key as K
from ..types.player import Player
from ..util.constants import AXIS_ACTIVATION, AXIS_DEADZONE, DOUBLE_TAP_SPEED
from ..util.input_defaults import (
    BUTTONS,
    DEFAULT_JOYSTICK_MAP,
    DEFAULT_KEYBOARD_MAP,
    DEFAULT_TOUCHSCREEN_MAP,
)
from .touch_control_scheme_a import TouchControlSchemeA
from .touch_control_scheme_b import TouchControlSchemeB

LOG = logging.getLogger(__name__)

KEYBOARD_EVENTS = [pygame.KEYUP, pygame.KEYDOWN]
JOYSTICK_EVENTS = [
    pygame.JOYDEVICEADDED,
    pygame.JOYDEVICEREMOVED,
    pygame.JOYBUTTONUP,
    pygame.JOYBUTTONDOWN,
    pygame.JOYAXISMOTION,
    pygame.JOYHATMOTION,
]
TOUCH_EVENTS = [pygame.FINGERUP, pygame.FINGERDOWN, pygame.FINGERMOTION]
SDL2_BACKGROUND_EVENTS = [259, 260, 261, 262]


class PygameUserInput:
    """A class that manages keys and key events."""

    def __init__(
        self,
        key_map: Optional[Dict[K, List[str]]] = None,
        joystick_map: Optional[Dict[K, List[Union[str, int]]]] = None,
        joy_to_player: Optional[Dict[int, Player]] = None,
        platform: str = "PC",
    ):
        self._last_keys: Dict[K, bool] = {}
        self._new_keys: Dict[K, bool] = {but: False for but in BUTTONS}
        self._touch_control = TouchControlSchemeB()
        # self._left_finger_tap_pos: pygame.Vector2 = pygame.Vector2(0, 0)
        # self._right_finger_tap_pos: pygame.Vector2 = pygame.Vector2(0, 0)
        # self._left_finger_pos: pygame.Vector2 = pygame.Vector2(0, 0)
        # self._right_finger_pos: pygame.Vector2 = pygame.Vector2(0, 0)
        # self._last_left_tap: float = 0.0
        # self._last_right_tap: float = 0.0
        # self._last_left_motion: float = 0.0
        # self._last_right_motion: float = 0.0
        self._key_map: Dict[K, List[int]] = {}
        self.joystick_to_player: Dict[int, Player] = (
            joy_to_player
            if joy_to_player is not None
            else {
                0: Player.P1,
                1: Player.P2,
                2: Player.P3,
                4: Player.P4,
            }
        )
        self.vd = pygame.Vector2(0, 0)
        self.joystick_input_enabled: bool = True
        if platform == "android":
            # Disable motion control
            # FIXME allow external controllers
            self.joystick_input_enabled = False
        # self._fingers: List[pygame.Vector2] = []

        # if key_map is None:
        #     self._key_map = dict()
        #     for key, vals in RuntimeConfig().keymap.items():
        #         self._key_map[key] = list()
        #         for val in vals:
        #             self._key_map[key].append(getattr(pygame, f"K_{val}"))
        # else:
        key_map = key_map if key_map is not None else DEFAULT_KEYBOARD_MAP
        for key, vals in key_map.items():
            self._key_map[key] = []
            for val in vals:
                if len(val) > 1:
                    val = val.upper()
                self._key_map[key].append(getattr(pygame, f"K_{val}"))

        # print(self._key_map)
        # self._key_map = key_map
        # if joystick_map is None:
        #     self._joystick_map = DEFAULT_JOYSTICK_MAP
        # else:
        if joystick_map is None:
            self._joystick_map = {}
            for but in BUTTONS:
                self._joystick_map[but] = DEFAULT_JOYSTICK_MAP[
                    K(but.value % 12)
                ]
        else:
            self._joystick_map = joystick_map

        self.joysticks: Dict[Player, Optional[Any]] = {}
        self._init_joysticks()
        self.width = 0
        self.height = 0
        self._past_events = {}
        self._new_events = {}
        self._collect_all_events = False
        self.enable_touch_controls = False

    def reset(self):
        self._last_keys = self._new_keys.copy()
        self._past_events = self._new_events.copy()
        self.all_events = []

    def get_keyboard_map(self) -> Dict[K, List[str]]:
        key_map: Dict[K, List[str]] = {}
        for key, mapping in self._key_map.items():
            key_map[key] = []
            for val in mapping:
                key_map[key].append(pygame.key.name(val))
        return key_map

    def get_joystick_map(self):
        return self._joystick_map

    def get_key_name(self, val: int):
        return pygame.key.name(val)

    def update_keyboard_map(self, kbmap: Dict[K, List[str]]):
        new_keymap: Dict[K, List[int]] = {}
        try:
            for key, vals in kbmap.items():
                new_keymap[key] = []
                for val in vals:
                    if len(val) > 1:
                        val = val.upper()
                    new_keymap[key].append(getattr(pygame, f"K_{val}"))
        except Exception as err:
            LOG.exception(f"Failed to update keyboard map: {err}")
            return
        self._key_map = new_keymap

    def update_joystick_map(self, jsmap):
        self._joystick_map = jsmap

    def update_joysticks(self, reassign: List[Tuple[int, Player]]):
        self.joystick_to_player = {}
        for item in reassign:
            self.joystick_to_player[item[0]] = item[1]
        # k2d = None
        # for jid, p in self.joystick_to_player.items():
        #     if p == player:
        #         k2d = jid
        # self.joystick_to_player[joy] = player
        # self.joystick_to_player[k2d] = None

    def process(self, event):
        if event.type in KEYBOARD_EVENTS:
            self._handle_keyboard(event)

        if event.type in JOYSTICK_EVENTS and self.joystick_input_enabled:
            self._handle_joystick(event)

        # self._touch_control.update(self.width, self.height)
        if self.enable_touch_controls and event.type in TOUCH_EVENTS:
            self._handle_touch(event)

        # print(
        #     {key: val for key, val in self._last_keys.items() if val},
        #     {k: v for k, v in self._new_keys.items() if v},
        # )

    def _handle_keyboard(self, event):
        if self._collect_all_events:
            self._collect_keyboard_events(event)

        if event.type == pygame.KEYDOWN:
            for but, keys in self._key_map.items():
                if event.key in keys:
                    self.set_key(but)

        if event.type == pygame.KEYUP:
            for but, keys in self._key_map.items():
                if event.key in keys:
                    self.unset_key(but)

    def _js_real(self, joy, but):
        return K[f"{self.joystick_to_player[joy].name}_{but.name}"]

    def _handle_joystick(self, event):
        if self._collect_all_events:
            self._collect_joystick_events(event)

        if event.type == pygame.JOYDEVICEREMOVED:
            self.joystick = {}
            LOG.info("Gamepad unplugged.")

        if event.type == pygame.JOYDEVICEADDED:
            self._init_joysticks()
            LOG.info("Detected new gamepad device %s.", self.joysticks)

        if event.type == pygame.JOYBUTTONDOWN:
            if event.joy not in self.joystick_to_player:
                return
            for but, keys in self._joystick_map.items():
                if (
                    str(event.button) in keys
                    and self.joystick_to_player[event.joy] is not None
                    and self.joystick_to_player[event.joy].name in but.name
                ):
                    self.set_key(but)

        if event.type == pygame.JOYBUTTONUP:
            if event.joy not in self.joystick_to_player:
                return
            for but, keys in self._joystick_map.items():
                if (
                    str(event.button) in keys
                    and self.joystick_to_player[event.joy] is not None
                    and self.joystick_to_player[event.joy].name in but.name
                ):
                    self.unset_key(but)

        if event.type == pygame.JOYHATMOTION:
            if event.joy not in self.joystick_to_player:
                return

            if event.value[0] == 0:
                self.unset_key(self._js_real(event.joy, K.LEFT))
                self.unset_key(self._js_real(event.joy, K.RIGHT))
            elif event.value[0] == -1:
                self.set_key(self._js_real(event.joy, K.LEFT))
                self.unset_key(self._js_real(event.joy, K.RIGHT))
            else:
                self.unset_key(self._js_real(event.joy, K.LEFT))
                self.set_key(self._js_real(event.joy, K.RIGHT))

            if event.value[1] == 0:
                self.unset_key(self._js_real(event.joy, K.UP))
                self.unset_key(self._js_real(event.joy, K.DOWN))
            elif event.value[1] == 1:
                self.set_key(self._js_real(event.joy, K.UP))
                self.unset_key(self._js_real(event.joy, K.DOWN))
            else:
                self.unset_key(self._js_real(event.joy, K.UP))
                self.set_key(self._js_real(event.joy, K.DOWN))

        if event.type == pygame.JOYAXISMOTION:
            if event.joy not in self.joystick_to_player:
                return

            if event.axis == 0:
                if event.value < -AXIS_ACTIVATION:
                    self.set_key(self._js_real(event.joy, K.LEFT))
                    self.unset_key(self._js_real(event.joy, K.RIGHT))
                elif event.value > AXIS_ACTIVATION:
                    self.unset_key(self._js_real(event.joy, K.LEFT))
                    self.set_key(self._js_real(event.joy, K.RIGHT))
                elif abs(event.value) < AXIS_DEADZONE:
                    self.unset_key(self._js_real(event.joy, K.LEFT))
                    self.unset_key(self._js_real(event.joy, K.RIGHT))
                else:
                    pass
            if event.axis == 1:
                if event.value < -AXIS_ACTIVATION:
                    self.set_key(self._js_real(event.joy, K.UP))
                    self.unset_key(self._js_real(event.joy, K.DOWN))
                elif event.value > AXIS_ACTIVATION:
                    self.unset_key(self._js_real(event.joy, K.UP))
                    self.set_key(self._js_real(event.joy, K.DOWN))
                elif abs(event.value) < AXIS_DEADZONE:
                    self.unset_key(self._js_real(event.joy, K.UP))
                    self.unset_key(self._js_real(event.joy, K.DOWN))

    def _handle_touch(self, event):
        set_keys, unset_keys = self._touch_control.handle_touch(
            event, self.width, self.height
        )
        for key in unset_keys:
            self.unset_key(key)
        for key in set_keys:
            self.set_key(key)

        # finger_pos = pygame.Vector2(
        #     event.x * self.width, event.y * self.height
        # )

        # if event.type == pygame.FINGERDOWN:
        #     tap = time.time()
        #     for key, area in DEFAULT_TOUCHSCREEN_MAP.items():

        #         if (
        #             area[0][0] <= event.x < area[1][0]
        #             and area[0][1] <= event.y < area[1][1]
        #         ):
        #             if key == K.P1_UP:
        #                 self._left_finger_tap_pos = finger_pos
        #                 if tap - self._last_left_tap < DOUBLE_TAP_SPEED:
        #                     # print("Left Double Tap")
        #                     self.set_key(K.P1_SELECT)
        #                 self._last_left_tap = tap
        #             elif key == K.P1_L:
        #                 self.set_key(K.P1_L)
        #             else:
        #                 self.set_key(key)
        #                 self._right_finger_tap_pos = finger_pos
        #                 self._last_right_tap = tap

        #     # if event.x < 0.0625 and event.y < 0.1111:
        #     #     self.set_key(K.L)
        #     # elif event.x > 1.0 - 0.0625 and event.y < 0.1111:
        #     #     self.set_key(K.R)
        #     # elif event.x < 0.5:
        #     #     # print(f"Left Finger Down: {finger_pos}")
        #     #     self._left_finger_tap_pos = finger_pos

        #     #     if tap - self._last_left_tap < DOUBLE_TAP_SPEED:
        #     #         # print("Left Double Tap")
        #     #         self.set_key(K.SELECT)
        #     #     self._last_left_tap = tap
        #     #     #     self._left_finger_pos.x = event.x
        #     #     #     self._left_finger_pos.y = event.y

        #     #     #     if tap - self._last_left_tap < 0.2:
        #     #     #         print("Left Double Tap")
        #     #     #         # self._set_key(K.START)
        #     #     #         # self._unset_key(K.RIGHT)
        #     #     #         # self._unset_key(K.LEFT)
        #     #     #         # self._unset_key(K.UP)
        #     #     #         # self._unset_key(K.DOWN)
        #     # else:
        #     #     self._right_finger_tap_pos = finger_pos

        #     #     # if tap - self._last_right_tap < DOUBLE_TAP_SPEED:
        #     #     #     # print("Right Double Tap")
        #     #     #     self.set_key(K.SELECT)
        #     #     self._last_right_tap = tap
        #     #     if event.y < 0.3:
        #     #         self.set_key(K.START)
        #     #     elif event.x < 0.75:
        #     #         self.set_key(K.B)
        #     #     else:
        #     #         self.set_key(K.A)
        #     #     self._right_finger_pos.x = event.x
        #     #     self._right_finger_pos.y = event.y
        #     #     if tap - self._last_right_tap < 0.2:
        #     #         print("Right Double Tap")

        # if event.type == pygame.FINGERUP:
        #     # release = time.time()
        #     # finger_dist = (finger_pos - self._left_finger_tap_pos).length()

        #     if event.x < 0.5:
        #         # print(f"Left Finger Up: {finger_pos}")
        #         # if (
        #         #     SINGLE_TAP_MIN
        #         #     < release - self._last_left_tap
        #         #     < SINGLE_TAP_MAX
        #         # ) and finger_dist < 2.5:
        #         #     print("Left Single Tap")
        #         #     # self.set_key(K.START)

        #         self.unset_key(K.P1_SELECT)
        #         self.unset_key(K.P1_RIGHT)
        #         self.unset_key(K.P1_LEFT)
        #         self.unset_key(K.P1_UP)
        #         self.unset_key(K.P1_DOWN)
        #         self.unset_key(K.P1_L)
        #         # print(
        #         #     f"Left Finger moved {finger_dist} "
        #         #     f"({release - self._last_left_tap} s)"
        #         # )
        #     else:
        #         self.unset_key(K.P1_START)
        #         self.unset_key(K.P1_A)
        #         self.unset_key(K.P1_B)
        #         self.unset_key(K.P1_Y)
        #         self.unset_key(K.P1_X)
        #         self.unset_key(K.P1_R)
        #     # print(f"Right Finger Up: {finger_pos}")
        #     # if (
        #     #     SINGLE_TAP_MIN
        #     #     < release - self._last_right_tap
        #     #     < SINGLE_TAP_MAX
        #     # ) and finger_dist < 2.5:
        #     #     print("Right Single Tap")

        #     # print(
        #     #     f"Left Finger moved {finger_dist} "
        #     #     f"({release - self._last_left_tap} s)"
        #     # )
        #     #
        #     # if event.x < 0.5:
        #     #     if 0.1 < release - self._last_left_tap < 0.25:
        #     #         print("Left Single Tap")

        #     #     self._left_finger_pos.x = 0
        #     #     self._left_finger_pos.y = 0
        #     #     self._unset_key(K.DOWN)
        #     #     self._unset_key(K.LEFT)
        #     #     self._unset_key(K.UP)
        #     #     self._unset_key(K.RIGHT)
        #     #     self._unset_key(K.START)
        #     # else:
        #     #     if 0.1 < release - self._last_right_tap < 0.25:
        #     #         print("Right Single Tap")

        #     #     self._unset_key(K.A)
        #     #     self._unset_key(K.B)
        # if event.type == pygame.FINGERMOTION:
        #     if event.x < 0.5:
        #         vd = finger_pos - self._left_finger_tap_pos
        #         self.unset_key(K.P1_RIGHT)
        #         self.unset_key(K.P1_LEFT)
        #         self.unset_key(K.P1_UP)
        #         self.unset_key(K.P1_DOWN)
        #         if abs(vd.x) > 2 * abs(vd.y):
        #             # Horizontal
        #             if vd.x > 5.0:
        #                 self.set_key(K.P1_RIGHT)
        #                 self.unset_key(K.P1_LEFT)
        #                 self.unset_key(K.P1_UP)
        #                 self.unset_key(K.P1_DOWN)
        #             elif vd.x < -5.0:
        #                 self.set_key(K.P1_LEFT)
        #                 self.unset_key(K.P1_RIGHT)
        #                 self.unset_key(K.P1_UP)
        #                 self.unset_key(K.P1_DOWN)
        #         elif abs(vd.x) * 2 < abs(vd.y):
        #             # Vertical
        #             if vd.y > 5.0:
        #                 self.unset_key(K.P1_RIGHT)
        #                 self.unset_key(K.P1_LEFT)
        #                 self.unset_key(K.P1_UP)
        #                 self.set_key(K.P1_DOWN)
        #             elif vd.y < -5.0:
        #                 self.unset_key(K.P1_LEFT)
        #                 self.unset_key(K.P1_RIGHT)
        #                 self.set_key(K.P1_UP)
        #                 self.unset_key(K.P1_DOWN)
        #         elif abs(vd.x) * 1.05 > abs(vd.y) or abs(vd.x) < 1.05 * abs(
        #             vd.y
        #         ):
        #             if vd.x < 0:
        #                 self.set_key(K.P1_LEFT)
        #             elif vd.x > 0:
        #                 self.set_key(K.P1_RIGHT)
        #             if vd.y < 0:
        #                 self.set_key(K.P1_UP)
        #             elif vd.y > 0:
        #                 self.set_key(K.P1_DOWN)
        #         # else:
        #         #     vd = finger_pos - self._right_finger_tap_pos
        #         #     self.unset_key(K.A)
        #         #     self.unset_key(K.B)
        #         #     self.unset_key(K.Y)
        #         #     self.unset_key(K.X)
        #         #     if abs(vd.x) > 2 * abs(vd.y):
        #         #         # Horizontal
        #         #         if vd.x > 5.0:
        #         #             self.set_key(K.Y)
        #         #         elif vd.x < -5.0:
        #         #             self.set_key(K.B)
        #         #     elif abs(vd.x) * 2 < abs(vd.y):
        #         #         # Vertical
        #         #         if vd.y > 5.0:
        #         #             self.set_key(K.A)
        #         #         elif vd.y < -5.0:
        #         #             self.set_key(K.X)

        #         self.vd = vd

    def _handle_mouse(self, event):
        # if event.type == pygame.MOUSEBUTTONDOWN:
        #     if 0 <= event.pos[0] < 16 and 80 <= event.pos[1] < 96:
        #         self._unset_key(K.RIGHT)
        #         self._set_key(K.LEFT)
        #         self._unset_key(K.UP)
        #         self._unset_key(K.DOWN)
        #     elif 0 <= event.pos[0] < 16 and 64 <= event.pos[1] < 80:
        #         self._unset_key(K.RIGHT)
        #         self._set_key(K.LEFT)
        #         self._set_key(K.UP)
        #         self._unset_key(K.DOWN)
        #     elif 16 <= event.pos[0] < 32 and 64 <= event.pos[1] < 80:
        #         self._unset_key(K.RIGHT)
        #         self._unset_key(K.LEFT)
        #         self._set_key(K.UP)
        #         self._unset_key(K.DOWN)
        #     elif 32 <= event.pos[0] < 48 and 64 <= event.pos[1] < 80:
        #         self._set_key(K.RIGHT)
        #         self._unset_key(K.LEFT)
        #         self._set_key(K.UP)
        #         self._unset_key(K.DOWN)
        #     elif 32 <= event.pos[0] < 48 and 80 <= event.pos[1] < 96:
        #         self._set_key(K.RIGHT)
        #         self._unset_key(K.LEFT)
        #         self._unset_key(K.UP)
        #         self._unset_key(K.DOWN)
        #     elif 32 <= event.pos[0] < 48 and 96 <= event.pos[1] < 112:
        #         self._set_key(K.RIGHT)
        #         self._unset_key(K.LEFT)
        #         self._unset_key(K.UP)
        #         self._set_key(K.DOWN)
        #     elif 16 <= event.pos[0] < 32 and 96 <= event.pos[1] < 112:
        #         self._unset_key(K.RIGHT)
        #         self._unset_key(K.LEFT)
        #         self._unset_key(K.UP)
        #         self._set_key(K.DOWN)
        #     elif 0 <= event.pos[0] < 16 and 96 <= event.pos[1] < 112:
        #         self._unset_key(K.RIGHT)
        #         self._set_key(K.LEFT)
        #         self._unset_key(K.UP)
        #         self._set_key(K.DOWN)
        #     if 112 <= event.pos[0] < 144 and 0 <= event.pos[1] < 32:
        #         self._set_key(K.START)
        #         self._unset_key(K.RIGHT)
        #         self._unset_key(K.LEFT)
        #         self._unset_key(K.UP)
        #         self._unset_key(K.DOWN)
        #     if 240 <= event.pos[0] < 256 and 80 <= event.pos[1] < 112:
        #         self._set_key(K.A)
        #         self._unset_key(K.RIGHT)
        #         self._unset_key(K.LEFT)
        #         self._unset_key(K.UP)
        #         self._unset_key(K.DOWN)

        # if event.type == pygame.MOUSEBUTTONUP:
        #     self._unset_key(K.DOWN)
        #     self._unset_key(K.LEFT)
        #     self._unset_key(K.UP)
        #     self._unset_key(K.RIGHT)
        #     self._unset_key(K.START)
        #     self._unset_key(K.A)
        pass

    def _init_joysticks(self):
        for jid in range(pygame.joystick.get_count()):
            js = pygame.joystick.Joystick(jid)
            js.init()
            # p = Player(jid + 1)
            self.joysticks[js.get_id()] = js
            LOG.info(
                "Initialized Joystick #%d: %s",
                jid,
                self.joysticks[js.get_id()].get_name(),
            )

    def set_key(self, button: K):
        self._new_keys[button] = True

    def unset_key(self, button: K):
        self._new_keys[button] = False

    def new_key_press(self, button: K, player: Player = Player.P1):
        button = _button_to_player(button, player)
        return self._new_keys[button] and not self._last_keys[button]

    def key_held(self, button: K, player: Player = Player.P1):
        button = _button_to_player(button, player)
        return self._new_keys[button]

    def new_key_release(self, button: K, player: Player = Player.P1):
        button = _button_to_player(button, player)
        return self._last_keys[button] and not self._new_keys[button]

    def get_all_events(self):
        return self._new_events

    def _collect_keyboard_events(self, event):
        kid = f"kb_{event.key}"
        if event.type == pygame.KEYDOWN:
            self._new_events[kid] = {
                "type": "keyboard",
                "id": event.type,
                "button": event.key,
                "name": pygame.key.name(event.key),
            }
        if event.type == pygame.KEYUP and kid in self._new_events:
            del self._new_events[kid]

    def _collect_joystick_events(self, event):
        if event.type == pygame.JOYDEVICEREMOVED:
            jid = f"js_{event.instance_id}_removed"
            self._new_events[jid] = {
                "type": "joystick",
                "id": event.instance_id,
                "button": "removed",
                "name": "removed",
            }
        if event.type == pygame.JOYDEVICEADDED:
            jid = f"js_{event.device_index}_added"
            self._new_events[jid] = {
                "type": "joystick",
                "id": event.device_index,
                "button": "added",
                "guid": event.guid,
            }

        if event.type == pygame.JOYBUTTONDOWN:
            kid = f"js_{event.joy}_{event.button}"

            self._new_events[kid] = {
                "type": "joystick",
                "id": event.instance_id,
                "joy": event.joy,
                "button": event.button,
                "name": self.joysticks[event.joy].get_name(),
                "power_level": self.joysticks[event.joy].get_power_level(),
            }
        if event.type == pygame.JOYBUTTONUP:
            kid = f"js_{event.joy}_{event.button}"
            if kid in self._new_events:
                del self._new_events[kid]
        if event.type == pygame.JOYHATMOTION:
            kid = f"js_{event.joy}_{event.hat}"
            klid = f"{kid}_left"
            krid = f"{kid}_right"
            kuid = f"{kid}_up"
            kdid = f"{kid}_down"
            if event.value[0] == 0:
                if klid in self._new_events:
                    del self._new_events[klid]
                if krid in self._new_events:
                    del self._new_events[krid]
            elif event.value[0] == -1:
                self._new_events[klid] = {
                    "type": "joystick",
                    "id": event.instance_id,
                    "joy": event.joy,
                    "button": "left",
                    "hat": event.hat,
                    "value": event.value[0],
                    "name": self.joysticks[event.joy].get_name(),
                    "power_level": self.joysticks[event.joy].get_power_level(),
                }
                if krid in self._new_events:
                    del self._new_events[krid]
            else:
                self._new_events[krid] = {
                    "type": "joystick",
                    "id": event.instance_id,
                    "joy": event.joy,
                    "button": "right",
                    "hat": event.hat,
                    "value": event.value[0],
                    "name": self.joysticks[event.joy].get_name(),
                    "power_level": self.joysticks[event.joy].get_power_level(),
                }
                if klid in self._new_events:
                    del self._new_events[klid]

            if event.value[1] == 0:
                if kuid in self._new_events:
                    del self._new_events[kuid]
                if kdid in self._new_events:
                    del self._new_events[kdid]
            elif event.value[1] == 1:
                self._new_events[kuid] = {
                    "type": "joystick",
                    "id": event.instance_id,
                    "joy": event.joy,
                    "button": "up",
                    "hat": event.hat,
                    "value": event.value[1],
                    "name": self.joysticks[event.joy].get_name(),
                    "power_level": self.joysticks[event.joy].get_power_level(),
                }
                if kdid in self._new_events:
                    del self._new_events[kdid]
            else:
                self._new_events[kdid] = {
                    "type": "joystick",
                    "id": event.instance_id,
                    "joy": event.joy,
                    "button": "down",
                    "hat": event.hat,
                    "value": event.value[1],
                    "name": self.joysticks[event.joy].get_name(),
                    "power_level": self.joysticks[event.joy].get_power_level(),
                }
                if kuid in self._new_events:
                    del self._new_events[kuid]

    def trigger_all_events_collection(self, active: bool = True):
        self._collect_all_events = active

    def get_touch_state(self):
        return self._touch_control.get_touch_state()


def _button_to_player(button: K, player: Player):
    return K(button.value + 12 * player.value)
