# generated from codegen/templates/_trianglemesh3d.py

from __future__ import annotations

__all__ = ["DTriangleMesh3d", "DTriangleMesh3dRaycastResult"]

from typing import Generator
from typing import Generic
from typing import NamedTuple
from typing import TypeVar

from emath import DVector3
from emath import DVector3Array
from emath import I8Array
from emath import I16Array
from emath import I32Array
from emath import U8Array
from emath import U16Array
from emath import U32Array

_I = TypeVar("_I", U8Array, U16Array, U32Array, I8Array, I16Array, I32Array)


class DTriangleMesh3dRaycastResult(NamedTuple):
    position: DVector3
    distance: float
    triangle: tuple[DVector3, DVector3, DVector3]
    triangle_index: int


class DTriangleMesh3d(Generic[_I]):
    __slots__ = ["_vertices", "_indices"]

    def __init__(self, vertices: DVector3Array, indices: _I):
        self._vertices = vertices
        self._indices = indices

    @property
    def vertices(self) -> DVector3Array:
        return self._vertices

    @property
    def indices(self) -> _I:
        return self._indices

    @property
    def triangles(self) -> tuple[tuple[DVector3, DVector3, DVector3], ...]:
        return tuple(
            (
                self._vertices[self._indices[i]],
                self._vertices[self._indices[i + 1]],
                self._vertices[self._indices[i + 2]],
            )
            for i in range(0, len(self._indices), 3)
        )

    def raycast(
        self, eye: DVector3, direction: DVector3
    ) -> Generator[DTriangleMesh3dRaycastResult, None, None]:
        for i, triangle in enumerate(self.triangles):
            d_edge_0 = triangle[1] - triangle[0]
            d_edge_1 = triangle[0] - triangle[2]
            normal = -d_edge_0.cross(d_edge_1).normalize()

            den = normal @ direction
            if den == 0:
                continue
            d = normal @ triangle[0]
            t = (d - normal @ eye) / den
            if t < 0:
                continue

            intersection_point = eye + t * direction

            v0 = triangle[2] - triangle[0]
            v1 = triangle[1] - triangle[0]
            v2 = intersection_point - triangle[0]
            dot00 = v0 @ v0
            dot01 = v0 @ v1
            dot02 = v0 @ v2
            dot11 = v1 @ v1
            dot12 = v1 @ v2
            inv_denom = 1.0 / (dot00 * dot11 - dot01 * dot01)
            w = (dot11 * dot02 - dot01 * dot12) * inv_denom
            v = (dot00 * dot12 - dot01 * dot02) * inv_denom
            if w >= 0 and v >= 0 and w + v <= 1:
                yield DTriangleMesh3dRaycastResult(intersection_point, t, triangle, i)
