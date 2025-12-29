from __future__ import annotations

from .exceptions import ShapeError
from .matrix import Matrix
from .types import Number


def det2(m: Matrix) -> Number:
    r, c = m.shape
    if (r, c) != (2, 2):
        raise ShapeError("det2 requires a 2x2 matrix.")
    a, b = m[0]
    c1, d = m[1]
    return a * d - b * c1


def trace(m: Matrix) -> Number:
    r, c = m.shape
    if r != c:
        raise ShapeError("trace requires a square matrix.")
    return sum(m[i][i] for i in range(r))
