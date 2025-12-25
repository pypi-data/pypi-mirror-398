# noqa: E741
import math
from typing import Any, TypeAlias, overload

from pygame.math import Vector2

EPSILON = 1e-3


class Line:
    def __init__(
        self, start: Vector2 | None = None, end: Vector2 | None = None
    ) -> None:
        self.start: Vector2 = start if start is not None else Vector2()
        self.end: Vector2 = end if end is not None else Vector2()

    def vector(self) -> Vector2:
        """Get vector pointing from start to end"""
        return self.end - self.start

    def length(self) -> float:
        return self.vector().magnitude()

    def length2(self) -> float:
        return self.vector().magnitude_squared()

    def rpoint(self, distance: float) -> Vector2:
        """Get point along the line for a real distance."""
        return self.start + self.vector().normalize() * distance

    def upoint(self, distance: float) -> Vector2:
        """Get point along the line for a unit distance."""
        return self.start + self.vector() * distance

    def side(self, point: Vector2) -> int:
        """Return which side of the line does a point lie"""
        d = self.vector().cross(point - self.start)
        return -1 if d < 0 else 1 if d > 0 else 0

    def coefficients(self) -> Vector2:
        """Returns line equation coefficients.

        Calculates line equation "mx + a" coefficients where:
        x: m
        y: a

        Returns (inf, inf) when abs(end.x - start.x) < EPSILON
        """
        # Check if line is vertical or close to vertical
        if abs(self.end.x - self.start.y) < EPSILON:
            return Vector2(math.inf, math.inf)

        m = (self.end.y - self.start.y) / (self.end.x - self.start.x)
        return Vector2(m, -m * self.start.x + self.start.y)

    def __len__(self) -> float:
        return self.length()

    @property
    def pos(self) -> Vector2:
        return self.start

    @pos.setter
    def pos(self, pos: Vector2) -> None:
        self.start = pos


class Ray:
    def __init__(
        self, origin: Vector2 | None = None, direction: Vector2 | None = None
    ) -> None:
        self.origin: Vector2 = origin if origin is not None else Vector2()
        self.direction: Vector2 = direction if direction is not None else Vector2()


class Rect:
    def __init__(self, pos: Vector2 | None = None, size: Vector2 | None = None) -> None:
        self.pos: Vector2 = pos if pos is not None else Vector2()
        self.size: Vector2 = size if size is not None else Vector2()

    def middle(self) -> Vector2:
        """Get point in the center of the rectangle."""
        return self.pos + (self.size * 0.5)

    def top(self) -> Line:
        """Get line segment from top side of the rectangle."""
        return Line(self.pos, Vector2(self.pos.x + self.size.x, self.pos.y))

    def bottom(self) -> Line:
        """Get line segment from bottom side of the rectangle."""
        return Line(Vector2(self.pos.x, self.pos.y + self.size.y), self.pos + self.size)

    def left(self) -> Line:
        """Get line segment from left side of the rectangle."""
        return Line(self.pos, Vector2(self.pos.x, self.pos.y + self.size.y))

    def right(self) -> Line:
        """Get line segment from right side of the rectangle."""
        return Line(Vector2(self.pos.x + self.size.x, self.pos.y), self.pos + self.size)

    def side(self, index: int) -> Line:
        """Get a line from an indexed side.

        Starting top, going clockwise:
        0 = top
        1 = right
        2 = bottom
        3 = left

        """
        if index % 4 == 0:
            return self.top()
        elif index % 4 == 1:
            return self.right()
        elif index % 4 == 2:
            return self.bottom()
        else:
            return self.left()

    def area(self) -> float:
        """Get area of the rectangle."""
        return self.size.x * self.size.y

    def perimeter(self) -> float:
        """Get perimeter of the rectangle."""
        return 2.0 * (self.size.x + self.size.y)

    def side_count(self) -> int:
        return 4


class Circle:
    def __init__(self, pos: Vector2 | None = None, radius: float = 0.0) -> None:
        self.pos = pos if pos is not None else Vector2()
        self.radius = radius

    def area(self) -> float:
        return math.pi * self.radius**2

    def perimeter(self) -> float:
        return math.pi * self.radius * 2.0

    def circumference(self) -> float:
        return self.perimeter()


def clamp(val: float, low: float, high: float) -> float:
    return max(low, min(high, val))


def filter_duplicates(points: list[Vector2]) -> list[Vector2]:
    filtered = []
    for p in points:
        is_duplicate = False
        for fp in filtered:
            if abs(p.x - fp.x) < EPSILON and abs(p.y - fp.y) < EPSILON:
                is_duplicate = True
                break

        if not is_duplicate:
            filtered.append(p)

    return filtered


Shape: TypeAlias = Line | Rect | Circle


def shape_from_str(
    shape: str, pos: Vector2, pos2_or_size: Vector2, radius: float
) -> Shape:
    if shape == "circle":
        return Circle(pos, radius)
    elif shape == "rect":
        return Rect(pos, pos2_or_size)
    elif shape == "line":
        return Line(pos, pos2_or_size)

    msg = f"Unsupported shape {shape}. Use circle, line, or rect."
    raise ValueError(msg)


def shape_from_dict(shape_dict: dict[str, Any]) -> Shape:
    return shape_from_str(
        shape_dict["shape"], shape_dict["pos"], shape_dict["size"], shape_dict["radius"]
    )


@overload
def copy_shape(shape: Rect) -> Rect: ...
@overload
def copy_shape(shape: Circle) -> Circle: ...
@overload
def copy_shape(shape: Line) -> Line: ...


def copy_shape(shape: Shape) -> Shape:
    if isinstance(shape, Rect):
        return Rect(Vector2(shape.pos), Vector2(shape.size))
    elif isinstance(shape, Circle):
        return Circle(Vector2(shape.pos), shape.radius)
    elif isinstance(shape, Line):
        return Line(Vector2(shape.start), Vector2(shape.end))


