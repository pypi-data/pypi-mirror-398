class MatrixError(Exception):
    """Base library error."""


class ShapeError(MatrixError):
    """Raised on incompatible shapes."""


class ValueMatrixError(MatrixError):
    """Raised on invalid matrix values."""
