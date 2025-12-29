from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator, List, Sequence, Tuple, Union

from .exceptions import ShapeError, ValueMatrixError
from .types import MatrixLike, Number


def _validate_and_copy(values: MatrixLike) -> List[List[Number]]:
    if not isinstance(values, Sequence) or len(values) == 0:
        raise ValueMatrixError("Matrix must be a non-empty 2D sequence.")

    rows = []
    row_len = None

    for r, row in enumerate(values):
        if not isinstance(row, Sequence) or len(row) == 0:
            raise ValueMatrixError(f"Row {r} must be a non-empty sequence.")
        if row_len is None:
            row_len = len(row)
        elif len(row) != row_len:
            raise ValueMatrixError("All rows must have the same length.")

        new_row: List[Number] = []
        for c, v in enumerate(row):
            if not isinstance(v, (int, float)):
                raise ValueMatrixError(f"Value at ({r},{c}) is not a number: {v!r}")
            new_row.append(v)
        rows.append(new_row)

    return rows


@dataclass(frozen=True, slots=True)
class Matrix:
    _data: Tuple[Tuple[Number, ...], ...]

    @staticmethod
    def from_list(values: MatrixLike) -> "Matrix":
        rows = _validate_and_copy(values)
        return Matrix(tuple(tuple(r) for r in rows))

    @staticmethod
    def zeros(r: int, c: int) -> "Matrix":
        if r <= 0 or c <= 0:
            raise ValueMatrixError("Shape must be positive.")
        return Matrix(tuple(tuple(0 for _ in range(c)) for _ in range(r)))

    @staticmethod
    def identity(n: int) -> "Matrix":
        if n <= 0:
            raise ValueMatrixError("n must be positive.")
        return Matrix(tuple(tuple(1 if i == j else 0 for j in range(n)) for i in range(n)))

    @property
    def shape(self) -> Tuple[int, int]:
        return (len(self._data), len(self._data[0]))

    def to_list(self) -> List[List[Number]]:
        return [list(r) for r in self._data]

    def __iter__(self) -> Iterator[Tuple[Number, ...]]:
        return iter(self._data)

    def __getitem__(self, idx: int) -> Tuple[Number, ...]:
        return self._data[idx]

    def T(self) -> "Matrix":
        r, c = self.shape
        return Matrix(tuple(tuple(self._data[i][j] for i in range(r)) for j in range(c)))

    def __repr__(self) -> str:
        r, c = self.shape
        preview = self._data if r <= 6 else self._data[:6]
        return f"Matrix(shape={r}x{c}, data={preview})"

    # element-wise ops
    def _assert_same_shape(self, other: "Matrix") -> None:
        if self.shape != other.shape:
            raise ShapeError(f"Shape mismatch: {self.shape} vs {other.shape}")

    def __add__(self, other: "Matrix") -> "Matrix":
        self._assert_same_shape(other)
        r, c = self.shape
        return Matrix(tuple(tuple(self._data[i][j] + other._data[i][j] for j in range(c)) for i in range(r)))

    def __sub__(self, other: "Matrix") -> "Matrix":
        self._assert_same_shape(other)
        r, c = self.shape
        return Matrix(tuple(tuple(self._data[i][j] - other._data[i][j] for j in range(c)) for i in range(r)))

    def __neg__(self) -> "Matrix":
        r, c = self.shape
        return Matrix(tuple(tuple(-self._data[i][j] for j in range(c)) for i in range(r)))

    def __mul__(self, other: Union["Matrix", Number]) -> "Matrix":
        # scalar
        if isinstance(other, (int, float)):
            r, c = self.shape
            return Matrix(tuple(tuple(self._data[i][j] * other for j in range(c)) for i in range(r)))
        # matrix multiply
        if isinstance(other, Matrix):
            return self.matmul(other)
        return NotImplemented  # type: ignore[return-value]

    def matmul(self, other: "Matrix") -> "Matrix":
        a_r, a_c = self.shape
        b_r, b_c = other.shape
        if a_c != b_r:
            raise ShapeError(f"Matmul mismatch: {self.shape} x {other.shape}")

        # classic O(n^3), optimized a bit via transpose
        bT = other.T()
        out = []
        for i in range(a_r):
            row = []
            arow = self._data[i]
            for j in range(b_c):
                brow = bT._data[j]
                s = 0
                for k in range(a_c):
                    s += arow[k] * brow[k]
                row.append(s)
            out.append(tuple(row))
        return Matrix(tuple(out))

    def hadamard(self, other: "Matrix") -> "Matrix":
        self._assert_same_shape(other)
        r, c = self.shape
        return Matrix(tuple(tuple(self._data[i][j] * other._data[i][j] for j in range(c)) for i in range(r)))

    def sum(self) -> Number:
        return sum(sum(row) for row in self._data)
