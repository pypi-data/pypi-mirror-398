# generated from codegen/templates/_boundingbox3d.py

from __future__ import annotations

__all__ = [
    "DBoundingBox3d",
    "DBoundingBox3dOverlappable",
    "HasDBoundingBox3d",
    "DBoundingBox3dRaycastResult",
]

from math import copysign
from typing import TYPE_CHECKING
from typing import Any
from typing import Generator
from typing import Iterable
from typing import NamedTuple
from typing import Protocol
from typing import overload

from emath import DMatrix4
from emath import DVector3

try:
    import pydantic_core
except ImportError:
    pass
if TYPE_CHECKING:
    import pydantic_core


if TYPE_CHECKING:
    from ._drectanglefrustum import DRectangleFrustum


class DBoundingBox3dOverlappable(Protocol):
    def overlaps_d_bounding_box_3d(self, other: DBoundingBox3d) -> bool: ...


class HasDBoundingBox3d(Protocol):
    @property
    def bounding_box(self) -> DBoundingBox3d: ...


class DBoundingBox3dRaycastResult(NamedTuple):
    position: DVector3
    distance: float


class DBoundingBox3d:
    __slots__ = ["_extent", "_position", "_size"]

    @overload
    def __init__(self, position: DVector3, size: DVector3) -> None: ...

    @overload
    def __init__(self, *, shapes: Iterable[HasDBoundingBox3d | DVector3]) -> None: ...

    def __init__(
        self,
        position: DVector3 | None = None,
        size: DVector3 | None = None,
        *,
        shapes: Iterable[HasDBoundingBox3d | DVector3] | None = None,
    ):
        if shapes is not None:
            if position is not None:
                raise TypeError("position cannot be supplied with shapes argument")
            if size is not None:
                raise TypeError("size cannot be supplied with shapes argument")
            accum_position: DVector3 | None = None
            accum_extent: DVector3 | None = None
            for s in shapes:
                if isinstance(s, DVector3):
                    p = e = s
                else:
                    p = s.bounding_box.position
                    e = s.bounding_box.extent
                if accum_position is None:
                    accum_position = p
                else:
                    accum_position = DVector3(
                        min(p.x, accum_position.x),
                        min(p.y, accum_position.y),
                        min(p.z, accum_position.z),
                    )
                if accum_extent is None:
                    accum_extent = e
                else:
                    accum_extent = DVector3(
                        max(e.x, accum_extent.x),
                        max(e.y, accum_extent.y),
                        max(e.z, accum_extent.z),
                    )
            if accum_position is None:
                position = DVector3(0)
                size = DVector3(0)
            else:
                assert accum_extent is not None
                position = accum_position
                size = accum_extent - accum_position

        assert position is not None
        assert size is not None
        if size < DVector3(0):
            raise ValueError("each size dimension must be >= 0")
        self._position = position
        self._size = size
        self._extent = self._position + self._size

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DBoundingBox3d):
            return False
        return self._position == other._position and self._size == other._size

    def __repr__(self) -> str:
        return f"<BoundingBox3d position={self._position} size={self._size}>"

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: Any
    ) -> pydantic_core.CoreSchema:
        return pydantic_core.core_schema.no_info_after_validator_function(
            cls._deserialize,
            pydantic_core.core_schema.any_schema(),
            serialization=pydantic_core.core_schema.plain_serializer_function_ser_schema(
                cls._serialize, when_used="always"
            ),
        )

    @classmethod
    def _deserialize(cls, value: Any) -> DBoundingBox3d:
        if isinstance(value, DBoundingBox3d):
            return value
        position, size = value
        return DBoundingBox3d(DVector3.from_buffer(position), DVector3.from_buffer(size))

    @classmethod
    def _serialize(cls, value: DBoundingBox3d) -> tuple[bytes, bytes]:
        return (bytes(value._position), bytes(value._size))

    def overlaps(self, other: DVector3 | DBoundingBox3dOverlappable) -> bool:
        if isinstance(other, DVector3):
            return self.overlaps_d_vector_3(other)
        try:
            other_overlaps = other.overlaps_d_bounding_box_3d
        except AttributeError:
            raise TypeError(other)
        return other_overlaps(self)

    def overlaps_d_rectangle_frustum(self, other: DRectangleFrustum) -> bool:
        half_extents = self.size * 0.5
        center = self.position + half_extents
        for plane in other.planes:
            p = (
                center
                + DVector3(
                    copysign(1, plane.normal.x),
                    copysign(1, plane.normal.y),
                    copysign(1, plane.normal.z),
                )
                * half_extents
            )
            if (plane.normal @ p) + plane.distance < 0:
                return False
        return True

    def overlaps_d_bounding_box_3d(self, other: DBoundingBox3d) -> bool:
        return not (
            self._position.x >= other._extent.x
            or self._extent.x <= other._position.x
            or self._position.y >= other._extent.y
            or self._extent.y <= other._position.y
            or self._position.z >= other._extent.z
            or self._extent.z <= other._position.z
        )

    def overlaps_d_vector_3(self, other: DVector3) -> bool:
        return (
            other.x >= self._position.x
            and other.x < self._extent.x
            and other.y >= self._position.y
            and other.y < self._extent.y
            and other.z >= self._position.z
            and other.z < self._extent.z
        )

    def translate(self, translation: DVector3) -> DBoundingBox3d:
        return DBoundingBox3d(self._position + translation, self._size)

    def __rmatmul__(self, transform: DMatrix4) -> DBoundingBox3d:
        return DBoundingBox3d(shapes=(transform @ p for p in self.points))

    @property
    def bounding_box(self) -> DBoundingBox3d:
        return self

    @property
    def extent(self) -> DVector3:
        return self._extent

    @property
    def position(self) -> DVector3:
        return self._position

    @property
    def size(self) -> DVector3:
        return self._size

    @property
    def points(
        self,
    ) -> tuple[DVector3, DVector3, DVector3, DVector3, DVector3, DVector3, DVector3, DVector3]:
        return (
            self._position,
            self._position + self._size.xoo,
            self._position + self._size.oyo,
            self._position + self._size.ooz,
            self._position + self._size.xyo,
            self._position + self._size.xoz,
            self._position + self._size.oyz,
            self._extent,
        )

    def raycast(
        self, eye: DVector3, direction: DVector3
    ) -> Generator[DBoundingBox3dRaycastResult, None, None]:
        t_min = float("-inf")
        t_max = float("inf")

        if abs(direction.x) > 1e-6:
            t1 = (self._position.x - eye.x) / direction.x
            t2 = (self._extent.x - eye.x) / direction.x
            t_min = max(t_min, min(t1, t2))
            t_max = min(t_max, max(t1, t2))
        elif eye.x < self._position.x or eye.x > self._extent.x:
            return

        if abs(direction.y) > 1e-6:
            t1 = (self._position.y - eye.y) / direction.y
            t2 = (self._extent.y - eye.y) / direction.y
            t_min = max(t_min, min(t1, t2))
            t_max = min(t_max, max(t1, t2))
        elif eye.y < self._position.y or eye.y > self._extent.y:
            return

        if abs(direction.z) > 1e-6:
            t1 = (self._position.z - eye.z) / direction.z
            t2 = (self._extent.z - eye.z) / direction.z
            t_min = max(t_min, min(t1, t2))
            t_max = min(t_max, max(t1, t2))
        elif eye.z < self._position.z or eye.z > self._extent.z:
            return

        if t_min <= t_max and t_max >= 0:
            if t_min < 0:
                t_min = 0
            intersection_point = eye + t_min * direction
            yield DBoundingBox3dRaycastResult(intersection_point, t_min)