@overload
def contains(g1: Vector2, g2: Vector2) -> bool: ...
@overload
def contains(g1: Vector2, g2: Line) -> bool: ...
@overload
def contains(g1: Vector2, g2: Rect) -> bool: ...
@overload
def contains(g1: Vector2, g2: Circle) -> bool: ...
@overload
def contains(g1: Line, g2: Vector2) -> bool: ...
@overload
def contains(g1: Line, g2: Line) -> bool: ...
@overload
def contains(g1: Line, g2: Rect) -> bool: ...
@overload
def contains(g1: Line, g2: Circle) -> bool: ...
@overload
def contains(g1: Rect, g2: Vector2) -> bool: ...
@overload
def contains(g1: Rect, g2: Line) -> bool: ...
@overload
def contains(g1: Rect, g2: Rect) -> bool: ...
@overload
def contains(g1: Rect, g2: Circle) -> bool: ...
@overload
def contains(g1: Circle, g2: Vector2) -> bool: ...
@overload
def contains(g1: Circle, g2: Line) -> bool: ...
@overload
def contains(g1: Circle, g2: Rect) -> bool: ...
@overload
def contains(g1: Circle, g2: Circle) -> bool: ...


def contains(g1: Vector2 | Shape, g2: Vector2 | Shape) -> bool:
    if isinstance(g1, Vector2):
        if isinstance(g2, Vector2):
            return _point_contains_point(g1, g2)
        elif isinstance(g2, Line):
            return False  # It can't!
        if isinstance(g2, Rect):
            return False  # It can't!
        elif isinstance(g2, Circle):
            return False  # It can't!
    elif isinstance(g1, Line):
        if isinstance(g2, Vector2):
            return _line_contains_point(g1, g2)
        elif isinstance(g2, Line):
            return _line_contains_line(g1, g2)
        elif isinstance(g2, Rect):
            return False  # It can't!
        elif isinstance(g2, Circle):
            return False  # It can't!
    elif isinstance(g1, Rect):
        if isinstance(g2, Vector2):
            return _rect_contains_point(g1, g2)
        elif isinstance(g2, Line):
            return _rect_contains_line(g1, g2)
        elif isinstance(g2, Rect):
            return _rect_contains_rect(g1, g2)
        elif isinstance(g2, Circle):
            return _rect_contains_circle(g1, g2)
    elif isinstance(g1, Circle):
        if isinstance(g2, Vector2):
            return _circle_contains_point(g1, g2)
        elif isinstance(g2, Line):
            return _circle_contains_line(g1, g2)
        elif isinstance(g2, Rect):
            return _circle_contains_rect(g1, g2)
        elif isinstance(g2, Circle):
            return _circle_contains_circle(g1, g2)

    msg = f"Unsupported types {type(g1)} and {type(g2)}"
    raise ValueError(msg)


# Point contains ...
def _point_contains_point(p1: Vector2, p2: Vector2) -> bool:
    return (p1 - p2).magnitude_squared() < EPSILON


# Line contains ...
def _line_contains_point(l: Line, p: Vector2) -> bool:  # noqa: E741
    d = (p.x - l.start.x) * (l.end.y - l.start.y) - (p.y - l.start.y) * (
        l.end.x - l.start.x
    )
    if abs(d) < EPSILON:
        # point is on line
        u = l.vector().dot(p - l.start) / l.vector().magnitude_squared()
        return 0.0 <= u <= 1.0
    return False


def _line_contains_line(l1: Line, l2: Line) -> bool:
    return overlaps(l1, l2.start) and overlaps(l1, l2.end)


# Rect contains ...
def _rect_contains_point(r1: Rect, p2: Vector2) -> bool:
    return not (
        p2.x < r1.pos.x
        or p2.y < r1.pos.y
        or p2.x > (r1.pos.x + r1.size.x)
        or p2.y > (r1.pos.y + r1.size.y)
    )


def _rect_contains_line(r: Rect, l: Line) -> bool:  # noqa: E741
    return contains(r, l.start) and contains(r, l.end)


def _rect_contains_rect(r1: Rect, r2: Rect) -> bool:
    return (
        (r2.pos.x >= r1.pos.x)
        and (r2.pos.x + r2.size.x <= r1.pos.x + r1.size.x)
        and (r2.pos.y >= r1.pos.y)
        and (r2.pos.y + r2.size.y <= r1.pos.y + r1.size.y)
    )


def _rect_contains_circle(r: Rect, c: Circle) -> bool:
    return (
        r.pos.x + c.radius <= c.pos.x
        and c.pos.x <= r.pos.x + r.size.x - c.radius
        and r.pos.y + c.radius <= c.pos.y
        and c.pos.y <= r.pos.y + r.size.y - c.radius
    )


# Circle contains ...
def _circle_contains_point(c1: Circle, p2: Vector2) -> bool:
    return (c1.pos - p2).magnitude_squared() <= c1.radius**2


def _circle_contains_line(c: Circle, l: Line) -> bool:  # noqa: E741
    return contains(c, l.start) and contains(c, l.end)


def _circle_contains_rect(c: Circle, r: Rect) -> bool:
    return (
        contains(c, r.pos)
        and contains(c, Vector2(r.pos.x + r.size.x, r.pos.y))
        and contains(c, Vector2(r.pos.x, r.pos.y + r.size.y))
        and contains(c, r.pos + r.size)
    )


def _circle_contains_circle(c1: Circle, c2: Circle) -> bool:
    return (
        math.sqrt((c2.pos.x - c1.pos.x) ** 2 + (c2.pos.y - c1.pos.y) ** 2) + c2.radius
    ) <= c1.radius


