# generated from codegen/templates/_boundingbox2d.py


__all__ = ["IBoundingBox2d", "IBoundingBox2dOverlappable", "HasIBoundingBox2d"]

from typing import Protocol

from ._egeometry import IBoundingBox2d


class IBoundingBox2dOverlappable(Protocol):
    def overlaps_i_bounding_box_2d(self, other: IBoundingBox2d) -> bool: ...


class HasIBoundingBox2d(Protocol):
    @property
    def bounding_box(self) -> IBoundingBox2d: ...
