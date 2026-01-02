# generated from codegen/templates/_triangle2d.py

from __future__ import annotations

__all__ = ["FTriangle2d", "FTriangle2dOverlappable"]

from typing import TYPE_CHECKING
from typing import Protocol
from typing import TypeAlias

from emath import FVector2

from ._fboundingbox2d import FBoundingBox2d
from ._separating_axis_theorem import separating_axis_theorem

if TYPE_CHECKING:
    from ._fcircle import FCircle
    from ._frectangle import FRectangle


_FloatVector2: TypeAlias = FVector2


def _to_float_vector(v: FVector2) -> _FloatVector2:
    return v


def _to_float_vectors(vs: tuple[FVector2, ...]) -> tuple[_FloatVector2, ...]:
    return vs


class FTriangle2dOverlappable(Protocol):
    def overlaps_f_triangle_2d(self, other: FTriangle2d) -> bool: ...


class FTriangle2d:
    __slots__ = ["_bounding_box", "_vertices"]

    _vertices: tuple[FVector2, FVector2, FVector2]

    def __init__(self, point_0: FVector2, point_1: FVector2, point_2: FVector2, /):
        self._vertices = (point_0, point_1, point_2)

        if len(set(self._vertices)) != 3:
            raise ValueError("vertices do not form a triangle")
        # fmt: off
        double_area = (
            point_0.x * (point_1.y - point_2.y) +
            point_1.x * (point_2.y - point_0.y) +
            point_2.x * (point_0.y - point_1.y)
        )
        # fmt: on
        if double_area == 0:
            raise ValueError("vertices do not form a triangle")

        i = sorted(enumerate(self._vertices))[0][0]
        self._vertices = self._vertices[i:] + self._vertices[:i]  # type: ignore

        self._bounding_box = FBoundingBox2d(shapes=self._vertices)

    def __hash__(self) -> int:
        return hash(self._vertices)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FTriangle2d):
            return False
        return self._vertices == other._vertices

    def __repr__(self) -> str:
        return f"<Triangle2d vertices={self._vertices}>"

    @property
    def _axes(self) -> tuple[_FloatVector2, _FloatVector2, _FloatVector2]:
        p = self._vertices
        return (
            _FloatVector2(p[1].y - p[0].y, p[0].x - p[1].x).normalize(),
            _FloatVector2(p[2].y - p[1].y, p[1].x - p[2].x).normalize(),
            _FloatVector2(p[0].y - p[2].y, p[2].x - p[0].x).normalize(),
        )

    def overlaps(self, other: FVector2 | FTriangle2dOverlappable) -> bool:
        if isinstance(other, FVector2):
            return self.overlaps_f_vector_2(other)
        try:
            other_overlaps = other.overlaps_f_triangle_2d
        except AttributeError:
            raise TypeError(other)
        return other_overlaps(self)

    def overlaps_f_vector_2(self, other: FVector2) -> bool:
        # solve for the point's barycentric coordinates
        p0 = self._vertices[0]
        v0 = _to_float_vector(self._vertices[2] - p0)
        v1 = _to_float_vector(self._vertices[1] - p0)
        v2 = _to_float_vector(other - p0)
        dot00 = v0 @ v0
        dot01 = v0 @ v1
        dot02 = v0 @ v2
        dot11 = v1 @ v1
        dot12 = v1 @ v2
        inv_denom = 1.0 / (dot00 * dot11 - dot01 * dot01)
        u = (dot11 * dot02 - dot01 * dot12) * inv_denom
        if u < 0:
            return False
        v = (dot00 * dot12 - dot01 * dot02) * inv_denom
        if v >= 0 and u + v <= 1:
            return True
        return False

    def _overlaps_rect_like(self, other: FBoundingBox2d | FRectangle) -> bool:
        return separating_axis_theorem(
            {*self._axes, _FloatVector2(1, 0), _FloatVector2(0, 1)},
            _to_float_vectors(self._vertices),
            _to_float_vectors(
                tuple(
                    (
                        other.position,
                        other.position + other.size.xo,
                        other.extent,
                        other.position + other.size.oy,
                    )
                )
            ),
        )

    def overlaps_f_bounding_box_2d(self, other: FBoundingBox2d) -> bool:
        return self._overlaps_rect_like(other)

    def overlaps_f_circle(self, other: FCircle) -> bool:
        return other.overlaps_f_triangle_2d(self)

    def overlaps_f_rectangle(self, other: FRectangle) -> bool:
        return self._overlaps_rect_like(other)

    def overlaps_f_triangle_2d(self, other: FTriangle2d) -> bool:
        return separating_axis_theorem(
            {*self._axes, *other._axes},
            _to_float_vectors(self._vertices),
            _to_float_vectors(other._vertices),
        )

    def translate(self, translation: FVector2) -> FTriangle2d:
        return FTriangle2d(*(v + translation for v in self._vertices))

    @property
    def bounding_box(self) -> FBoundingBox2d:
        return self._bounding_box

    @property
    def vertices(self) -> tuple[FVector2, FVector2, FVector2]:
        return self._vertices