@overload
def closest(g1: Vector2, g2: Vector2) -> Vector2: ...
@overload
def closest(g1: Vector2, g2: Line) -> Vector2: ...
@overload
def closest(g1: Vector2, g2: Rect) -> Vector2: ...
@overload
def closest(g1: Vector2, g2: Circle) -> Vector2: ...
@overload
def closest(g1: Line, g2: Vector2) -> Vector2: ...
@overload
def closest(g1: Line, g2: Line) -> Vector2: ...
@overload
def closest(g1: Line, g2: Rect) -> Vector2: ...
@overload
def closest(g1: Line, g2: Circle) -> Vector2: ...
@overload
def closest(g1: Rect, g2: Vector2) -> Vector2: ...
@overload
def closest(g1: Rect, g2: Line) -> Vector2: ...
@overload
def closest(g1: Rect, g2: Rect) -> Vector2: ...
@overload
def closest(g1: Rect, g2: Circle) -> Vector2: ...
@overload
def closest(g1: Circle, g2: Vector2) -> Vector2: ...
@overload
def closest(g1: Circle, g2: Line) -> Vector2: ...
@overload
def closest(g1: Circle, g2: Rect) -> Vector2: ...
@overload
def closest(g1: Circle, g2: Circle) -> Vector2: ...


def closest(
    g1: Vector2 | Line | Rect | Circle, g2: Vector2 | Line | Rect | Circle
) -> Vector2:
    if isinstance(g1, Vector2):
        return g1
    elif isinstance(g1, Line):
        if isinstance(g2, Vector2):
            return _closest_point_on_line_to_point(g1, g2)
        elif isinstance(g2, Line):
            return _closest_point_on_line_to_line(g1, g2)
        elif isinstance(g2, Rect):
            return _closest_point_on_line_to_rect(g1, g2)
        elif isinstance(g2, Circle):
            return _closest_point_on_line_to_circle(g1, g2)
    elif isinstance(g1, Rect):
        if isinstance(g2, Vector2):
            return _closest_point_on_rect_to_point(g1, g2)
        elif isinstance(g2, Line):
            return _closest_point_on_rect_to_line(g1, g2)
        elif isinstance(g2, Rect):
            return _closest_point_on_rect_to_rect(g1, g2)
        elif isinstance(g2, Circle):
            return _closest_point_on_rect_to_circle(g1, g2)
    elif isinstance(g1, Circle):
        if isinstance(g2, Vector2):
            return _closest_point_on_circle_to_point(g1, g2)
        elif isinstance(g2, Line):
            return _closest_point_on_circle_to_line(g1, g2)
        elif isinstance(g2, Rect):
            return _closest_point_on_circle_to_rect(g1, g2)
        elif isinstance(g2, Circle):
            return _closest_point_on_circle_to_circle(g1, g2)

    msg = f"Unsupported types {type(g1)} and {type(g2)}"
    raise ValueError(msg)


# Closest point on Line to ...
def _closest_point_on_line_to_point(
    l: Line,  # noqa: E741
    p: Vector2,
) -> Vector2:
    d = l.vector()
    u = clamp(d.dot(p - l.start) / d.magnitude_squared(), 0.0, 1.0)
    return l.start + u * d


def _closest_point_on_line_to_line(l1: Line, l2: Line) -> Vector2:
    raise NotImplementedError


def _closest_point_on_line_to_rect(l: Line, r: Rect) -> Vector2:  # noqa: E741
    raise NotImplementedError


def _closest_point_on_line_to_circle(
    l: Line,  # noqa: E741
    c: Circle,  # noqa: E741
) -> Vector2:
    p = closest(c, l)
    return closest(l, p)


# Closest point on rectangle to ...
def _closest_point_on_rect_to_point(r: Rect, p: Vector2) -> Vector2:
    edges = [r.top(), r.bottom(), r.left(), r.right()]

    closest_to_edges = [closest(e, p) for e in edges]
    distance_to_edges = [(c - p).magnitude_squared() for c in closest_to_edges]

    dmin = distance_to_edges[0]
    cmin = closest_to_edges[0]
    for i in range(1, len(distance_to_edges)):
        if distance_to_edges[i] < dmin:
            dmin = distance_to_edges[i]
            cmin = closest_to_edges[i]
    return cmin


def _closest_point_on_rect_to_line(r: Rect, l: Line) -> Vector2:  # noqa: E741
    raise NotImplementedError


def _closest_point_on_rect_to_rect(r1: Rect, r2: Rect) -> Vector2:
    raise NotImplementedError


def _closest_point_on_rect_to_circle(r: Rect, c: Circle) -> Vector2:
    return Vector2(
        max(r.pos.x, min(c.pos.x, r.pos.x + r.size.x)),
        max(r.pos.y, min(c.pos.y, r.pos.y + r.size.y)),
    )


# Closest point on circle to ...
def _closest_point_on_circle_to_point(c: Circle, p: Vector2) -> Vector2:
    return c.pos + (p - c.pos).normalize() * c.radius


def _closest_point_on_circle_to_line(
    c: Circle,
    l: Line,  # noqa: E741
) -> Vector2:
    p = closest(l, c.pos)
    return c.pos + (p - c.pos).normalize() * c.radius


def _closest_point_on_circle_to_rect(c: Circle, r: Rect) -> Vector2:
    # Find the closest point on the rectangle to the center of the circle
    closest_point = Vector2(
        max(r.pos.x, min(c.pos.x, r.pos.x + r.size.x)),
        max(r.pos.y, min(c.pos.y, r.pos.y + r.size.y)),
    )

    # Compute the direction vector from the circle's center to the closest
    # rectangle point
    direction = closest_point - c.pos

    # Normalize the direction vector
    if direction.length() > 0:
        direction = direction.normalize()
    else:
        direction = Vector2(0, 0)

    # Scale the direction vector by the circle's radius and add the circle's
    # position
    return c.pos + direction * c.radius


