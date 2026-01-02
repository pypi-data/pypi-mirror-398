# generated from codegen/templates/_circle.py

from __future__ import annotations

__all__ = ["FCircle", "FCircleOverlappable"]

from typing import TYPE_CHECKING
from typing import Protocol
from typing import TypeAlias

from emath import FVector2

from ._fboundingbox2d import FBoundingBox2d

if TYPE_CHECKING:
    from ._frectangle import FRectangle
    from ._ftriangle2d import FTriangle2d


_FloatVector2: TypeAlias = FVector2


def _to_float_vector(v: FVector2) -> _FloatVector2:
    return v


def _to_component_type(v: float) -> float:
    return v


class FCircleOverlappable(Protocol):
    def overlaps_f_circle(self, other: FCircle) -> bool: ...


class FCircle:
    __slots__ = ["_bounding_box", "_position", "_radius"]

    def __init__(self, position: FVector2, radius: float):
        if radius <= 0:
            raise ValueError("radius must be > 0")
        self._position = position
        self._radius = radius
        self._bounding_box = FBoundingBox2d(position - radius, FVector2(radius * 2))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FCircle):
            return False
        return self._position == other._position and self._radius == other._radius

    def __repr__(self) -> str:
        return f"<Circle position={self._position} radius={self._radius}>"

    def overlaps(self, other: FVector2 | FCircleOverlappable) -> bool:
        if isinstance(other, FVector2):
            return self.overlaps_f_vector_2(other)
        try:
            other_overlaps = other.overlaps_f_circle
        except AttributeError:
            raise TypeError(other)
        return other_overlaps(self)

    def _overlaps_rect_like(self, other: FBoundingBox2d | FRectangle) -> bool:
        assert other.size != FVector2(0)
        o_center = _to_float_vector(other.position) + (_to_float_vector(other.size) * 0.5)
        f_position = _to_float_vector(self._position)
        diff = f_position - o_center
        closest_o_point = _FloatVector2(
            min(max(diff.x, other.position.x), other.extent.x),
            min(max(diff.y, other.position.y), other.extent.y),
        )
        closest_o_point_distance = f_position.distance(closest_o_point)
        return _to_component_type(closest_o_point_distance) < self._radius

    def overlaps_f_bounding_box_2d(self, other: FBoundingBox2d) -> bool:
        if other.size == FVector2(0):
            return False
        return self._overlaps_rect_like(other)

    def overlaps_f_circle(self, other: FCircle) -> bool:
        min_distance = self._radius + other._radius
        distance = _to_float_vector(self._position).distance(_to_float_vector(other._position))
        return _to_component_type(distance) < min_distance

    def overlaps_f_rectangle(self, other: FRectangle) -> bool:
        return self._overlaps_rect_like(other)

    def overlaps_f_triangle_2d(self, other: FTriangle2d) -> bool:
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

    def overlaps_f_vector_2(self, other: FVector2) -> bool:
        distance = _FloatVector2(*self._position).distance(_FloatVector2(*other))
        return _to_component_type(distance) < self._radius

    def translate(self, translation: FVector2) -> FCircle:
        return FCircle(self._position + translation, self._radius)

    @property
    def bounding_box(self) -> FBoundingBox2d:
        return self._bounding_box

    @property
    def position(self) -> FVector2:
        return self._position

    @property
    def radius(self) -> float:
        return self._radius


def _project_point_on_to_line_segment(
    line_a: _FloatVector2, line_b: _FloatVector2, point: _FloatVector2
) -> _FloatVector2:
    slope = line_b - line_a
    length_2 = sum(x**2 for x in slope)
    t = ((point - line_a) @ slope) / length_2
    t = max(min(t, 1), 0)
    return line_a + (t * slope)
