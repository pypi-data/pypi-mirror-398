# generated from codegen/templates/_rectanglefrustum.py

from __future__ import annotations

__all__ = ["FRectangleFrustum"]

from typing import TYPE_CHECKING
from typing import Protocol
from typing import overload

from emath import FMatrix4
from emath import FVector3
from emath import FVector4

from ._fplane import FPlane

if TYPE_CHECKING:
    from ._fboundingbox3d import FBoundingBox3d


class FRectangleFrustumOverlappable(Protocol):
    def overlaps_f_rectangle_frustum(self, other: FRectangleFrustum) -> bool: ...


class FRectangleFrustum:
    __slots__ = [
        "_transform",
        "_projection",
        "_near_plane",
        "_far_plane",
        "_left_plane",
        "_right_plane",
        "_bottom_plane",
        "_top_plane",
    ]

    @overload
    def __init__(
        self,
        *,
        transform: FMatrix4 = FMatrix4(1),
        orthographic: tuple[float, float, float, float, float, float],
    ): ...

    @overload
    def __init__(
        self, *, transform: FMatrix4 = FMatrix4(1), perspective: tuple[float, float, float, float]
    ): ...

    def __init__(
        self,
        *,
        transform: FMatrix4 = FMatrix4(1),
        orthographic: tuple[float, float, float, float, float, float] | None = None,
        perspective: tuple[float, float, float, float] | None = None,
    ):
        if orthographic is None and perspective is None:
            raise TypeError("either orthographic or perspective must be specified, but not both")
        elif orthographic is not None and perspective is not None:
            raise TypeError("either orthographic or perspective must be specified")
        elif orthographic is not None:
            projection = FMatrix4.orthographic(*orthographic)
        else:
            assert perspective is not None
            projection = FMatrix4.perspective(*perspective)

        self._transform = transform
        self._projection = projection

        r = [projection.get_row(i) for i in range(4)]
        tip = transform.inverse().transpose()
        self._near_plane = _create_transformed_plane(tip, r[3] + r[2])
        self._far_plane = _create_transformed_plane(tip, r[3] - r[2])
        self._left_plane = _create_transformed_plane(tip, r[3] + r[0])
        self._right_plane = _create_transformed_plane(tip, r[3] - r[0])
        self._bottom_plane = _create_transformed_plane(tip, r[3] + r[1])
        self._top_plane = _create_transformed_plane(tip, r[3] - r[1])

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FRectangleFrustum):
            return False
        return self.planes == other.planes

    def __repr__(self) -> str:
        return (
            f"<RectangleFrustum "
            f"near_plane={self._near_plane} "
            f"far_plane={self._far_plane} "
            f"left_plane={self._left_plane} "
            f"right_plane={self._right_plane} "
            f"bottom_plane={self._bottom_plane} "
            f"top_plane={self._top_plane}>"
        )

    def overlaps(self, other: FVector3 | FRectangleFrustumOverlappable) -> bool:
        if isinstance(other, FVector3):
            return self.overlaps_f_vector_3(other)
        try:
            other_overlaps = other.overlaps_f_rectangle_frustum
        except AttributeError:
            raise TypeError(other)
        return other_overlaps(self)

    def overlaps_f_bounding_box_3d(self, other: FBoundingBox3d) -> bool:
        return other.overlaps_f_rectangle_frustum(self)

    def overlaps_f_vector_3(self, other: FVector3) -> bool:
        for plane in self.planes:
            if plane.get_signed_distance_to_point(other) < 0:
                return False
        return True

    @property
    def transform(self) -> FMatrix4:
        return self._transform

    @property
    def projection(self) -> FMatrix4:
        return self._projection

    @property
    def near_plane(self) -> FPlane:
        return self._near_plane

    @property
    def far_plane(self) -> FPlane:
        return self._far_plane

    @property
    def left_plane(self) -> FPlane:
        return self._left_plane

    @property
    def right_plane(self) -> FPlane:
        return self._right_plane

    @property
    def top_plane(self) -> FPlane:
        return self._top_plane

    @property
    def bottom_plane(self) -> FPlane:
        return self._bottom_plane

    @property
    def planes(self) -> tuple[FPlane, FPlane, FPlane, FPlane, FPlane, FPlane]:
        return (
            self._near_plane,
            self._far_plane,
            self._left_plane,
            self._right_plane,
            self._top_plane,
            self._bottom_plane,
        )

    @property
    def points(
        self,
    ) -> tuple[FVector3, FVector3, FVector3, FVector3, FVector3, FVector3, FVector3, FVector3]:
        vp = (self._transform @ self._projection).inverse()
        return (
            vp @ FVector3(-1, -1, -1),
            vp @ FVector3(1, -1, -1),
            vp @ FVector3(-1, 1, -1),
            vp @ FVector3(-1, -1, 1),
            vp @ FVector3(1, 1, 1),
            vp @ FVector3(-1, 1, 1),
            vp @ FVector3(1, -1, 1),
            vp @ FVector3(1, 1, -1),
        )


def _create_transformed_plane(inversed_transposed_transform: FMatrix4, plane: FVector4) -> FPlane:
    plane = inversed_transposed_transform @ plane
    return FPlane(plane.w, plane.xyz)
