# generated from codegen/templates/_boundingbox3d.py

from __future__ import annotations

__all__ = ["IBoundingBox3d", "IBoundingBox3dOverlappable", "HasIBoundingBox3d"]

from typing import TYPE_CHECKING
from typing import Any
from typing import Iterable
from typing import Protocol
from typing import overload

from emath import IVector3

try:
    import pydantic_core
except ImportError:
    pass
if TYPE_CHECKING:
    import pydantic_core


class IBoundingBox3dOverlappable(Protocol):
    def overlaps_i_bounding_box_3d(self, other: IBoundingBox3d) -> bool: ...


class HasIBoundingBox3d(Protocol):
    @property
    def bounding_box(self) -> IBoundingBox3d: ...


class IBoundingBox3d:
    __slots__ = ["_extent", "_position", "_size"]

    @overload
    def __init__(self, position: IVector3, size: IVector3) -> None: ...

    @overload
    def __init__(self, *, shapes: Iterable[HasIBoundingBox3d | IVector3]) -> None: ...

    def __init__(
        self,
        position: IVector3 | None = None,
        size: IVector3 | None = None,
        *,
        shapes: Iterable[HasIBoundingBox3d | IVector3] | None = None,
    ):
        if shapes is not None:
            if position is not None:
                raise TypeError("position cannot be supplied with shapes argument")
            if size is not None:
                raise TypeError("size cannot be supplied with shapes argument")
            accum_position: IVector3 | None = None
            accum_extent: IVector3 | None = None
            for s in shapes:
                if isinstance(s, IVector3):
                    p = e = s
                else:
                    p = s.bounding_box.position
                    e = s.bounding_box.extent
                if accum_position is None:
                    accum_position = p
                else:
                    accum_position = IVector3(
                        min(p.x, accum_position.x),
                        min(p.y, accum_position.y),
                        min(p.z, accum_position.z),
                    )
                if accum_extent is None:
                    accum_extent = e
                else:
                    accum_extent = IVector3(
                        max(e.x, accum_extent.x),
                        max(e.y, accum_extent.y),
                        max(e.z, accum_extent.z),
                    )
            if accum_position is None:
                position = IVector3(0)
                size = IVector3(0)
            else:
                assert accum_extent is not None
                position = accum_position
                size = accum_extent - accum_position

        assert position is not None
        assert size is not None
        if size < IVector3(0):
            raise ValueError("each size dimension must be >= 0")
        self._position = position
        self._size = size
        self._extent = self._position + self._size

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, IBoundingBox3d):
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
    def _deserialize(cls, value: Any) -> IBoundingBox3d:
        if isinstance(value, IBoundingBox3d):
            return value
        position, size = value
        return IBoundingBox3d(IVector3.from_buffer(position), IVector3.from_buffer(size))

    @classmethod
    def _serialize(cls, value: IBoundingBox3d) -> tuple[bytes, bytes]:
        return (bytes(value._position), bytes(value._size))

    def overlaps(self, other: IVector3 | IBoundingBox3dOverlappable) -> bool:
        if isinstance(other, IVector3):
            return self.overlaps_i_vector_3(other)
        try:
            other_overlaps = other.overlaps_i_bounding_box_3d
        except AttributeError:
            raise TypeError(other)
        return other_overlaps(self)

    def overlaps_i_bounding_box_3d(self, other: IBoundingBox3d) -> bool:
        return not (
            self._position.x >= other._extent.x
            or self._extent.x <= other._position.x
            or self._position.y >= other._extent.y
            or self._extent.y <= other._position.y
            or self._position.z >= other._extent.z
            or self._extent.z <= other._position.z
        )

    def overlaps_i_vector_3(self, other: IVector3) -> bool:
        return (
            other.x >= self._position.x
            and other.x < self._extent.x
            and other.y >= self._position.y
            and other.y < self._extent.y
            and other.z >= self._position.z
            and other.z < self._extent.z
        )

    def translate(self, translation: IVector3) -> IBoundingBox3d:
        return IBoundingBox3d(self._position + translation, self._size)

    @property
    def bounding_box(self) -> IBoundingBox3d:
        return self

    @property
    def extent(self) -> IVector3:
        return self._extent

    @property
    def position(self) -> IVector3:
        return self._position

    @property
    def size(self) -> IVector3:
        return self._size

    @property
    def points(
        self,
    ) -> tuple[IVector3, IVector3, IVector3, IVector3, IVector3, IVector3, IVector3, IVector3]:
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
