from pygame import Vector2

from mima.standalone.geometry import (
    Circle,
    Rect,
    Shape,
    contains,
    copy_shape,
    overlaps,
    resolve_collision,
    vmax,
    vmin,
)

VZERO = Vector2()


class ShapeCollection:
    def __init__(self, pos: Vector2 | None = None, *shapes: Shape):
        self.pos: Vector2 = Vector2() if pos is None else pos
        self._ori_shapes: list[Shape] = list(shapes)
        self.shapes: list[Shape] = []

        self.tl = Vector2()
        self.br = Vector2()

        for shape in self._ori_shapes:
            if isinstance(shape, Rect):
                if self.tl == VZERO:
                    self.tl = shape.pos
                else:
                    self.tl = vmin(self.tl, shape.pos)
                self.br = vmax(self.br, shape.pos + shape.size)
            if isinstance(shape, Circle):
                shape_tl = shape.pos.elementwise() - shape.radius
                if self.tl == VZERO:
                    self.tl = shape_tl
                else:
                    self.tl = vmin(self.tl, shape_tl)
                self.br = vmax(self.br, shape_tl.elementwise() + 2 * shape.radius)
        for shape in self._ori_shapes:
            new_shape = copy_shape(shape)
            new_shape.pos = shape.pos + self.pos
            self.shapes.append(new_shape)
        self.bounding_box = Rect(self.pos + self.tl, self.br - self.tl)

    def update(self, pos: Vector2) -> None:
        self.pos = pos
        self.bounding_box.pos = self.pos + self.tl
        for i, s in enumerate(self.shapes):
            s.pos = self.pos + self._ori_shapes[i].pos

    def contains(self, shape: Vector2 | Shape) -> bool:
        self.bounding_box.pos = self.pos + self.tl
        if not contains(self.bounding_box, shape):
            return False

        for i, s in enumerate(self.shapes):
            s.pos = self.pos + self._ori_shapes[i].pos
            if contains(s, shape):
                return True

        return False

    def overlaps(self, shape: Vector2 | Shape) -> bool:
        self.bounding_box.pos = self.pos + self.tl
        if not overlaps(self.bounding_box, shape):
            return False

        for i, s in enumerate(self.shapes):
            s.pos = self.pos + self._ori_shapes[i].pos
            if overlaps(s, shape):
                return True

        return False

    def resolve_collision(
        self, shape: Shape, move_both: bool = False
    ) -> tuple[Vector2, Vector2]:
        delta = Vector2()
        shape = copy_shape(shape)
        for i, s in enumerate(self.shapes):
            s.pos = self.pos + self._ori_shapes[i].pos + delta
            res = resolve_collision(s, shape, move_both)

            delta = res[0] - s.pos + delta
            if move_both:
                shape.pos = res[1]

        return self.pos + delta, shape.pos

    def get_tl_pos(self) -> Vector2:
        return self.pos + self.tl

    def get_br_pos(self) -> Vector2:
        return self.pos + self.br
