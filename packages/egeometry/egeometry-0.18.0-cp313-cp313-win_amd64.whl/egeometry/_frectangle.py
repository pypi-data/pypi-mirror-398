# generated from codegen/templates/_rectangle.py

from __future__ import annotations

__all__ = ["FRectangle", "FRectangleOverlappable"]

from typing import TYPE_CHECKING
from typing import Protocol

from emath import FVector2

from ._fboundingbox2d import FBoundingBox2d

if TYPE_CHECKING:
    from ._fcircle import FCircle
    from ._ftriangle2d import FTriangle2d


class FRectangleOverlappable(Protocol):
    def overlaps_f_rectangle(self, other: FRectangle) -> bool: ...


class FRectangle:
    __slots__ = ["_bounding_box", "_extent", "_position", "_size"]

    def __init__(self, position: FVector2, size: FVector2):
        if size <= FVector2(0):
            raise ValueError("each size dimension must be > 0")
        self._bounding_box = FBoundingBox2d(position, size)
        self._position = position
        self._size = size
        self._extent = self._position + self._size

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FRectangle):
            return False
        return self._position == other._position and self._size == other._size

    def __repr__(self) -> str:
        return f"<Rectangle position={self._position} size={self._size}>"

    def overlaps(self, other: FVector2 | FRectangleOverlappable) -> bool:
        if isinstance(other, FVector2):
            return self.overlaps_f_vector_2(other)
        try:
            other_overlaps = other.overlaps_f_rectangle
        except AttributeError:
            raise TypeError(other)
        return other_overlaps(self)

    def _overlaps_rect_like(self, other: FRectangle | FBoundingBox2d) -> bool:
        other_extent = other.extent
        return not (
            self.position.x >= other_extent.x
            or self._extent.x <= other.position.x
            or self.position.y >= other_extent.y
            or self._extent.y <= other.position.y
        )

    def overlaps_f_bounding_box_2d(self, other: FBoundingBox2d) -> bool:
        return self._overlaps_rect_like(other)

    def overlaps_f_circle(self, other: FCircle) -> bool:
        return other.overlaps_f_rectangle(self)

    def overlaps_f_rectangle(self, other: FRectangle) -> bool:
        return self._overlaps_rect_like(other)

    def overlaps_f_triangle_2d(self, other: FTriangle2d) -> bool:
        return other.overlaps_f_rectangle(self)

    def overlaps_f_vector_2(self, other: FVector2) -> bool:
        return (
            other.x >= self._position.x
            and other.x < self._extent.x
            and other.y >= self._position.y
            and other.y < self._extent.y
        )

    def translate(self, translation: FVector2) -> FRectangle:
        return FRectangle(self._position + translation, self._size)

    @property
    def bounding_box(self) -> FBoundingBox2d:
        return self._bounding_box

    @property
    def extent(self) -> FVector2:
        return self._extent

    @property
    def position(self) -> FVector2:
        return self._position

    @property
    def size(self) -> FVector2:
        return self._size
