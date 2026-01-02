# generated from codegen/templates/_circle.py

from __future__ import annotations

__all__ = ["ICircle", "ICircleOverlappable"]

from typing import TYPE_CHECKING
from typing import Protocol
from typing import TypeAlias

from emath import IVector2

from ._iboundingbox2d import IBoundingBox2d

if TYPE_CHECKING:
    from ._irectangle import IRectangle
    from ._itriangle2d import ITriangle2d


from emath import DVector2

_FloatVector2: TypeAlias = DVector2


def _to_float_vector(v: IVector2) -> _FloatVector2:
    return _FloatVector2(*v)


def _to_component_type(v: float) -> int:
    return round(v)


class ICircleOverlappable(Protocol):
    def overlaps_i_circle(self, other: ICircle) -> bool: ...


class ICircle:
    __slots__ = ["_bounding_box", "_position", "_radius"]

    def __init__(self, position: IVector2, radius: int):
        if radius <= 0:
            raise ValueError("radius must be > 0")
        self._position = position
        self._radius = radius
        self._bounding_box = IBoundingBox2d(position - radius, IVector2(radius * 2))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ICircle):
            return False
        return self._position == other._position and self._radius == other._radius

    def __repr__(self) -> str:
        return f"<Circle position={self._position} radius={self._radius}>"

    def overlaps(self, other: IVector2 | ICircleOverlappable) -> bool:
        if isinstance(other, IVector2):
            return self.overlaps_i_vector_2(other)
        try:
            other_overlaps = other.overlaps_i_circle
        except AttributeError:
            raise TypeError(other)
        return other_overlaps(self)

    def _overlaps_rect_like(self, other: IBoundingBox2d | IRectangle) -> bool:
        assert other.size != IVector2(0)
        o_center = _to_float_vector(other.position) + (_to_float_vector(other.size) * 0.5)
        f_position = _to_float_vector(self._position)
        diff = f_position - o_center
        closest_o_point = _FloatVector2(
            min(max(diff.x, other.position.x), other.extent.x),
            min(max(diff.y, other.position.y), other.extent.y),
        )
        closest_o_point_distance = f_position.distance(closest_o_point)
        return _to_component_type(closest_o_point_distance) < self._radius

    def overlaps_i_bounding_box_2d(self, other: IBoundingBox2d) -> bool:
        if other.size == IVector2(0):
            return False
        return self._overlaps_rect_like(other)

    def overlaps_i_circle(self, other: ICircle) -> bool:
        min_distance = self._radius + other._radius
        distance = _to_float_vector(self._position).distance(_to_float_vector(other._position))
        return _to_component_type(distance) < min_distance

    def overlaps_i_rectangle(self, other: IRectangle) -> bool:
        return self._overlaps_rect_like(other)

    def overlaps_i_triangle_2d(self, other: ITriangle2d) -> bool:
        fv_position = _to_float_vector(self._position)
        for tri_edge_a, tri_edge_b in (
            (other.vertices[0], other.vertices[1]),
            (other.vertices[1], other.vertices[2]),
            (other.vertices[2], other.vertices[0]),
        ):
            p = _project_point_on_to_line_segment(
                _to_float_vector(tri_edge_a), _to_float_vector(tri_edge_b), fv_position
            )
            if _to_component_type(p.distance(fv_position)) < self._radius:
                return True
        return False

    def overlaps_i_vector_2(self, other: IVector2) -> bool:
        distance = _FloatVector2(*self._position).distance(_FloatVector2(*other))
        return _to_component_type(distance) < self._radius

    def translate(self, translation: IVector2) -> ICircle:
        return ICircle(self._position + translation, self._radius)

    @property
    def bounding_box(self) -> IBoundingBox2d:
        return self._bounding_box

    @property
    def position(self) -> IVector2:
        return self._position

    @property
    def radius(self) -> int:
        return self._radius


def _project_point_on_to_line_segment(
    line_a: _FloatVector2, line_b: _FloatVector2, point: _FloatVector2
) -> _FloatVector2:
    slope = line_b - line_a
    length_2 = sum(x**2 for x in slope)
    t = ((point - line_a) @ slope) / length_2
    t = max(min(t, 1), 0)
    return line_a + (t * slope)