def _closest_point_on_circle_to_circle(c1: Circle, c2: Circle) -> Vector2:
    return closest(c1, c2.pos)


@overload
def overlaps(g1: Vector2, g2: Vector2) -> bool: ...
@overload
def overlaps(g1: Vector2, g2: Line) -> bool: ...
@overload
def overlaps(g1: Vector2, g2: Rect) -> bool: ...
@overload
def overlaps(g1: Vector2, g2: Circle) -> bool: ...
@overload
def overlaps(g1: Line, g2: Vector2) -> bool: ...
@overload
def overlaps(g1: Line, g2: Line) -> bool: ...
@overload
def overlaps(g1: Line, g2: Rect) -> bool: ...
@overload
def overlaps(g1: Line, g2: Circle) -> bool: ...
@overload
def overlaps(g1: Rect, g2: Vector2) -> bool: ...
@overload
def overlaps(g1: Rect, g2: Line) -> bool: ...
@overload
def overlaps(g1: Rect, g2: Rect) -> bool: ...
@overload
def overlaps(g1: Rect, g2: Circle) -> bool: ...
@overload
def overlaps(g1: Circle, g2: Vector2) -> bool: ...
@overload
def overlaps(g1: Circle, g2: Line) -> bool: ...
@overload
def overlaps(g1: Circle, g2: Rect) -> bool: ...
@overload
def overlaps(g1: Circle, g2: Circle) -> bool: ...


def overlaps(
    g1: Vector2 | Line | Rect | Circle, g2: Vector2 | Line | Rect | Circle
) -> bool:
    if isinstance(g1, Vector2):
        if isinstance(g2, Vector2):
            return _point_overlaps_point(g1, g2)
        elif isinstance(g2, Line):
            return _point_overlaps_line(g1, g2)
        if isinstance(g2, Rect):
            return _point_overlaps_rect(g1, g2)
        elif isinstance(g2, Circle):
            return _point_overlaps_circle(g1, g2)
    elif isinstance(g1, Line):
        if isinstance(g2, Vector2):
            return _line_overlaps_point(g1, g2)
        elif isinstance(g2, Line):
            return _line_overlaps_line(g1, g2)
        elif isinstance(g2, Rect):
            return _line_overlaps_rect(g1, g2)
        elif isinstance(g2, Circle):
            return _line_overlaps_circle(g1, g2)
    elif isinstance(g1, Rect):
        if isinstance(g2, Vector2):
            return _rect_overlaps_point(g1, g2)
        elif isinstance(g2, Line):
            return _rect_overlaps_line(g1, g2)
        elif isinstance(g2, Rect):
            return _rect_overlaps_rect(g1, g2)
        elif isinstance(g2, Circle):
            return _rect_overlaps_circle(g1, g2)
    elif isinstance(g1, Circle):
        if isinstance(g2, Vector2):
            return _circle_overlaps_point(g1, g2)
        elif isinstance(g2, Line):
            return _circle_overlaps_line(g1, g2)
        elif isinstance(g2, Rect):
            return _circle_overlaps_rect(g1, g2)
        elif isinstance(g2, Circle):
            return _circle_overlaps_circle(g1, g2)

    msg = f"Unsupported types {type(g1)} and {type(g2)}"
    raise ValueError(msg)


# Point overlaps ...
def _point_overlaps_point(p1: Vector2, p2: Vector2) -> bool:
    return contains(p1, p2)


def _point_overlaps_line(p: Vector2, l: Line) -> bool:  # noqa: E741
    return contains(l, p)


def _point_overlaps_rect(p: Vector2, r: Rect) -> bool:
    return overlaps(r, p)


def _point_overlaps_circle(p: Vector2, c: Circle) -> bool:
    return overlaps(c, p)


# Line overlaps ...
def _line_overlaps_point(l: Line, p: Vector2) -> bool:  # noqa: E741
    return contains(l, p)


def _line_overlaps_line(l1: Line, l2: Line) -> bool:
    d = (l2.end.y - l2.start.y) * (l1.end.x - l1.start.x) - (l2.end.x - l2.start.x) * (
        l1.end.y - l1.start.y
    )
    ua = (
        (l2.end.x - l2.start.x) * (l1.start.y - l2.start.y)
        - (l2.end.y - l2.start.y) * (l1.start.x - l2.start.x)
    ) / d
    ub = (
        (l1.end.x - l1.start.x) * (l1.start.y - l2.start.y)
        - (l1.end.y - l1.start.y) * (l1.start.x - l2.start.x)
    ) / d
    return 0 <= ua <= 1 and 0 <= ub <= 1


def _line_overlaps_rect(l: Line, r: Rect) -> bool:  # noqa: E741
    return overlaps(r, l)


def _line_overlaps_circle(l: Line, c: Circle) -> bool:  # noqa: E741
    return overlaps(c, l)


# Rect overlaps ...
def _rect_overlaps_point(r: Rect, p: Vector2) -> bool:
    return contains(r, p)


def _rect_overlaps_line(r: Rect, l: Line) -> bool:  # noqa: E741
    return (
        contains(r, l.start)
        or overlaps(r.top(), l)
        or overlaps(r.bottom(), l)
        or overlaps(r.right(), l)
    )


def _rect_overlaps_rect(r1: Rect, r2: Rect) -> bool:
    return (
        r1.pos.x <= r2.pos.x + r2.size.x
        and r1.pos.x + r1.size.x >= r2.pos.x
        and r1.pos.y <= r2.pos.y + r2.size.y
        and r1.pos.y + r1.size.y >= r2.pos.y
    )


