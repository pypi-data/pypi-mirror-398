# generated from codegen/templates/_plane.py

from __future__ import annotations

__all__ = ["FPlane", "FPlaneRaycastResult"]

from typing import Generator
from typing import NamedTuple

from emath import FVector3


class FPlaneRaycastResult(NamedTuple):
    position: FVector3
    distance: float


class FPlane:
    __slots__ = ["_distance", "_normal"]

    def __init__(self, distance: float, normal: FVector3):
        self._distance = distance
        self._normal = normal

        magnitude = normal.magnitude
        try:
            self._distance /= magnitude
            self._normal /= magnitude
        except ZeroDivisionError:
            raise ValueError("invalid normal")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FPlane):
            return False
        return self._distance == other._distance and self._normal == other._normal

    def __repr__(self) -> str:
        return f"<Plane distance={self._distance} normal={self._normal}>"

    def get_signed_distance_to_point(self, point: FVector3) -> float:
        return self._normal @ point + self._distance

    @property
    def distance(self) -> float:
        return self._distance

    @property
    def normal(self) -> FVector3:
        return self._normal

    def raycast(
        self, eye: FVector3, direction: FVector3
    ) -> Generator[FPlaneRaycastResult, None, None]:
        den = self._normal @ direction
        if den == 0:
            return
        d = self._normal @ (self._normal * -self._distance)
        t = (d - self._normal @ eye) / den
        if t < 0:
            return
        yield FPlaneRaycastResult(eye + t * direction, t)
