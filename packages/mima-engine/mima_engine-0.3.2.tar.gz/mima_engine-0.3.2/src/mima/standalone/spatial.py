import itertools
import logging
import math
from typing import Generic, TypeVar, overload

from pygame import Vector2

LOG = logging.getLogger(__name__)
T = TypeVar("T")


class SpatialGrid(Generic[T]):
    def __init__(self, world_size: Vector2, cell_size: int) -> None:
        self._world_size: Vector2 = world_size
        self._cell_size: int = cell_size

        self._n_cols = int(math.ceil(world_size.x / cell_size))
        self._n_rows = int(math.ceil(world_size.y / cell_size))

        # self._cells: dict[int, list[T]] = {
        #     i: [] for i in range(self._n_cols * self._n_rows)
        # }
        self._cells: list[list[T]] = [[] for _ in range(self._n_cols * self._n_rows)]
        self._object_map: dict[T, int] = {}
        self.n_objects = 0

    def insert(self, obj: T, pos: Vector2) -> None:
        """Insert object at given position in the grid."""
        idx = self.get_grid_index(pos)
        self._cells[idx].append(obj)
        self._object_map[obj] = idx
        self.n_objects += 1

    def remove(self, obj: T, pos: Vector2) -> None:
        """Remove object at given position from the grid."""
        idx = self.get_grid_index(pos)
        self._cells[idx].remove(obj)
        self._object_map.pop(obj)
        self.n_objects -= 1

    def relocate(self, obj: T, old_pos: Vector2, new_pos: Vector2) -> None:
        """Move object from old position to new position in the grid."""
        if old_pos == new_pos:
            return

        old_idx_from_pos = self.get_grid_index(old_pos)
        if (old_idx := self._object_map[obj]) != old_idx_from_pos:
            LOG.error(
                "Cell mismatch for object %s: saved index %d != %d",
                str(obj),
                self._object_map[obj],
                old_idx,
            )
        new_idx = self.get_grid_index(new_pos)

        if old_idx == new_idx:
            return

        LOG.debug(
            "%s moving from (%.1f, %.1f) (cell %d) to (%.1f, %.1f) (cell %d)",
            str(obj),
            old_pos.x,
            old_pos.y,
            old_idx,
            new_pos.x,
            new_pos.y,
            new_idx,
        )

        if old_idx < 0 or old_idx >= len(self._cells):
            LOG.error(
                "Old cell %d of object does not exist. Number of cells %d.",
                old_idx,
                len(self._cells),
            )

        if obj not in self._cells[old_idx]:
            LOG.error("Object %s not in cell %d", str(obj), old_idx)

        self._cells[old_idx].remove(obj)
        self._cells[new_idx].append(obj)
        self._object_map[obj] = new_idx

    def get_grid_index(self, pos: Vector2) -> int:
        x, y = self.get_grid_coords(pos)
        return x + y * self._n_cols

    def get_grid_coords(self, pos: Vector2) -> tuple[int, int]:
        return (
            int(clamp(pos.x / self._cell_size, 0, self._n_cols - 1)),
            int(clamp(pos.y / self._cell_size, 0, self._n_rows - 1)),
        )

    def get_all_objects(self) -> list[T]:
        """Return all objects stored in the grid."""
        return [val for vals in self._cells for val in vals]

    def get_objects_in_region(self, pos: Vector2, size: Vector2) -> list[T]:
        """Return all objects in the area defined by pos and size."""

        sx = int(max(0, pos.x // self._cell_size))
        sy = int(max(0, pos.y // self._cell_size))

        # Clamp correctly here
        ex = int(min(self._n_cols - 1, (pos.x + size.x - 1e-9) // self._cell_size))
        ey = int(min(self._n_rows - 1, (pos.y + size.y - 1e-9) // self._cell_size))

        return list(
            itertools.chain(
                *[
                    self._cells[gx + gy * self._n_cols]
                    for gy in range(sy, ey + 1)  # include last index
                    for gx in range(sx, ex + 1)
                ]
            )
        )

    def get_cells_in_region(
        self, pos: Vector2, size: Vector2
    ) -> list[tuple[tuple[int, int], list[T]]]:
        """Return all cells in the area defined by pos and size."""
        tl = self.get_grid_coords(pos)
        br = self.get_grid_coords(pos + size)
        clamped_tl = (
            clamp(tl[0], 0, self._n_cols - 1),
            clamp(tl[1], 0, self._n_rows - 1),
        )
        clamped_br = (
            clamp(br[0], 0, self._n_cols - 1),
            clamp(br[0], 0, self._n_rows - 1),
        )

        results = [
            ((x, y), self._cells[x + y * self._n_cols])
            for y in range(clamped_tl[1], clamped_br[1] + 1)
            for x in range(clamped_tl[0], clamped_br[0] + 1)
        ]

        return results

    def clear(self) -> None:
        self._cells: list[list[T]] = [[] for _ in range(self._n_cols * self._n_rows)]
        self._object_map = {}
        self.n_objects = 0


class SpatialHash(Generic[T]):
    def __init__(self, cell_size: int):
        self._cell_size: int = cell_size
        self._cells: dict[tuple[int, int], list[T]] = {}

    def _hash(self, pos: Vector2) -> tuple[int, int]:
        return (int(pos.x) // self._cell_size, int(pos.y) // self._cell_size)


@overload
def clamp(val: int, low: int, high: int) -> int: ...


@overload
def clamp(val: float, low: float, high: float) -> float: ...


def clamp(val: int | float, low: int | float, high: int | float) -> int | float:
    return max(low, min(high, val))