def _rect_overlaps_circle(r: Rect, c: Circle) -> bool:
    return overlaps(c, r)


# Circle overlaps ...
def _circle_overlaps_point(c: Circle, p: Vector2) -> bool:
    return contains(c, p)


def _circle_overlaps_line(c: Circle, l: Line) -> bool:  # noqa: E741
    closest_p = closest(l, c.pos)
    return (c.pos - closest_p).magnitude_squared() <= (c.radius**2)


def _circle_overlaps_rect(c: Circle, r: Rect) -> bool:
    overlap = (
        Vector2(
            clamp(c.pos.x, r.pos.x, r.pos.x + r.size.x),
            clamp(c.pos.y, r.pos.y, r.pos.y + r.size.y),
        )
        - c.pos
    ).magnitude_squared()
    # TODO: if (std::isnan(overlap)) overlap = 0
    return (overlap - (c.radius**2)) < 0


def _circle_overlaps_circle(c1: Circle, c2: Circle) -> bool:
    return (c1.pos - c2.pos).magnitude_squared() <= (c1.radius + c2.radius) * (
        c1.radius + c2.radius
    )


@overload
def intersects(g1: Vector2, g2: Vector2) -> list[Vector2]: ...
@overload
def intersects(g1: Vector2, g2: Line) -> list[Vector2]: ...
@overload
def intersects(g1: Vector2, g2: Rect) -> list[Vector2]: ...
@overload
def intersects(g1: Vector2, g2: Circle) -> list[Vector2]: ...
@overload
def intersects(g1: Line, g2: Vector2) -> list[Vector2]: ...
@overload
def intersects(g1: Line, g2: Line) -> list[Vector2]: ...
@overload
def intersects(g1: Line, g2: Rect) -> list[Vector2]: ...
@overload
def intersects(g1: Line, g2: Circle) -> list[Vector2]: ...
@overload
def intersects(g1: Rect, g2: Vector2) -> list[Vector2]: ...
@overload
def intersects(g1: Rect, g2: Line) -> list[Vector2]: ...
@overload
def intersects(g1: Rect, g2: Rect) -> list[Vector2]: ...
@overload
def intersects(g1: Rect, g2: Circle) -> list[Vector2]: ...
@overload
def intersects(g1: Circle, g2: Vector2) -> list[Vector2]: ...
@overload
def intersects(g1: Circle, g2: Line) -> list[Vector2]: ...
@overload
def intersects(g1: Circle, g2: Rect) -> list[Vector2]: ...
@overload
def intersects(g1: Circle, g2: Circle) -> list[Vector2]: ...


def intersects(
    g1: Vector2 | Line | Rect | Circle, g2: Vector2 | Line | Rect | Circle
) -> list[Vector2]:
    if isinstance(g1, Vector2):
        if isinstance(g2, Vector2):
            return _point_intersects_point(g1, g2)
        elif isinstance(g2, Line):
            return _point_intersects_line(g1, g2)
        if isinstance(g2, Rect):
            return _point_intersects_rect(g1, g2)
        elif isinstance(g2, Circle):
            return _point_intersects_circle(g1, g2)
    elif isinstance(g1, Line):
        if isinstance(g2, Vector2):
            return _line_intersects_point(g1, g2)
        elif isinstance(g2, Line):
            return _line_intersects_line(g1, g2)
        elif isinstance(g2, Rect):
            return _line_intersects_rect(g1, g2)
        elif isinstance(g2, Circle):
            return _line_intersects_circle(g1, g2)
    elif isinstance(g1, Rect):
        if isinstance(g2, Vector2):
            return _rect_intersects_point(g1, g2)
        elif isinstance(g2, Line):
            return _rect_intersects_line(g1, g2)
        elif isinstance(g2, Rect):
            return _rect_intersects_rect(g1, g2)
        elif isinstance(g2, Circle):
            return _rect_intersects_circle(g1, g2)
    elif isinstance(g1, Circle):
        if isinstance(g2, Vector2):
            return _circle_intersects_point(g1, g2)
        elif isinstance(g2, Line):
            return _circle_intersects_line(g1, g2)
        elif isinstance(g2, Rect):
            return _circle_intersects_rect(g1, g2)
        elif isinstance(g2, Circle):
            return _circle_intersects_circle(g1, g2)

    msg = f"Unsupported types {type(g1)} and {type(g2)}"
    raise ValueError(msg)


# Point intersects ...
def _point_intersects_point(p1: Vector2, p2: Vector2) -> list[Vector2]:
    return [p1] if contains(p1, p2) else []


def _point_intersects_line(p: Vector2, l: Line) -> list[Vector2]:  # noqa: E741
    return intersects(l, p)


def _point_intersects_rect(p: Vector2, r: Rect) -> list[Vector2]:
    return intersects(r, p)


def _point_intersects_circle(p: Vector2, c: Circle) -> list[Vector2]:
    return intersects(c, p)


# Line intersects ...
def _line_intersects_point(l: Line, p: Vector2) -> list[Vector2]:  # noqa: E741
    return [p] if contains(l, p) else []


def _line_intersects_line(l1: Line, l2: Line, infinite: bool = False) -> list[Vector2]:
    rd = l1.vector().cross(l2.vector())
    if rd == 0:
        # Parallel or Colinear TODO: return two points
        return []

    rd = 1.0 / rd
    rn = (
        (l2.end.x - l2.start.x) * (l1.start.y - l2.start.y)
        - (l2.end.y - l2.start.y) * (l1.start.x - l2.start.x)
    ) * rd
    sn = (
        (l1.end.x - l1.start.x) * (l1.start.y - l2.start.y)
        - (l1.end.y - l1.start.y) * (l1.start.x - l2.start.x)
    ) * rd

    if not infinite and (rn < 0.0 or rn > 1.0 or sn < 0.0 or sn > 1.0):
        return []  # Intersection not within line segment
    return [l1.start + rn * l1.vector()]


