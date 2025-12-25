from enum import Enum
from typing import Generic, Protocol, TypeVar

from pygame import Vector2


class CameraTarget(Protocol):
    def get_pos(self) -> Vector2: ...


T = TypeVar("T", bound=CameraTarget)


class CameraMode(Enum):
    SIMPLE = 0  # No motion, just directly settable
    EDGE_MOVE = 1  # Moves as target crosses boundary
    LAZY_FOLLOW = 2  # Lazily follows the target
    FIXED_SCREENS = 3  # Moves statically between screens
    SLIDE_SCREENS = 4  # Moves statically between screens but with a fast transition


class Camera(Generic[T]):
    def __init__(self, view_size: Vector2, view_pos: Vector2 | None = None) -> None:
        self._view_size = view_size
        self._view_pos = Vector2(0, 0) if view_pos is None else view_pos
        self._mode = CameraMode.SIMPLE
        self._pos = Vector2(0, 0)
        self._edge_trigger_dist = Vector2(1.0, 1.0)
        self._world_boundary_pos = Vector2(0, 0)
        self._world_boundary_size = Vector2(256, 240)
        self._world_boundary_enabled: bool = False
        self._screen_size = Vector2(16, 15)

        self._lazy_follow_rate: float = 4.0
        self._target: T | None = None

    def set_mode(self, mode: CameraMode) -> None:
        self._mode = mode

    def get_mode(self) -> CameraMode:
        return self._mode

    def get_target(self) -> T | None:
        return self._target

    def get_pos(self) -> Vector2:
        return self._pos

    def get_view_pos(self) -> Vector2:
        return self._view_pos

    def get_view_size(self) -> Vector2:
        return self._view_size

    def set_view_size(self, size: Vector2) -> None:
        self._view_size = size

    def set_screen_size(self, size: Vector2):
        self._screen_size = size

    def get_screen_size(self) -> Vector2:
        return self._screen_size

    def set_target(self, target: T | None = None) -> None:
        self._target = target

    def set_world_boundary(self, pos: Vector2, size: Vector2) -> None:
        self._world_boundary_pos = pos
        self._world_boundary_size = size

    def enable_world_boundary(self, enable: bool = True) -> None:
        self._world_boundary_enabled = enable

    def is_world_boundary_enabled(self) -> bool:
        return self._world_boundary_enabled

    def get_world_boundary_pos(self) -> Vector2:
        return self._world_boundary_pos

    def get_world_boundary_size(self) -> Vector2:
        return self._world_boundary_size

    def get_lazy_follow_rate(self) -> float:
        return self._lazy_follow_rate

    def set_lazy_follow_rate(self, rate: float) -> None:
        self._lazy_follow_rate = rate

    def set_edge_trigger_dist(self, edge: Vector2) -> None:
        self._edge_trigger_dist = edge

    def get_edge_trigger_dist(self) -> Vector2:
        return self._edge_trigger_dist

    def update(self, elapsed_time: float) -> bool:
        if self._target is None:
            return False

        tpos = self._target.get_pos()
        if self._mode == CameraMode.SIMPLE:
            self._pos = tpos
        elif self._mode == CameraMode.EDGE_MOVE:
            overlap = tpos - self._pos
            if overlap.x > self._edge_trigger_dist.x:
                self._pos.x += overlap.x - self._edge_trigger_dist.x
            if overlap.x < self._edge_trigger_dist.x:
                self._pos.x += overlap.x + self._edge_trigger_dist.x
            if overlap.y > self._edge_trigger_dist.y:
                self._pos.y += overlap.y - self._edge_trigger_dist.y
            if overlap.y < self._edge_trigger_dist.y:
                self._pos.y += overlap.y + self._edge_trigger_dist.y
        elif self._mode == CameraMode.LAZY_FOLLOW:
            self._pos += (tpos - self._pos) * self._lazy_follow_rate * elapsed_time
        elif self._mode == CameraMode.FIXED_SCREENS:
            self._pos = Vector2(
                int(tpos.x // self._screen_size.x) * int(self._screen_size.x),
                int(tpos.y // self._screen_size.y) * int(self._screen_size.y),
            ) + (self._view_size * 0.5)
        elif self._mode == CameraMode.SLIDE_SCREENS:
            screen = Vector2(
                int(tpos.x // self._screen_size.x) * int(self._screen_size.x),
                int(tpos.y // self._screen_size.y) * int(self._screen_size.y),
            ) + (self._view_size * 0.5)
            self._pos = (
                (screen - self._pos) * self._lazy_follow_rate * 2.0 * elapsed_time
            )

        self._view_pos = self._pos - (self._view_size * 0.5)
        if self._world_boundary_enabled:
            self._view_pos = vclamp(
                self._view_pos,
                self._world_boundary_pos,
                self._world_boundary_pos + self._world_boundary_size - self._view_size,
            )

        return (
            tpos.x >= self._view_pos.x
            and tpos.x < (self._view_pos.x + self._view_size.x)
            and tpos.y >= self._view_pos.y
            and tpos.y < (self._view_pos.y + self._view_size.y)
        )


def vclamp(val: Vector2, low: Vector2, high: Vector2) -> Vector2:
    return Vector2(max(low.x, min(high.x, val.x)), max(low.y, min(high.y, val.y)))


def vmax(val: Vector2, other: Vector2) -> Vector2:
    return Vector2(max(val.x, other.x), max(val.y, other.y))


def vmin(val: Vector2, other: Vector2) -> Vector2:
    return Vector2(min(val.x, other.x), min(val.y, other.y))
