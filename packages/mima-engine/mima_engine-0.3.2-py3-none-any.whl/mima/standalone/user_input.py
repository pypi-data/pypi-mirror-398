from dataclasses import dataclass
from enum import Enum
from typing import Protocol, TypeVar

import pygame


class Input(Enum):
    """Capture all possible inputs based on typical gamepad layouts."""

    UP = 0
    DOWN = 1
    LEFT = 2
    RIGHT = 3
    A = 4
    B = 5
    X = 6
    Y = 7
    START = 8
    SELECT = 9
    L1 = 10
    R1 = 11
    L2 = 12
    R2 = 13
    L3 = 14
    R3 = 15
    DPAD_UP = 16
    DPAD_DOWN = 17
    DPAD_LEFT = 18
    DPAD_RIGHT = 19
    LEFT_STICK_X = 20  # left x-axis
    LEFT_STICK_Y = 21  # left y-axis
    RIGHT_STICK_X = 22  # left x-axis
    RIGHT_STICK_Y = 23  # left y-axis


class Player(Enum):
    NP = 0  # No player
    P1 = 1  # Player 1
    P2 = 2  # Player 2
    P3 = 3  # Player 3
    P4 = 4  # Player 4
    RP = 5  # Remote player


@dataclass
class InputEvent:
    button: Input
    player: Player
    value: float  # 1 set, 0 unset, -1 and everything between for axes


BUTTONS = [x for x in Input]

AXIS_ACTIVATION = 0.5
AXIS_DEADZONE = 0.25


class InputScheme(Protocol):
    def handle(self, event: pygame.event.Event) -> list[InputEvent]: ...


Proto = TypeVar("Proto", bound=InputScheme)


class InputManager:
    """A class that manages keyboards, gamepad, and touch events."""

    def __init__(self) -> None:
        self._last_keys: dict[Player, dict[Input, float]] = {
            p: {i: 0.0 for i in Input} for p in Player
        }
        self._new_keys: dict[Player, dict[Input, float]] = {
            p: {i: 0.0 for i in Input} for p in Player
        }
        self._inputs_schemes = []

    def add_input_scheme(self, scheme: InputScheme) -> None:
        """Add an input scheme to this manager."""
        self._inputs_schemes.append(scheme)

    def process_events(
        self, events: list[pygame.event.Event] | None = None
    ) -> list[pygame.event.Event]:
        """Query and process all pygame events that are relevant for input.

        Events may be provided or queried directly from pygame. Processing of
        events is delegated to the input schemes.

        Args:
            events: List of pygame events or None. When None is passed, the
            inputs will be queried from ``pygame.event``.

        Returns:
            A list with all pygame events.
        """
        if events is None or not events:
            events = [e for e in pygame.event.get()]

        self._last_keys = {p: d.copy() for p, d in self._new_keys.items()}

        actions: list[InputEvent] = []
        for event in events:
            for scheme in self._inputs_schemes:
                actions.extend(scheme.handle(event))

        for event in actions:
            self.set_value(event.value, event.button, event.player)

        return events

    def pressed(self, button: Input, player: Player = Player.P1) -> bool:
        """Return True when the requested input has been newly pressed."""
        return (
            self._new_keys[player][button] != 0 and self._last_keys[player][button] == 0
        )

    def held(self, button: Input, player: Player = Player.P1) -> bool:
        """Return True when the requested input has been held."""
        return self._new_keys[player][button] != 0

    def released(self, button: Input, player: Player = Player.P1) -> bool:
        """Return True when the requested input is no longer held."""
        return (
            self._last_keys[player][button] != 0 and self._new_keys[player][button] == 0
        )

    def get_value(self, button: Input, player: Player = Player.P1) -> float:
        """Return the value of the requested input."""
        return self._new_keys[player][button]

    def set_value(
        self, value: float, button: Input, player: Player = Player.P1
    ) -> None:
        """Set the value for the requested input."""
        self._new_keys[player][button] = value


