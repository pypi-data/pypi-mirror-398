# generated from codegen/templates/_boundingbox2d.py


__all__ = ["DBoundingBox2d", "DBoundingBox2dOverlappable", "HasDBoundingBox2d"]

from typing import Protocol

from ._egeometry import DBoundingBox2d


class DBoundingBox2dOverlappable(Protocol):
    def overlaps_d_bounding_box_2d(self, other: DBoundingBox2d) -> bool: ...


class HasDBoundingBox2d(Protocol):
    @property
    def bounding_box(self) -> DBoundingBox2d: ...
