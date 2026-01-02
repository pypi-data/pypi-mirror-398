# generated from codegen/templates/_boundingbox2d.py


__all__ = ["FBoundingBox2d", "FBoundingBox2dOverlappable", "HasFBoundingBox2d"]

from typing import Protocol

from ._egeometry import FBoundingBox2d


class FBoundingBox2dOverlappable(Protocol):
    def overlaps_f_bounding_box_2d(self, other: FBoundingBox2d) -> bool: ...


class HasFBoundingBox2d(Protocol):
    @property
    def bounding_box(self) -> FBoundingBox2d: ...