def _line_intersects_rect(l: Line, r: Rect) -> list[Vector2]:  # noqa: E741
    return intersects(r, l)


def _line_intersects_circle(l: Line, c: Circle) -> list[Vector2]:  # noqa: E741
    return intersects(c, l)


# Rect intersects ...
def _rect_intersects_point(r: Rect, p: Vector2) -> list[Vector2]:
    for i in range(r.side_count()):
        if contains(r.side(i), p):
            return [p]
    return []


def _rect_intersects_line(r: Rect, l: Line) -> list[Vector2]:  # noqa: E741
    intersections = []
    for i in range(r.side_count()):
        intersections.extend(intersects(r.side(i), l))

    return filter_duplicates(intersections)


def _rect_intersects_rect(r1: Rect, r2: Rect) -> list[Vector2]:
    intersections = []
    for i in range(r2.side_count()):
        intersections.extend(intersects(r1, r2.side(i)))

    return filter_duplicates(intersections)


def _rect_intersects_circle(r: Rect, c: Circle) -> list[Vector2]:
    return intersects(c, r)


# Circle intersects ...
def _circle_intersects_point(c: Circle, p: Vector2) -> list[Vector2]:
    if abs((p - c.pos).magnitude_squared() - (c.radius**2)) <= EPSILON:
        return [p]
    return []


def _circle_intersects_line(c: Circle, l: Line) -> list[Vector2]:  # noqa: E741
    closest_point_to_segment = closest(l, c.pos)

    if overlaps(c, closest_point_to_segment):
        # Circle is too far away
        return []

    # Compute closest to the circle on the line
    d = l.vector()
    u_line = d.dot(c.pos - l.start) / d.magnitude_squared()
    closest_point_to_line = l.start + u_line * d
    dist_to_line = (c.pos - closest_point_to_line).magnitude_squared()

    if abs(dist_to_line - c.radius**2) < EPSILON:
        # Circle "kisses" the line
        return [closest_point_to_line]

    # Circle intersects the line
    length = math.sqrt(c.radius**2 - dist_to_line)
    p1 = closest_point_to_line + l.vector().normalize() * length
    p2 = closest_point_to_line - l.vector().normalize() * length

    intersections = []
    if (p1 - closest(l, p1)).magnitude_squared() < EPSILON**2:
        intersections.append(p1)
    if (p2 - closest(l, p2)).magnitude_squared() < EPSILON**2:
        intersections.append(p2)

    return filter_duplicates(intersections)


def _circle_intersects_rect(c: Circle, r: Rect) -> list[Vector2]:
    intersections = []
    for i in range(r.side_count()):
        intersections.extend(intersects(c, r.side(i)))

    return filter_duplicates(intersections)


def _circle_intersects_circle(c1: Circle, c2: Circle) -> list[Vector2]:
    if c1.pos == c2.pos:
        # Circles are either within one another so cannot intersect or
        # are identical so share all point but this cannot be
        # represented in a good way in the return value
        return []

    between = c2.pos - c1.pos
    dist2 = between.magnitude_squared()
    radius_sum = c1.radius + c2.radius
    if dist2 > radius_sum**2:
        # Circles are too far apart to be touching
        return []
    if contains(c1, c2) or contains(c2, c1):
        # One circle is inside of the other, they can't be intersecting
        return []
    if dist2 == radius_sum:
        # Circles are touching at exactly 1 point
        return [Vector2(c1.pos + between.normalize() * c1.radius)]

    # Otherwise, they're touching at 2 points
    dist = math.sqrt(dist2)
    cc_dist = (dist2 + c1.radius**2 - c2.radius**2) / (2 * dist)
    chord_center = c1.pos + between.normalize() * cc_dist
    half_chord = between.normalize().rotate(-90) * math.sqrt(
        c1.radius**2 - cc_dist**2
    )  # FIXME: 90 or -90
    return [chord_center + half_chord, chord_center - half_chord]


@overload
def resolve_collision(
    g1: Vector2, g2: Vector2, move_both: bool = False
) -> tuple[Vector2, Vector2]: ...
@overload
def resolve_collision(
    g1: Vector2, g2: Line, move_both: bool = False
) -> tuple[Vector2, Vector2]: ...
@overload
def resolve_collision(
    g1: Vector2, g2: Rect, move_both: bool = False
) -> tuple[Vector2, Vector2]: ...
@overload
def resolve_collision(
    g1: Vector2, g2: Circle, move_both: bool = False
) -> tuple[Vector2, Vector2]: ...
@overload
def resolve_collision(
    g1: Line, g2: Vector2, move_both: bool = False
) -> tuple[Vector2, Vector2]: ...
@overload
def resolve_collision(
    g1: Line, g2: Line, move_both: bool = False
) -> tuple[Vector2, Vector2]: ...
@overload
def resolve_collision(
    g1: Line, g2: Rect, move_both: bool = False
) -> tuple[Vector2, Vector2]: ...
@overload
def resolve_collision(
    g1: Line, g2: Circle, move_both: bool = False
) -> tuple[Vector2, Vector2]: ...
@overload
def resolve_collision(
    g1: Rect, g2: Vector2, move_both: bool = False
) -> tuple[Vector2, Vector2]: ...
@overload
def resolve_collision(
    g1: Rect, g2: Line, move_both: bool = False
) -> tuple[Vector2, Vector2]: ...
@overload
def resolve_collision(
    g1: Rect, g2: Rect, move_both: bool = False
) -> tuple[Vector2, Vector2]: ...
@overload
def resolve_collision(
    g1: Rect, g2: Circle, move_both: bool = False
) -> tuple[Vector2, Vector2]: ...
@overload
def resolve_collision(
    g1: Circle, g2: Vector2, move_both: bool = False
) -> tuple[Vector2, Vector2]: ...
@overload
def resolve_collision(
    g1: Circle, g2: Line, move_both: bool = False
) -> tuple[Vector2, Vector2]: ...
@overload
def resolve_collision(
    g1: Circle, g2: Rect, move_both: bool = False
) -> tuple[Vector2, Vector2]: ...
@overload
def resolve_collision(
    g1: Circle, g2: Circle, move_both: bool = False
) -> tuple[Vector2, Vector2]: ...


