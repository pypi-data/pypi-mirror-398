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

        self._cells: list[list[T]] = [[] for _ in range(self._n_cols * self._n_rows)]
        self._object_map: dict[T, list[int]] = {}
        self.n_objects = 0

    def insert(self, obj: T, pos: Vector2, size: Vector2 | None = None) -> None:
        """Insert object at given position in the grid."""
        size = Vector2(1, 1) if size is None else size
        indices = cells_for_aabb(pos, size, self._cell_size, self._n_rows, self._n_cols)

        for idx in indices:
            self._cells[idx].append(obj)

        self._object_map[obj] = indices
        self.n_objects += 1

    def remove(self, obj: T) -> None:
        """Remove object from all grid cells it occupies."""
        indices = self._object_map.get(obj)
        if indices is None:
            return

        for idx in indices:
            if obj in self._cells[idx]:
                self._cells[idx].remove(obj)

        self._object_map.pop(obj)
        self.n_objects -= 1

    def relocate(self, obj: T, new_pos: Vector2, size: Vector2 | None = None) -> None:
        """Move object to a new position in the grid."""

        old_indices = self._object_map.get(obj)
        if old_indices is None:
            LOG.warning(
                "Objects %s not in grid. Performing insertion instead.", str(obj)
            )
            return self.insert(obj, new_pos, size)

        size = Vector2(1, 1) if size is None else size

        new_indices = cells_for_aabb(
            new_pos, size, self._cell_size, self._n_rows, self._n_cols
        )
        if old_indices == new_indices:
            return

        LOG.debug(
            "Object %s (%s) moving from cells %s to %s",
            str(obj),
            new_pos,
            old_indices,
            new_indices,
        )
        for idx in old_indices:
            if obj in self._cells[idx]:
                self._cells[idx].remove(obj)

        for idx in new_indices:
            self._cells[idx].append(obj)

        self._object_map[obj] = new_indices

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
        return list(self._object_map.keys())

    def get_objects_in_region(self, pos: Vector2, size: Vector2) -> list[T]:
        """Return all objects in the area defined by pos and size."""

        sx = int(max(0, pos.x // self._cell_size))
        sy = int(max(0, pos.y // self._cell_size))

        # Clamp correctly here
        ex = int(min(self._n_cols - 1, (pos.x + size.x - 1e-9) // self._cell_size))
        ey = int(min(self._n_rows - 1, (pos.y + size.y - 1e-9) // self._cell_size))

        result: set[T] = set()

        for gy in range(sy, ey + 1):
            row_offset = gy * self._n_cols
            for gx in range(sx, ex + 1):
                result.update(self._cells[gx + row_offset])

        return list(result)

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


def vmax(val: Vector2, other: Vector2) -> Vector2:
    return Vector2(max(val.x, other.x), max(val.y, other.y))


def vmin(val: Vector2, other: Vector2) -> Vector2:
    return Vector2(min(val.x, other.x), min(val.y, other.y))


def cells_for_aabb(
    pos: Vector2, size: Vector2, cell_size: int, n_rows: int, n_cols: int
) -> list[int]:
    tl = pos // cell_size
    br = (pos + size) // cell_size
    v_cols = Vector2(n_cols - 1, n_rows - 1)
    tl = vmax(Vector2(), vmin(tl, v_cols))
    br = vmax(Vector2(), vmin(br, v_cols))

    indices: list[int] = []
    for y in range(int(tl.y), int(br.y) + 1):
        for x in range(int(tl.x), int(br.x) + 1):
            indices.append(x + y * n_cols)

    return indices
