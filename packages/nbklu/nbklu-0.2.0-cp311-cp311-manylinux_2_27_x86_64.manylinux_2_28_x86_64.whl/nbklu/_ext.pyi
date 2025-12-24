import numpy
from numpy.typing import NDArray


class Common:
    """
    KLU common control parameters and statistics.

    Contains user-definable parameters and statistics returned from KLU functions.
    This object appears in every KLU function as the last parameter. The defaults
    are chosen specifically for circuit simulation matrices.
    """

    def __init__(self) -> None: ...

    def defaults(self) -> int:
        """
        Set default parameters for KLU.

        This function sets the default parameters for KLU and clears the statistics.
        It may be used for either the real or complex cases. A value of 0 is returned
        if an error occurs, 1 otherwise. This function must be called before any
        other KLU function can be called.

        Example::

            >>> common = klu.Common()
            >>> common.defaults()
        """

    @property
    def tol(self) -> float:
        """pivot tolerance for diagonal preference"""

    @tol.setter
    def tol(self, arg: float, /) -> None: ...

    @property
    def memgrow(self) -> float:
        """realloc memory growth size for LU factors"""

    @memgrow.setter
    def memgrow(self, arg: float, /) -> None: ...

    @property
    def initmem_amd(self) -> float:
        """init. memory size with AMD: c*nnz(L) + n"""

    @initmem_amd.setter
    def initmem_amd(self, arg: float, /) -> None: ...

    @property
    def initmem(self) -> float:
        """init. memory size: c*nnz(A) + n"""

    @initmem.setter
    def initmem(self, arg: float, /) -> None: ...

    @property
    def maxwork(self) -> float:
        """maxwork for BTF, <= 0 if no limit"""

    @maxwork.setter
    def maxwork(self, arg: float, /) -> None: ...

    @property
    def btf(self) -> int:
        """use BTF pre-ordering, or not"""

    @btf.setter
    def btf(self, arg: int, /) -> None: ...

    @property
    def ordering(self) -> int:
        """0: AMD, 1: COLAMD, 2: user P and Q,"""

    @ordering.setter
    def ordering(self, arg: int, /) -> None: ...

    @property
    def scale(self) -> int:
        """
        row scaling: -1: none (and no error check),
                                     * 0: none, 1: sum, 2: max
        """

    @scale.setter
    def scale(self, arg: int, /) -> None: ...

    @property
    def halt_if_singular(self) -> int:
        """
        how to handle a singular matrix.
        0: keep going.  Return a Numeric object with a zero U(k,k). A
           divide-by-zero may occur when computing L(:,k). The Numeric object
           can be passed to klu_solve (a divide-by-zero will occur). It can
           also be safely passed to klu_refactor.
        1: stop quickly. klu_factor will free the partially-constructed
           Numeric object. klu_refactor will not free it, but will leave the
           numerical values only partially defined. This is the default.
        """

    @halt_if_singular.setter
    def halt_if_singular(self, arg: int, /) -> None: ...

    @property
    def status(self) -> int:
        """KLU_OK if OK, < 0 if error"""

    @status.setter
    def status(self, arg: int, /) -> None: ...

    @property
    def nrealloc(self) -> int:
        """# of reallocations of L and U"""

    @nrealloc.setter
    def nrealloc(self, arg: int, /) -> None: ...

    @property
    def structural_rank(self) -> int:
        """
        0 to n-1 if the matrix is structurally rank deficient (as determined
        by maxtrans). -1 if not computed. n if the matrix has full structural
        rank. This is computed by klu_analyze if a BTF preordering is requested.
        """

    @structural_rank.setter
    def structural_rank(self, arg: int, /) -> None: ...

    @property
    def numerical_rank(self) -> int:
        """
        First k for which a zero U(k,k) was found,
        if the matrix was singular (in the range 0 to n-1). n if the matrix
        has full rank. This is not a true rank-estimation. It just reports
        where the first zero pivot was found. -1 if not computed.
        Computed by klu_factor and klu_refactor.
        """

    @numerical_rank.setter
    def numerical_rank(self, arg: int, /) -> None: ...

    @property
    def singular_col(self) -> int:
        """
        n if the matrix is not singular. If in the
        range 0 to n-1, this is the column index of the original matrix A that
        corresponds to the column of U that contains a zero diagonal entry.
        -1 if not computed. Computed by klu_factor and klu_refactor.
        """

    @singular_col.setter
    def singular_col(self, arg: int, /) -> None: ...

    @property
    def noffdiag(self) -> int:
        """# of off-diagonal pivots, -1 if not computed"""

    @noffdiag.setter
    def noffdiag(self, arg: int, /) -> None: ...

    @property
    def flops(self) -> float:
        """actual factorization flop count, from klu_flops"""

    @flops.setter
    def flops(self, arg: float, /) -> None: ...

    @property
    def rcond(self) -> float:
        """crude reciprocal condition est., from klu_rcond"""

    @rcond.setter
    def rcond(self, arg: float, /) -> None: ...

    @property
    def condest(self) -> float:
        """accurate condition est., from klu_condest"""

    @condest.setter
    def condest(self, arg: float, /) -> None: ...

    @property
    def rgrowth(self) -> float:
        """reciprocal pivot rgrowth, from klu_rgrowth"""

    @rgrowth.setter
    def rgrowth(self, arg: float, /) -> None: ...

    @property
    def work(self) -> float:
        """actual work done in BTF, in klu_analyze"""

    @work.setter
    def work(self, arg: float, /) -> None: ...

    @property
    def memusage(self) -> int:
        """current memory usage, in bytes"""

    @memusage.setter
    def memusage(self, arg: int, /) -> None: ...

    @property
    def mempeak(self) -> int:
        """peak memory usage, in bytes"""

    @mempeak.setter
    def mempeak(self, arg: int, /) -> None: ...