def resolve_collision(
    g1: Vector2 | Line | Rect | Circle,
    g2: Vector2 | Line | Rect | Circle,
    move_both: bool = False,
) -> tuple[Vector2, Vector2]:
    if isinstance(g1, Vector2):
        if isinstance(g2, Vector2):
            return _point_collides_with_point(g1, g2, move_both)
        elif isinstance(g2, Line):
            return _point_collides_with_line(g1, g2, move_both)
        if isinstance(g2, Rect):
            return _point_collides_with_rect(g1, g2, move_both)
        elif isinstance(g2, Circle):
            return _point_collides_with_circle(g1, g2, move_both)
    elif isinstance(g1, Line):
        if isinstance(g2, Vector2):
            return _line_collides_with_point(g1, g2, move_both)
        elif isinstance(g2, Line):
            return _line_collides_with_line(g1, g2, move_both)
        elif isinstance(g2, Rect):
            return _line_collides_with_rect(g1, g2, move_both)
        elif isinstance(g2, Circle):
            return _line_collides_with_circle(g1, g2, move_both)
    elif isinstance(g1, Rect):
        if isinstance(g2, Vector2):
            return _rect_collides_with_point(g1, g2, move_both)
        elif isinstance(g2, Line):
            return _rect_collides_with_line(g1, g2, move_both)
        elif isinstance(g2, Rect):
            return _rect_collides_with_rect(g1, g2, move_both)
        elif isinstance(g2, Circle):
            return _rect_collides_with_circle(g1, g2, move_both)
    elif isinstance(g1, Circle):
        if isinstance(g2, Vector2):
            return _circle_collides_with_point(g1, g2, move_both)
        elif isinstance(g2, Line):
            return _circle_collides_with_line(g1, g2, move_both)
        elif isinstance(g2, Rect):
            return _circle_collides_with_rect(g1, g2, move_both)
        elif isinstance(g2, Circle):
            return _circle_collides_with_circle(g1, g2, move_both)

    msg = f"Unsupported types {type(g1)} and {type(g2)}"
    raise ValueError(msg)


# Point collides_with ...
def _point_collides_with_point(
    p1: Vector2, p2: Vector2, move_both: bool = False
) -> tuple[Vector2, Vector2]:
    raise NotImplementedError


def _point_collides_with_line(
    p1: Vector2, l2: Line, move_both: bool = False
) -> tuple[Vector2, Vector2]:
    raise NotImplementedError


def _point_collides_with_rect(
    p1: Vector2, r2: Rect, move_both: bool = False
) -> tuple[Vector2, Vector2]:
    raise NotImplementedError


def _point_collides_with_circle(
    p1: Vector2, c2: Circle, move_both: bool = False
) -> tuple[Vector2, Vector2]:
    raise NotImplementedError


# Line collides_with ...
def _line_collides_with_point(
    l1: Line, p2: Vector2, move_both: bool = False
) -> tuple[Vector2, Vector2]:
    raise NotImplementedError


def _line_collides_with_line(
    l1: Line, l2: Line, move_both: bool = False
) -> tuple[Vector2, Vector2]:
    raise NotImplementedError


def _line_collides_with_rect(
    l1: Line, r2: Rect, move_both: bool = False
) -> tuple[Vector2, Vector2]:
    raise NotImplementedError


def _line_collides_with_circle(
    l1: Line, c2: Circle, move_both: bool = False
) -> tuple[Vector2, Vector2]:
    raise NotImplementedError


# Rect collides_with ...
def _rect_collides_with_point(
    r1: Rect, p2: Vector2, move_both: bool = False
) -> tuple[Vector2, Vector2]:
    raise NotImplementedError


def _rect_collides_with_line(
    r1: Rect, l2: Line, move_both: bool = False
) -> tuple[Vector2, Vector2]:
    raise NotImplementedError


def _rect_collides_with_rect(
    r1: Rect, r2: Rect, move_both: bool = False
) -> tuple[Vector2, Vector2]:
    """Calculate the collision between two rectangles.

    This function calculates the overlap of two rectangles r1 and r2
    and returns the new positions of both rectangles as tuple. By
    default, only the first rectangle will be moved and the second will
    be considered 'solid'. This can be changed with the move_both flag.
    In that case, both rectangles will be pushed away from each other
    by the same amount.

    Args:
        r1: Rectangle with `pos` and `size`
        r2: Second rectangle, solid by default
        move_both: If True, both rectangles will be moved.

    Returns:
        Tuple with the new positions of the rectangles.
    """

    # Calculate the horizontal (X) and vertical (Y) overlap
    br1 = r1.pos + r1.size
    br2 = r2.pos + r2.size
    overlap = vmin(br1, br2) - vmax(r1.pos, r2.pos)

    if overlap.x <= 0 or overlap.y <= 0:
        return r1.pos, r2.pos

    # Check if both rectangles have the same center point
    r1_center = r1.pos + r1.size / 2.0
    r2_center = r2.pos + r2.size / 2.0
    if r1_center == r2_center:
        # Special case: Both rectangles have identical center points
        # In this case, one (or both) of the rectangles will get a
        # Small adjustment to break perfect overlap
        push = Vector2(0.1, 0.1)
        if move_both:
            new_pos1 = r1.pos - push / 2.0
            new_pos2 = r2.pos + push / 2.0
        else:
            new_pos1 = r1.pos - push
            new_pos2 = r2.pos
        return new_pos1, new_pos2

    push = Vector2()
    # Resolve horizontal overlap
    if overlap.x > 0:
        roverlap = br2.x - r1.pos.x
        loverlap = br1.x - r2.pos.x
        if roverlap < loverlap:
            push.x = roverlap
        else:
            push.x = -loverlap

    # Resolve vertical overlap
    if overlap.y > 0:
        boverlap = br2.y - r1.pos.y
        toverlap = br1.y - r2.pos.y
        if boverlap < toverlap:
            push.y = boverlap
        else:
            push.y = -toverlap

    # Calculate new positions based on the move_both flag
    if move_both:
        new_pos1 = r1.pos + push / 2
        new_pos2 = r2.pos - push / 2
    else:
        new_pos1 = r1.pos + push
        new_pos2 = r2.pos
    return new_pos1, new_pos2


