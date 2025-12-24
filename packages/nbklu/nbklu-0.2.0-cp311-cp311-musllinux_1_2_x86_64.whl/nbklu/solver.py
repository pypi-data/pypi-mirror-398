from . import _ext as raw
from ._ext import Common, Symbolic, Numeric
import numpy as np
from typing import TypeVar
import warnings
from numpy.typing import NDArray

_T = TypeVar("_T", bound=np.generic)


class KLUException(Exception):
    pass


class KLUSingularException(KLUException):
    def __init__(self):
        super().__init__("Matrix is singular")


class KLUOutOfMemoryException(KLUException):
    def __init__(self):
        super().__init__("Out of memory")


class KLUInvalidOperationException(KLUException):
    def __init__(self):
        super().__init__("Invalid operation")


class KLUTooLargeException(KLUException):
    def __init__(self):
        super().__init__("Overflow error")


class KLUUnknownException(KLUException):
    pass


def as_1d(x: NDArray[_T]) -> "NDArray[_T]":
    x = np.squeeze(x)
    if x.ndim != 1:
        raise KLUException("Input must be 1-dimensional")
    return x


class KLUSolver:
    common: "Common"
    symbolic: "Symbolic | None"
    numeric: "Numeric | None"
    singular_as_error: bool

    n: int
    Ap: NDArray[np.int32] | None
    Ai: NDArray[np.int32] | None

    def __init__(self, singular_as_error=False):
        self.common = raw.Common()
        self.common.defaults()
        self.symbolic = None
        self.numeric = None
        self.singular_as_error = singular_as_error
        self.n = -1
        self.Ap = None
        self.Ai = None

    def _raise_if_error(self):
        status = self.common.status
        if status == raw.KLU_OK:
            return

        if status == raw.KLU_SINGULAR:
            if self.singular_as_error:
                raise KLUSingularException()
            else:
                warnings.warn("KLU: Matrix is singular")
        elif status == raw.KLU_OUT_OF_MEMORY:
            raise KLUOutOfMemoryException()
        elif status == raw.KLU_INVALID:
            raise KLUInvalidOperationException()
        elif status == raw.KLU_TOO_LARGE:
            raise KLUTooLargeException()

    def analyze(self, n: int, Ap: NDArray[np.int32], Ai: NDArray[np.int32]):
        """
        Order and analyze a matrix

        The AMD ordering is used if Common.ordering = 0, COLAMD is used
        if it is 1, the natural ordering is used if it is 2, and the
        user-provided Common.user ordering is used if it is 3.

        Args:
            n: Matrix dimension (n-by-n)
            Ap: Column pointers (size n+1)
            Ai: Row indices (size nz)
        """
        if self.numeric is not None:
            self.numeric.free(self.common)
            self.numeric = None

        if self.symbolic is not None:
            self.symbolic.free(self.common)
            self.symbolic = None

        self.n = n
        self.Ap = as_1d(Ap.copy())
        self.Ai = as_1d(Ai.copy())
        self.symbolic = raw.analyze(n, self.Ap, self.Ai, self.common)
        self._raise_if_error()

    def factor(
        self,
        Ax: NDArray[np.float64],
    ):
        """
        Numerical factorization of a matrix.

        The klu factor function factorizes a matrix, using a sparse left-looking method with threshold
        partial pivoting. The inputs Ap and Ai must be unchanged from the previous call to klu analyze
        that created the Symbolic object.

        Args:
            Ap: Column pointers (size n+1)
            Ai: Row indices (size nz)
            Ax: Numerical values (size nz)
        """
        if self.numeric is not None:
            self.numeric.free(self.common)
            self.numeric = None

        if self.symbolic is None or self.Ap is None or self.Ai is None:
            raise KLUException("Symbolic factorization not performed")

        self.numeric = raw.factor(self.Ap, self.Ai, Ax, self.symbolic, self.common)
        self._raise_if_error()

    def solve_(
        self,
        B: NDArray[np.float64],
    ):
        """
        Solve a linear system with multiple right-hand sides in-place.

        Args:
            B: Right-hand side matrix (nrhs, n)

        Returns:
            B: Solution matrix (nrhs, n)
        """
        if self.numeric is None or self.symbolic is None:
            raise KLUException("Numeric factorization not performed")

        B = B.squeeze()
        if B.ndim == 1:
            nrhs = 1
            n = B.shape[0]
        else:
            nrhs = B.shape[0]
            n = B.shape[1]

        if n != self.n:
            raise KLUException("Matrix dimension mismatch")

        raw.solve(self.symbolic, self.numeric, self.n, nrhs, B, self.common)
        self._raise_if_error()

        return B

    def solve(
        self,
        B: NDArray[np.float64],
    ) -> NDArray[np.float64]:
        """
        Solve a linear system with multiple right-hand sides.

        Args:
            B: Right-hand side matrix (nrhs, n)

        Returns:
            B: Solution matrix (nrhs, n)
        """
        return self.solve_(B.copy())
