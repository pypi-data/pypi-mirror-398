import pytest
from pygame import Vector2

from mima.standalone.spatial import SpatialGrid


@pytest.fixture
def empty_grid() -> SpatialGrid[int]:
    return SpatialGrid[int](Vector2(10, 10), 2)


@pytest.fixture()
def spatial_grid() -> SpatialGrid[int]:
    grid = SpatialGrid[int](Vector2(10, 10), 2)
    grid.insert(0, Vector2(3, 4), Vector2(0.2, 0.2))  # Cell 11
    grid.insert(1, Vector2(1.5, 7), Vector2(0.2, 0.2))  # Cell 15
    grid.insert(2, Vector2(8, 5), Vector2(0.2, 0.2))  # Cell 14
    grid.insert(3, Vector2(2, 1), Vector2(0.2, 0.2))  # Cell 1
    grid.insert(4, Vector2(2, 1), Vector2(0.2, 0.2))  # Cell 1
    grid.insert(5, Vector2(2, 3), Vector2(0.2, 0.2))  # Cell 2
    return grid


@pytest.fixture()
def large_object_grid() -> SpatialGrid[int]:
    grid = SpatialGrid[int](Vector2(10, 10), 2)

    grid.insert(0, Vector2(3, 4), Vector2(1, 1))  # cell 11
    grid.insert(1, Vector2(0, 5), Vector2(4, 4))
    grid.insert(2, Vector2(0, 9), Vector2(0.2, 0.2))
    return grid


@pytest.mark.parametrize(
    "pos, expected_cell", [((1.5, 1), 0), ((2.5, 1), 1), ((20, 20), 24)]
)
def test_insert(
    empty_grid: SpatialGrid[int], pos: tuple[int, int], expected_cell: int
) -> None:
    """Test insertion of objects.

    Todo:
        * Inserting out-of-bounds will add objects to border cells. Check if
          this is the expected behavior for spatial grids.

    """
    empty_grid.insert(0, Vector2(pos))

    assert empty_grid.n_objects == 1
    assert 0 in empty_grid._cells[expected_cell]


def test_insert_large_object(empty_grid: SpatialGrid[int]) -> None:
    pos = Vector2(3, 3)
    size = Vector2(4, 5.5)
    indices = [6, 7, 8, 11, 12, 13, 16, 17, 18, 21, 22, 23]

    empty_grid.insert(0, pos, size)

    assert empty_grid.n_objects == 1
    assert empty_grid._object_map[0] == indices
    for idx in indices:
        assert 0 in empty_grid._cells[idx]


@pytest.mark.parametrize("obj, expected_cell", [(0, 11)])
def test_remove(spatial_grid: SpatialGrid[int], obj: int, expected_cell: int) -> None:
    """Test removal of objects."""

    assert spatial_grid.n_objects == 6
    assert len(spatial_grid._cells[expected_cell]) == 1
    assert obj in spatial_grid._object_map

    spatial_grid.remove(obj)

    assert spatial_grid.n_objects == 5
    assert len(spatial_grid._cells[expected_cell]) == 0
    assert obj not in spatial_grid._object_map


def test_remove_object_not_in_grid(spatial_grid: SpatialGrid[int]) -> None:
    assert spatial_grid.n_objects == 6
    assert 6 not in spatial_grid._object_map

    spatial_grid.remove(6)

    assert spatial_grid.n_objects == 6
    assert 6 not in spatial_grid._object_map


@pytest.mark.parametrize(
    "obj,indices", [(0, [11, 12]), (1, [10, 11, 12, 15, 16, 17, 20, 21, 22]), (2, [20])]
)
def test_remove_large_object(
    large_object_grid: SpatialGrid[int], obj: int, indices: list[int]
) -> None:
    for idx in indices:
        assert obj in large_object_grid._cells[idx]
    assert large_object_grid.n_objects == 3

    large_object_grid.remove(obj)

    for idx in indices:
        assert obj not in large_object_grid._cells[idx]
    assert large_object_grid.n_objects == 2


def test_relocate(spatial_grid):
    assert spatial_grid._object_map[3] == [1]
    assert len(spatial_grid._cells[1]) == 2
    assert 3 in spatial_grid._cells[1]
    assert len(spatial_grid._cells[2]) == 0

    spatial_grid.relocate(3, Vector2(4, 1), Vector2(0.2, 0.2))

    assert spatial_grid._object_map[3] == [2]
    assert len(spatial_grid._cells[1]) == 1
    assert 3 not in spatial_grid._cells[1]
    assert len(spatial_grid._cells[2]) == 1
    assert 3 in spatial_grid._cells[2]


@pytest.mark.parametrize("new_pos, expected_indices", [((4, 1), [2]), ((0, 0), [0])])
def test_relocate_object_not_in_grid(
    spatial_grid: SpatialGrid[int],
    new_pos: tuple[int, int],
    expected_indices: list[int],
) -> None:
    assert spatial_grid.n_objects == 6
    assert 6 not in spatial_grid._object_map

    spatial_grid.relocate(6, Vector2(new_pos), Vector2(0.2, 0.2))

    assert spatial_grid.n_objects == 7
    assert 6 in spatial_grid._object_map
    assert spatial_grid._object_map[6] == expected_indices
    assert 6 in spatial_grid._cells[expected_indices[0]]


@pytest.mark.parametrize(
    "obj,pos,size,old_indices, new_indices",
    [
        (0, (6, 2), (1, 1), [11, 12], [8]),
        (
            1,
            (4, 4),
            (4, 4),
            [10, 11, 12, 15, 16, 17, 20, 21, 22],
            [12, 13, 14, 17, 18, 19, 22, 23, 24],
        ),
    ],
)
def test_relocate_large_object(
    large_object_grid: SpatialGrid[int],
    obj: int,
    pos: tuple[float, float],
    size: tuple[float, float],
    old_indices: list[int],
    new_indices: list[int],
) -> None:
    for idx in old_indices:
        assert obj in large_object_grid._cells[idx]
    for idx in new_indices:
        if idx not in old_indices:
            assert obj not in large_object_grid._cells[idx]

    large_object_grid.relocate(obj, Vector2(pos), Vector2(size))

    for idx in old_indices:
        if idx not in new_indices:
            assert obj not in large_object_grid._cells[idx]
    for idx in new_indices:
        assert obj in large_object_grid._cells[idx]


@pytest.mark.parametrize(
    "pos, size, n_objects",
    [((2.5, 2), (2, 3), 2), ((1.5, 0), (4, 4), 3), ((4, 5), (4, 4), 0)],
)
def test_get_objects_in_region(
    spatial_grid: SpatialGrid[int],
    pos: tuple[float, float],
    size: tuple[float, float],
    n_objects: int,
) -> None:
    objects = spatial_grid.get_objects_in_region(Vector2(pos), Vector2(size))

    assert len(objects) == n_objects


@pytest.mark.parametrize("pos, size, n_objects", [((0, 3), (4, 4), 2)])
def test_get_large_objects_in_region(
    large_object_grid,
    pos: tuple[float, float],
    size: tuple[float, float],
    n_objects: int,
) -> None:
    objects = large_object_grid.get_objects_in_region(Vector2(pos), Vector2(size))

    assert len(objects) == n_objects


def print_grid(spatial_grid: SpatialGrid[int]) -> str:
    s = ""
    for y in range(spatial_grid._n_rows):
        for x in range(spatial_grid._n_cols):
            idx = x + y * spatial_grid._n_cols
            s += f"{str(spatial_grid._cells[idx]):>7}"
        s += "\n"
    print(s)
    return s