class KeyboardMapping:
    def __init__(self, mapping: dict[Player, dict[Input, list[str]]]) -> None:
        self._mapping: dict[Player, dict[Input, list[str]]] = {}
        self._reverse_mapping: dict[int, tuple[Input, Player]] = {}
        for p, m in mapping.items():
            self._mapping.setdefault(p, {})
            for i, k in m.items():
                self._mapping[p][i] = []
                for val in k:
                    if len(val) > 1:
                        # text is uppercase, letters are lowercase
                        val = val.upper()
                    elif len(val) == 0:
                        val = val.lower()
                    key = getattr(pygame, f"K_{val}")
                    self._mapping[p][i].append(key)
                    self._reverse_mapping[key] = (i, p)

    def handle(self, event: pygame.event.Event) -> list[InputEvent]:
        actions = []

        if event.type == pygame.KEYDOWN:
            ip = self._reverse_mapping.get(event.key, ())
            if ip and len(ip) == 2:
                actions.append(InputEvent(button=ip[0], player=ip[1], value=1.0))
        if event.type == pygame.KEYUP:
            ip = self._reverse_mapping.get(event.key, ())
            if ip and len(ip) == 2:
                actions.append(InputEvent(button=ip[0], player=ip[1], value=0.0))
        return actions


class GamepadMapping:
    def __init__(self, mapping: dict[Player, dict[Input, list[str]]]) -> None:
        self._mapping: dict[Player, dict[Input, list[str]]] = {}
        self._reverse_mapping: dict[str, tuple[Input, Player]] = {}
        for p, m in mapping.items():
            self._mapping.setdefault(p, {})
            for i, k in m.items():
                self._mapping[p][i] = []
                for val in k:
                    if len(val) > 1:
                        # text is uppercase, letters are lowercase
                        val = val.upper()
                    elif len(val) == 0:
                        val = val.lower()

                    self._mapping[p][i].append(val)
                    self._reverse_mapping[val] = (i, p)

        self._joysticks = {}
        self._joy2player: dict[int, Player] = {}

    def handle(self, event: pygame.event.Event) -> list[InputEvent]:
        actions = []

        if event.type == pygame.JOYDEVICEREMOVED:
            self._joysticks.pop(event.instance_id)

        if event.type == pygame.JOYDEVICEADDED:
            js = pygame.joystick.Joystick(event.device_index)
            self._joysticks[js.get_instance_id()] = js

        if event.type == pygame.JOYBUTTONDOWN:
            ip = self._reverse_mapping.get(str(event.button), ())
            if ip and len(ip) == 2:
                actions.append(InputEvent(button=ip[0], player=ip[1], value=1.0))
        if event.type == pygame.JOYBUTTONUP:
            ip = self._reverse_mapping.get(str(event.button), ())
            if ip and len(ip) == 2:
                actions.append(InputEvent(button=ip[0], player=ip[1], value=0.0))

        if event.type == pygame.JOYHATMOTION:
            if event.value[0] > 0:
                left_val = 0
                right_val = 1
            elif event.value[0] < 0:
                left_val = 1
                right_val = 0
            else:
                left_val = right_val = 0

            if event.value[1] > 0:
                up_val = 1
                down_val = 0
            elif event.value[1] < 0:
                up_val = 0
                down_val = 1
            else:
                up_val = down_val = 0

            left = self._reverse_mapping.get("LEFT", ())
            if left and len(left) == 2:
                actions.append(
                    InputEvent(button=left[0], player=left[1], value=left_val)
                )

            right = self._reverse_mapping.get("RIGHT", ())
            if right and len(right) == 2:
                actions.append(
                    InputEvent(button=right[0], player=right[1], value=right_val)
                )

            up = self._reverse_mapping.get("UP", ())
            if up and len(up) == 2:
                actions.append(InputEvent(button=up[0], player=up[1], value=up_val))
            down = self._reverse_mapping.get("DOWN", ())
            if down and len(down) == 2:
                actions.append(
                    InputEvent(button=down[0], player=down[1], value=down_val)
                )

        return actions


class TouchMapping:
    def handle(self, event: pygame.event.Event) -> list[InputEvent]:
        return []
