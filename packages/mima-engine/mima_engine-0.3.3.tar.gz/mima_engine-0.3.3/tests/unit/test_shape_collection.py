from pygame.math import Vector2

from mima.advanced.shape import ShapeCollection
from mima.standalone.geometry import Circle, Rect


def test_shape_bounds():
    rect = Rect(Vector2(), Vector2(16, 16))
    circle = Circle(Vector2(4, 4), 8)

    sc = ShapeCollection(Vector2(2, 1), rect, circle)

    assert sc.tl == Vector2(-4, -4)
    assert sc.br == Vector2(16, 16)
    assert sc.bounding_box.pos == Vector2(-2, -3)
    assert sc.bounding_box.size == Vector2(20, 20)
    assert sc.shapes[0].pos == Vector2(2, 1)
    assert sc.shapes[1].pos == Vector2(6, 5)

def test_shape_bounds_circle():
    circle = Circle(Vector2(0.5, 0.5), 0.5)
    sc = ShapeCollection(Vector2(2, 1), circle)

    assert sc.tl == Vector2(0, 0)
    assert sc.br == Vector2(1, 1)
    assert sc.bounding_box.pos == Vector2(2, 1)
    assert sc.bounding_box.size == Vector2(1, 1)
    assert sc.shapes[0].pos == Vector2(2.5, 1.5)

    circle = Circle(Vector2(8, 11), 4)
    sc = ShapeCollection(Vector2(2, 1), circle)

    assert sc.tl == Vector2(4, 7)
    assert sc.br == Vector2(12, 15)
    assert sc.bounding_box.pos == Vector2(6, 8)
    assert sc.bounding_box.size == Vector2(8, 8)
    assert sc.shapes[0].pos == Vector2(10, 12)

def test_contains_rect():
    sc = ShapeCollection(
        Vector2(2, 1),
        Rect(Vector2(), Vector2(16, 16)),
        Circle(Vector2(4, 4), 8),
    )

    r1 = Rect(Vector2(20, 20), Vector2(16, 16))
    assert not sc.contains(r1)

    r2 = Rect(Vector2(), Vector2(16, 16))
    assert not sc.contains(r2)

    r3 = Rect(Vector2(13, -2), Vector2(2, 2))
    assert not sc.contains(r3)

    r4 = Rect(Vector2(5, -1), Vector2(1, 1))
    assert sc.contains(r4)

def test_overlaps_rect():
    sc = ShapeCollection(
        Vector2(2, 1),
        Rect(Vector2(), Vector2(16, 16)),
        Circle(Vector2(4, 4), 8),
    )

    r1 = Rect(Vector2(14, -4), Vector2(6, 4))
    assert not sc.overlaps(r1)

    r2 = Rect(Vector2(17, 16), Vector2(2, 2))
    assert sc.overlaps(r2)

    r3 = Rect(Vector2(5, -1), Vector2(1, 1))
    assert sc.overlaps(r3)

def test_resolve_collision():
    sc = ShapeCollection(
        Vector2(2, 1),
        Rect(Vector2(), Vector2(16, 16)),
        Circle(Vector2(4, 4), 8),
    )

    r1 = Rect(Vector2(17, 16), Vector2(2, 2))
    res = sc.resolve_collision(r1)
    assert res[0] == Vector2(1, 0)
    
    res = sc.resolve_collision(r1, True)
    assert res[0] == Vector2(1.5, 0.5)
    assert res[1] == Vector2(17.5, 16.5)

    r2 = Rect(Vector2(0,-1), Vector2(4, 4))
    res = sc.resolve_collision(r2)
    diff = res[0] - Vector2(5.65685, 4.65685)
    assert abs(diff.x) < 0.01 and abs(diff.y) < 0.01

    res =sc.resolve_collision(r2, True)
    diff1 = res[0] - Vector2(3.82843, 2.82843)
    assert abs(diff1.x) < 0.01 and abs(diff1.y) < 0.01
    diff2 = res[1] - Vector2(-1.82843, -2.82843)
    assert abs(diff2.x) < 0.01 and abs(diff2.y) < 0.01


if __name__ == "__main__":
    test_shape_bounds()
    test_shape_bounds_circle()
    test_contains_rect()
    test_overlaps_rect()
    test_resolve_collision()