class Symbolic:
    """
    KLU symbolic factorization object.

    Contains a pre-ordering which combines the block triangular form (BTF) with
    a fill-reducing ordering, and an estimate of the number of nonzeros in the
    factors of each block. Its size is proportional to n (the matrix dimension).
    It can be reused multiple times for the factorization of matrices with
    identical nonzero patterns.

    A (P,Q) is in upper block triangular form. The kth block goes from
    row/col index R [k] to R [k+1]-1. The estimated number of nonzeros
    in the L factor of the kth block is Lnz [k].
    """

    def free(self, arg: Common, /) -> None: ...

    @property
    def symmetry(self) -> float:
        """
        symmetry of largest block

        only computed if the AMD ordering is used
        """

    @symmetry.setter
    def symmetry(self, arg: float, /) -> None: ...

    @property
    def est_flops(self) -> float:
        """
        estimated factorization flop count

        only computed if the AMD ordering is used
        """

    @est_flops.setter
    def est_flops(self, arg: float, /) -> None: ...

    @property
    def lnz(self) -> float:
        """
        estimated nz in L, including diagonals

        only computed if the AMD ordering is used
        """

    @lnz.setter
    def lnz(self, arg: float, /) -> None: ...

    @property
    def unz(self) -> float:
        """
        estimated nz in U, including diagonals

        only computed if the AMD ordering is used
        """

    @unz.setter
    def unz(self, arg: float, /) -> None: ...

    @property
    def n(self) -> int:
        """input matrix A is n-by-n"""

    @n.setter
    def n(self, arg: int, /) -> None: ...

    @property
    def nz(self) -> int:
        """# entries in input matrix"""

    @nz.setter
    def nz(self, arg: int, /) -> None: ...

    @property
    def nzoff(self) -> int:
        """nz in off-diagonal blocks"""

    @nzoff.setter
    def nzoff(self, arg: int, /) -> None: ...

    @property
    def nblocks(self) -> int:
        """number of blocks"""

    @nblocks.setter
    def nblocks(self, arg: int, /) -> None: ...

    @property
    def maxblock(self) -> int:
        """size of largest block"""

    @maxblock.setter
    def maxblock(self, arg: int, /) -> None: ...

    @property
    def ordering(self) -> int:
        """ordering used (0:AMD, 1:COLAMD, 2:given, ... )"""

    @ordering.setter
    def ordering(self, arg: int, /) -> None: ...

    @property
    def do_btf(self) -> int:
        """whether or not BTF preordering was requested"""

    @do_btf.setter
    def do_btf(self, arg: int, /) -> None: ...

    @property
    def structural_rank(self) -> int:
        """
        0 to n-1 if the matrix is structurally rank
        deficient. -1 if not computed. n if the matrix has
        full structural rank 

        only computed if BTF preordering requested
        """

    @structural_rank.setter
    def structural_rank(self, arg: int, /) -> None: ...

