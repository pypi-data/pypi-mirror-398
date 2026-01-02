from __future__ import annotations

__all__ = ["separating_axis_theorem"]

import warnings
from math import inf
from typing import Collection
from typing import Iterable
from typing import TypeVar

from emath import DVector2
from emath import DVector3
from emath import FVector2
from emath import FVector3

_V = TypeVar("_V", DVector2, FVector2, DVector3, FVector3)


def separating_axis_theorem(
    axes: Iterable[_V], a_vertices: Collection[_V], b_vertices: Collection[_V]
) -> bool:
    if __debug__:
        axes = list(axes)
        if len(axes) == 0:
            warnings.warn("no axes supplied, behavior undefined", RuntimeWarning)
        if len(axes) != len(set(axes)):
            warnings.warn("for best performance, axes should be unique", RuntimeWarning)
        if len(a_vertices) == 0:
            warnings.warn("no a vertices supplied, behavior undefined", RuntimeWarning)
        if len(a_vertices) != len(set(a_vertices)):
            warnings.warn("for best performance, a_vertices should be unique", RuntimeWarning)
        if len(b_vertices) != len(set(b_vertices)):
            warnings.warn("for best performance, b_vertices should be unique", RuntimeWarning)
        if len(b_vertices) == 0:
            warnings.warn("no b vertices supplied, behavior undefined", RuntimeWarning)

    for sep_axis in axes:
        min_a = min_b = inf
        max_a = max_b = -inf

        for a_vert in a_vertices:
            d = sep_axis @ a_vert
            min_a = min(min_a, d)
            max_a = max(max_a, d)

        for b_vert in b_vertices:
            d = sep_axis @ b_vert
            min_b = min(min_b, d)
            max_b = max(max_b, d)

        half_a_diff = (max_a - min_a) * 0.5
        half_a_sum = (min_a + max_a) * 0.5

        min_b -= half_a_diff
        dmin = min_b - half_a_sum
        if dmin > 0:
            return False

        max_b += half_a_diff
        dmax = max_b - half_a_sum
        if dmax < 0:
            return False

    return True