def _rect_collides_with_circle(
    r: Rect, c: Circle, move_both: bool = False
) -> tuple[Vector2, Vector2]:
    closest_point = closest(c, r)
    ray = closest_point - c.pos
    overlap = c.radius - ray.magnitude()
    # TODO: std::isnan(overlap): overlap=0
    new_pos1 = Vector2(r.pos.x, r.pos.y)
    new_pos2 = Vector2(c.pos.x, c.pos.y)
    try:
        ray.normalize()
    except ValueError:
        # breakpoint()
        overlap = 0

    if overlap > 0:
        if move_both:
            new_pos1 -= ray.normalize() * overlap * 0.5
            new_pos2 += ray.normalize() * overlap * 0.5
        else:
            new_pos1 -= ray.normalize() * overlap

    return new_pos1, new_pos2


# Circle collides_with ...
def _circle_collides_with_point(
    c1: Circle, p2: Vector2, move_both: bool = False
) -> tuple[Vector2, Vector2]:
    raise NotImplementedError


def _circle_collides_with_line(
    c1: Circle, l2: Line, move_both: bool = False
) -> tuple[Vector2, Vector2]:
    raise NotImplementedError


def _circle_collides_with_rect(
    c: Circle, r: Rect, move_both: bool = False
) -> tuple[Vector2, Vector2]:
    new_pos1 = Vector2(c.pos.x, c.pos.y)
    new_pos2 = Vector2(r.pos.x, r.pos.y)

    closest_point = closest(r, c)
    # ray = closest_point - c.pos
    # overlap = c.radius - ray.magnitude()
    # TODO: std::isnan(overlap): overlap=0
    # try:
    #     ray.normalize()
    # except ValueError:
    #     # breakpoint()
    #     overlap = 0

    # if overlap > 0:
    #     if move_both:
    #         new_pos1 -= ray.normalize() * overlap * 0.5
    #         new_pos2 += ray.normalize() * overlap * 0.5
    #     else:
    #         new_pos1 -= ray.normalize() * overlap

    delta = c.pos - closest_point
    dist_sq = delta.length_squared()
    if dist_sq == 0:
        dx = min(abs(c.pos.x - r.left().pos.x), abs(c.pos.x - r.right().pos.x))
        dy = min(abs(c.pos.y - r.top().pos.y), abs(c.pos.y - r.bottom().pos.y))
        if dx < dy:
            normal = Vector2(1, 0) if c.pos.x > r.middle().x else Vector2(-1, 0)
        else:
            normal = Vector2(0, 1) if c.pos.y > r.middle().y else Vector2(0, -1)
        distance = 0
    else:
        distance = math.sqrt(dist_sq)
        normal = delta / distance

    penetration = c.radius - distance
    if move_both:
        new_pos1 += normal * penetration * 0.5
        new_pos2 -= normal * penetration * 0.5
    else:
        new_pos1 += normal * penetration
    return new_pos1, new_pos2


def _circle_collides_with_circle(
    c1: Circle, c2: Circle, move_both: bool = False
) -> tuple[Vector2, Vector2]:
    new_pos1 = Vector2(c1.pos.x, c1.pos.y)
    new_pos2 = Vector2(c2.pos.x, c2.pos.y)

    # distance = (c1.pos - c2.pos).magnitude()
    # overlap = distance - c1.radius - c2.radius

    # offset = c1.pos - c2.pos

    # if distance == 0:
    #     offset = Vector2(overlap, overlap)
    # else:
    #     offset *= overlap / distance

    # if move_both:
    #     new_pos1 -= offset * 0.5
    #     new_pos2 += offset * 0.5
    # else:
    #     new_pos1 -= offset
    delta = c1.pos - c2.pos
    dist_sq = delta.length_squared()

    if dist_sq == 0:
        # Deterministic fallback
        normal = Vector2(1, 0) if id(c1) < id(c2) else Vector2(-1, 0)
        distance = 0
    else:
        distance = math.sqrt(dist_sq)
        normal = delta / distance

    penetration = c1.radius + c2.radius - distance
    if penetration <= 0:
        return new_pos1, new_pos2

    if move_both:
        correction = normal * (penetration * 0.5)
        return new_pos1 + correction, new_pos2 - correction

    return new_pos1 + normal * penetration, new_pos2


def vmax(val: Vector2, other: Vector2) -> Vector2:
    return Vector2(max(val.x, other.x), max(val.y, other.y))


def vmin(val: Vector2, other: Vector2) -> Vector2:
    return Vector2(min(val.x, other.x), min(val.y, other.y))