class Numeric:
    def free(self, arg: Common, /) -> None: ...

    @property
    def n(self) -> int:
        """A is n-by-n"""

    @n.setter
    def n(self, arg: int, /) -> None: ...

    @property
    def nblocks(self) -> int:
        """number of diagonal blocks"""

    @nblocks.setter
    def nblocks(self, arg: int, /) -> None: ...

    @property
    def lnz(self) -> int:
        """actual nz in L, including diagonal"""

    @lnz.setter
    def lnz(self, arg: int, /) -> None: ...

    @property
    def unz(self) -> int:
        """actual nz in U, including diagonal"""

    @unz.setter
    def unz(self, arg: int, /) -> None: ...

    @property
    def max_lnz_block(self) -> int:
        """max actual nz in L in any one block, incl. diag"""

    @max_lnz_block.setter
    def max_lnz_block(self, arg: int, /) -> None: ...

    @property
    def max_unz_block(self) -> int:
        """max actual nz in U in any one block, incl. diag"""

    @max_unz_block.setter
    def max_unz_block(self, arg: int, /) -> None: ...

    @property
    def nzoff(self) -> int:
        """number of off-diagonal entries"""

    @nzoff.setter
    def nzoff(self, arg: int, /) -> None: ...

KLU_OK: int = 0

KLU_SINGULAR: int = 1

KLU_OUT_OF_MEMORY: int = -2

KLU_INVALID: int = -3

KLU_TOO_LARGE: int = -4

def analyze(n: int, Ap: NDArray[numpy.int32], Ai: NDArray[numpy.int32], common: Common) -> Symbolic:
    """
    Order and analyze a matrix

    The error status for this function, and all others, is returned in
    Common.status. These functions may be used for both real and complex
    cases. The AMD ordering is used if Common.ordering = 0, COLAMD is used
    if it is 1, the natural ordering is used if it is 2, and the
    user-provided Common.user ordering is used if it is 3.

    Args:
       n: Matrix dimension (n-by-n)
       Ap: Column pointers (size n+1)
       Ai: Row indices (size nz)
       common: KLU common object with control parameters

    Returns:
       Symbolic factorization object, or None if an error occurred
    """

def analyze_given(n: int, Ap: NDArray[numpy.int32], Ai: NDArray[numpy.int32], Puser: NDArray[numpy.int32] | None, Quser: NDArray[numpy.int32] | None, common: Common) -> Symbolic:
    """
    Order and analyze a matrix with a given ordering.

    In this routine, the fill-reducing ordering is provided by the user
    (Common.ordering is ignored). Instead, the row permutation P and
    column permutation Q are used. These are integer arrays of size n.
    If NULL, a natural ordering is used (so to provide just a column
    ordering, pass Q as non-NULL and P as NULL). A NULL pointer is returned
    if an error occurs. These functions may be used for both real and complex cases.

    Args:
       n: Matrix dimension (n-by-n)
       Ap: Column pointers (size n+1)
       Ai: Row indices (size nz)
       Puser: Permutation vector (size n, may be None)
       Quser: Permutation vector (size n, may be None)
       common: KLU common object with control parameters

    Returns:
       Symbolic factorization object, or None if an error occurred
    """

