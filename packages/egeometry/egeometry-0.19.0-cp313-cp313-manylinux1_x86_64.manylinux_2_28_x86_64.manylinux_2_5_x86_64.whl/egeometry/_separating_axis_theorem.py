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

        if max_a < min_b or max_b < min_a:
            return False

    return True
