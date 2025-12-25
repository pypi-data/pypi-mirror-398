"""A very simple sparse matrix implementation in COO format.

This is only for educational/demo purposes.
"""

from typing import List, Sequence, Tuple


class SparseCOOMatrix:
    """A 2D sparse matrix in COO (coordinate) format.

    Parameters
    ----------
    rows : Sequence[int]
        Row indices of non-zero elements (0-based).
    cols : Sequence[int]
        Column indices of non-zero elements (0-based).
    data : Sequence[float]
        Values of non-zero elements.
    shape : tuple[int, int]
        Matrix shape (n_rows, n_cols).

    Notes
    -----
    This implementation is intentionally simple and not optimized.
    It is only meant to demonstrate the idea of a sparse matrix class.
    """

    def __init__(
        self,
        rows: Sequence[int],
        cols: Sequence[int],
        data: Sequence[float],
        shape: Tuple[int, int],
    ) -> None:
        if not (len(rows) == len(cols) == len(data)):
            raise ValueError("rows, cols, and data must have the same length")

        m, n = shape
        if m <= 0 or n <= 0:
            raise ValueError("shape must contain positive integers")

        self.rows = list(rows)
        self.cols = list(cols)
        self.data = list(data)
        self.shape = (int(m), int(n))

        # Basic bounds check
        for r, c in zip(self.rows, self.cols):
            if not (0 <= r < m and 0 <= c < n):
                raise ValueError(
                    f"index out of bounds: ({r}, {c}) for shape {shape}"
                )

    @classmethod
    def from_dense(cls, dense: Sequence[Sequence[float]]) -> "SparseCOOMatrix":
        """Create a SparseCOOMatrix from a dense 2D list/sequence.

        Parameters
        ----------
        dense : sequence of sequences
            Dense matrix representation, e.g. a list of lists.

        Returns
        -------
        SparseCOOMatrix
        """
        if not dense:
            raise ValueError("dense matrix must not be empty")

        m = len(dense)
        n = len(dense[0])

        rows: List[int] = []
        cols: List[int] = []
        data: List[float] = []

        for i, row in enumerate(dense):
            if len(row) != n:
                raise ValueError("all rows in the dense matrix must have the same length")
            for j, value in enumerate(row):
                if value != 0:
                    rows.append(i)
                    cols.append(j)
                    data.append(value)

        return cls(rows, cols, data, (m, n))

    def to_dense(self) -> List[List[float]]:
        """Convert the sparse matrix back to a dense 2D list."""
        m, n = self.shape
        dense = [[0 for _ in range(n)] for _ in range(m)]
        for r, c, v in zip(self.rows, self.cols, self.data):
            dense[r][c] = v
        return dense

    def matvec(self, vector: Sequence[float]) -> List[float]:
        """Compute the matrix-vector product y = A x.

        Parameters
        ----------
        vector : sequence of numbers
            Input vector x. Its length must match the number of columns.

        Returns
        -------
        list of float
            Resulting vector y.
        """
        m, n = self.shape
        if len(vector) != n:
            raise ValueError(
                f"vector length {len(vector)} does not match matrix columns {n}"
            )

        result = [0.0 for _ in range(m)]
        for r, c, v in zip(self.rows, self.cols, self.data):
            result[r] += v * vector[c]
        return result

    def __repr__(self) -> str:
        return f"SparseCOOMatrix(nnz={len(self.data)}, shape={self.shape})"