def factor(Ap: NDArray[numpy.int32], Ai: NDArray[numpy.int32], Ax: NDArray[numpy.float64], symbolic: Symbolic, common: Common) -> Numeric:
    """
    Numerical factorization of a matrix.

    The klu factor function factorizes a matrix, using a sparse left-looking method with threshold
    partial pivoting. The inputs Ap and Ai must be unchanged from the previous call to klu analyze
    that created the Symbolic object.

    Args:
       Ap: Column pointers (size n+1)
       Ai: Row indices (size nz)
       Ax: Numerical values (size nz)
       symbolic: Symbolic factorization object
       common: KLU common object with control parameters

    Returns:
       Numeric factorization object, or None if an error occurred
    """

def solve(symbolic: Symbolic, numeric: Numeric, ldim: int, nrhs: int, B: NDArray[numpy.float64], common: Common) -> int:
    """
    Solve a linear system.

    Solves the linear system Ax = b, using the Symbolic and Numeric objects.
    The right-hand side B is overwritten with the solution on output.
    The array B is stored in column major order, with a leading dimension
    of ldim, and nrhs columns. Thus, the real entry bij is stored in B
    [i+j*ldim], where ldim >= n must hold. A complex entry bij is stored in B [2*(i+j*ldim)] and
    B [2*(i+j*ldim)+1] (for the real and imaginary parts, respectively).

    Args:
       symbolic: Symbolic factorization object
       numeric: Numeric factorization object
       d: leading dimension of B
       nrhs: Number of right-hand sides (nrhs columns of B)
       B: Right-hand side matrix (size n-by-nrhs)
       common: KLU common object with control parameters

    Returns:
       1 if successful, 0 if an error occurs
    """

def tsolve(symbolic: Symbolic, numeric: Numeric, ldim: int, nrhs: int, B: NDArray[numpy.float64], common: Common) -> int:
    """
    Solve a transposed linear system.

    Solves the linear system $A^T x = b$ or $A^Hx = b$.
    The conj solve input is 0 for $A^T x = b$, or nonzero
    for $A^Hx = b$. Otherwise, the function is identical to klu solve.

    Args:
       symbolic: Symbolic factorization object
       numeric: Numeric factorization object
       ldim: leading dimension of B
       nrhs: Number of right-hand sides (nrhs columns of B)
       B: Right-hand side matrix (size n-by-nrhs)
       common: KLU common object with control parameters

    Returns:
       1 if successful, 0 if an error occurs
    """

def refactor(Ap: NDArray[numpy.int32], Ai: NDArray[numpy.int32], Ax: NDArray[numpy.float64], symbolic: Symbolic, numeric: Numeric, common: Common) -> int:
    """
    Numerical refactorization of a matrix.
    The klu refactor function takes as input the Numeric object created by klu factor (or as modified
    by a previous call to klu refactor). It factorizes a new matrix with the same nonzero pattern
    as that given to the call to klu factor which created it. The same pivot order is used. Since
    this can lead to numeric instability, the use of klu rcond, klu rgrowth, or klu condest is rec-
    ommended to check the accuracy of the resulting factorization. The inputs Ap and Ai must be
    unmodified since the call to klu factor that first created the Numeric object. This is function is
    much faster than klu factor, and requires no dynamic memory allocation.

    Args:
       Ap: Column pointers (size n+1)
       Ai: Row indices (size nz)
       Ax: Numerical values (size nz)
       numeric: Numeric factorization object
       common: KLU common object with control parameters

    Returns:
       1 if successful, 0 if an error occurs
    """

