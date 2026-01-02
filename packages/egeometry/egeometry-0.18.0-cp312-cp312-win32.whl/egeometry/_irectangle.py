# generated from codegen/templates/_rectangle.py

from __future__ import annotations

__all__ = ["IRectangle", "IRectangleOverlappable"]

from typing import TYPE_CHECKING
from typing import Protocol

from emath import IVector2

from ._iboundingbox2d import IBoundingBox2d

if TYPE_CHECKING:
    from ._icircle import ICircle
    from ._itriangle2d import ITriangle2d


class IRectangleOverlappable(Protocol):
    def overlaps_i_rectangle(self, other: IRectangle) -> bool: ...


class IRectangle:
    __slots__ = ["_bounding_box", "_extent", "_position", "_size"]

    def __init__(self, position: IVector2, size: IVector2):
        if size <= IVector2(0):
            raise ValueError("each size dimension must be > 0")
        self._bounding_box = IBoundingBox2d(position, size)
        self._position = position
        self._size = size
        self._extent = self._position + self._size

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, IRectangle):
            return False
        return self._position == other._position and self._size == other._size

    def __repr__(self) -> str:
        return f"<Rectangle position={self._position} size={self._size}>"

    def overlaps(self, other: IVector2 | IRectangleOverlappable) -> bool:
        if isinstance(other, IVector2):
            return self.overlaps_i_vector_2(other)
        try:
            other_overlaps = other.overlaps_i_rectangle
        except AttributeError:
            raise TypeError(other)
        return other_overlaps(self)

    def _overlaps_rect_like(self, other: IRectangle | IBoundingBox2d) -> bool:
        other_extent = other.extent
        return not (
            self.position.x >= other_extent.x
            or self._extent.x <= other.position.x
            or self.position.y >= other_extent.y
            or self._extent.y <= other.position.y
        )

    def overlaps_i_bounding_box_2d(self, other: IBoundingBox2d) -> bool:
        return self._overlaps_rect_like(other)

    def overlaps_i_circle(self, other: ICircle) -> bool:
        return other.overlaps_i_rectangle(self)

    def overlaps_i_rectangle(self, other: IRectangle) -> bool:
        return self._overlaps_rect_like(other)

    def overlaps_i_triangle_2d(self, other: ITriangle2d) -> bool:
        return other.overlaps_i_rectangle(self)

    def overlaps_i_vector_2(self, other: IVector2) -> bool:
        return (
            other.x >= self._position.x
            and other.x < self._extent.x
            and other.y >= self._position.y
            and other.y < self._extent.y
        )

    def translate(self, translation: IVector2) -> IRectangle:
        return IRectangle(self._position + translation, self._size)

    @property
    def bounding_box(self) -> IBoundingBox2d:
        return self._bounding_box

    @property
    def extent(self) -> IVector2:
        return self._extent

    @property
    def position(self) -> IVector2:
        return self._position

    @property
    def size(self) -> IVector2:
        return self._size