def sort(symbolic: Symbolic, numeric: Numeric, common: Common) -> int:
    """
    Sort the columns of L and U.

    The klu factor function creates a Numeric object with factors L and U stored in a compressed-
    column form (not the same data structure as A, but similar). The columns typically contain lists
    of row indices in unsorted order. This function sorts these indices, for two purposes: (1) to return
    L and U to MATLAB, which expects its sparse matrices to have sorted columns, and (2) to slightly
    improve the performance of subsequent calls to klu solve and klu tsolve.

    Args:
       symbolic: Symbolic factorization object
       numeric: Numeric factorization object
       common: KLU common object with control parameters

    Returns:
       1 if successful, 0 if an error occurs
    """

def flops(symbolic: Symbolic, numeric: Numeric, common: Common) -> int:
    """
    Determine the flop count.

    This function determines the number of floating-point operations performed when the matrix was
    factorized by klu factor or klu refactor. The result is returned in Common.flops.

    Args:
       symbolic: Symbolic factorization object
       numeric: Numeric factorization object
       common: KLU common object with control parameters

    Returns:
       1 if successful, 0 if an error occurs
    """

def rgrowth(Ap: NDArray[numpy.int32], Ai: NDArray[numpy.int32], Ax: NDArray[numpy.float64], symbolic: Symbolic, numeric: Numeric, common: Common) -> int:
    r"""
    Determine the pivot growth.

    Computes the reciprocal pivot growth, $ rgrowth = \min_j (( \max_i |c_{ij}| ) / ( \max_i |u_{ij}| ))$, where $c_{ij}$ is a scaled entry in a diagonal block of the block triangular
    form. 

    In MATLAB notation: rgrowth = min (max (abs (R\A(p,q) - F)) ./ max (abs (U)))

    where the factorization is L*U + F = R \ A(p,q). If rgrowth is
    very small, an inaccurate factorization may have been performed.
    The inputs Ap, Ai, and Ax (Az in the complex case) must be
    unchanged since the last call to klu_factor or klu_refactor. The
    result is returned in Common.rgrowth.

    Args: 
       Ap: Column pointers (size n+1)
       Ai: Row indices (size nz)
       Ax: Numerical values (size nz)
       symbolic: Symbolic factorization object
       numeric: Numeric factorization object
       common: KLU common object with control parameters

    Returns:
       1 if successful, 0 if an error occurs
    """

def condest(Ap: NDArray[numpy.int32], Ax: NDArray[numpy.float64], symbolic: Symbolic, numeric: Numeric, common: Common) -> int:
    """
    Accurate condition number estimation.

    This function is essentially the same as the MATLAB condest function. It computes an estimate
    of the 1-norm condition number, using Hager's method and the generalization by Higham and
    Tisseur. The inputs Ap, and Ax (Az in the complex case) must be unchanged since the last call
    to klu factor or klu refactor. The result is returned in Common.condest.

    Args: 
       Ap: Column pointers (size n+1)
       Ax: Numerical values (size nz)
       symbolic: Symbolic factorization object
       numeric: Numeric factorization object
       common: KLU common object with control parameters

    Returns:
       1 if successful, 0 if an error occurs
    """

def rcond(symbolic: Symbolic, numeric: Numeric, common: Common) -> int:
    """
    Cheap reciprocal condition number estimation.

    This function returns the smallest diagonal entry of U divided by the largest, which is a very
    crude estimate of the reciprocal of the condition number of the matrix A. It is very cheap to
    compute, however. In MATLAB notation, rcond = min(abs(diag(U))) / max(abs(diag(U))).
    If the matrix is singular, rcond will be zero. The result is returned in Common.rcond.

    Args: 
       symbolic: Symbolic factorization object
       numeric: Numeric factorization object
       common: KLU common object with control parameters

    Returns:
       1 if successful, 0 if an error occurs
    """

def scale(scale: int, n: int, Ap: NDArray[numpy.int32], Ai: NDArray[numpy.int32], Ax: NDArray[numpy.float64], Rs: NDArray[numpy.float64], W: NDArray[numpy.int32], symbolic: Symbolic, numeric: Numeric, common: Common) -> int:
    """
    Scale and check a sparse matrix.

    This function computes the row scaling factors of a matrix and checks to see if it is a valid sparse
    matrix. It can perform two kinds of scaling, computing either the largest magnitude in each row,
    or the sum of the magnitudes of the entries each row. KLU calls this function itself, depending
    upon the Common.scale parameter, where scale < 0 means no scaling, scale=1 means the sum,
    and scale=2 means the maximum. That is, in MATLAB notation, Rs = sum(abs(A')) or Rs =
    max(abs(A')). KLU then divides each row of A by its corresponding scale factor. The function
    returns 0 if the matrix is invalid, or 1 otherwise. A valid sparse matrix must meet the following
    conditions:
      1. n > 0. Note that KLU does not handle empty (0-by-0) matrices.
      2. Ap, Ai, and Ax (Az for the complex case) must not be NULL.
      3. Ap[0]=0, and Ap [j] <= Ap [j+1] for all j in the range 0 to n-1.
      4. The row indices in each column, Ai [Ap [j] ...  Ap [j+1]-1], must be in the range 0
         to n-1, and no duplicates can appear. If the workspace W is NULL on input, the check for
         duplicate entries is skipped.

    Args:
       scale: 0: none, 1: sum, 2: max
       n: Matrix dimension
       Ap: Column pointers (size n+1)
       Ai: Row indices (size nz)
       Ax: Numerical values (size nz)
       Rs: Row scaling factors (size n, output, can be None if scale <= 0)
       W: Workspace (size n, can be None)
       common: KLU common object with control parameters

    Returns:
       1 if successful, 0 if an error occurs
    """

def extract(numeric: Numeric, symbolic: Symbolic, Lp: NDArray[numpy.int32], Li: NDArray[numpy.int32], Lx: NDArray[numpy.float64], Up: NDArray[numpy.int32], Ui: NDArray[numpy.int32], Ux: NDArray[numpy.float64], Fp: NDArray[numpy.int32], Fi: NDArray[numpy.int32], Fx: NDArray[numpy.float64], P: NDArray[numpy.int32], Q: NDArray[numpy.int32], Rs: NDArray[numpy.float64], R: NDArray[numpy.int32], common: Common) -> None:
    """
    Extract the LU factorization.

    This function extracts the LU factorization into a set of data structures suitable for passing back to
    MATLAB, with matrices in conventional compressed-column form. The klu sort function should
    be called first if the row indices should be returned sorted. The factorization is returned in caller-
    provided arrays; if any of them are NULL, that part of the factorization is not extracted (this is
    not an error).

    The sizes of Li, Lx, and Lz are Numeric->lnz, Ui, Ux, and Uz are of size Numeric->unz, and Fi,
    Fx, and Fz are of size Numeric->nzoff. Note that in the complex versions, the real and imaginary
    parts are returned in separate arrays, to be compatible with how MATLAB stores complex matrices.

    This function is not required to solve a linear system with KLU. KLU does not itself make
    use of the extracted LU factorization returned by this function. It is only provided to simplify
    the MATLAB interface to KLU, and it may be of use to the end user who wishes to examine the
    contents of the LU factors.

    Args:
       symbolic: Symbolic factorization object
       numeric: Numeric factorization object
       common: KLU common object with control parameters
       Lp: Column pointers for L (size n+1, output)
       Li: Row indices for L (size Numeric->lnz, output)
       Lx: Numerical values for L (size Numeric->lnz, output)
       Up: Column pointers for U (size n+1, output)
       Ui: Row indices for U (size Numeric->unz, output)
       Ux: Numerical values for U (size Numeric->unz, output)
       Fp: Column pointers for F (size n+1, output)
       Fi: Row indices for F (size Numeric->nzoff, output)
       Fx: Numerical values for F (size Numeric->nzoff, output)

    Returns:
       1 if successful, 0 if an error occurs
    """
