"""KLU sparse solver Python bindings"""

import numpy as np

# Type aliases
typedict = dict[str, np.ndarray]

# KLU status constants
KLU_OK: int
KLU_SINGULAR: int
KLU_OUT_OF_MEMORY: int
KLU_INVALID: int
KLU_TOO_LARGE: int

class Common:
    """KLU common control parameters and statistics"""
    def __init__(self) -> None: ...
    def defaults(self) -> None: ...
    
    # Parameters
    tol: float
    memgrow: float
    initmem_amd: float
    initmem: float
    maxwork: float
    btf: int
    ordering: int
    scale: int
    halt_if_singular: int
    
    # Statistics
    status: int
    nrealloc: int
    structural_rank: int
    numerical_rank: int
    singular_col: int
    noffdiag: int
    flops: float
    rcond: float
    condest: float
    rgrowth: float
    work: float
    memusage: int
    mempeak: int

class Symbolic:
    """KLU symbolic factorization object"""
    def free(self, common: Common) -> None: ...
    
    # Symbolic factorization properties
    symmetry: float
    est_flops: float
    lnz: float
    unz: float
    n: int
    nz: int
    nzoff: int
    nblocks: int
    maxblock: int
    ordering: int
    do_btf: int
    structural_rank: int

class Numeric:
    """KLU numeric factorization object"""
    def free(self, common: Common) -> None: ...
    
    # Numeric factorization properties
    n: int
    nblocks: int
    lnz: int
    unz: int
    max_lnz_block: int
    max_unz_block: int
    nzoff: int

# KLU functions
def analyze(n: int, Ap: np.ndarray[int], Ai: np.ndarray[int], common: Common) -> Symbolic: ...
def analyze_given(n: int, Ap: np.ndarray[int], Ai: np.ndarray[int], P: np.ndarray[int], Q: np.ndarray[int], common: Common) -> Symbolic: ...
def factor(Ap: np.ndarray[int], Ai: np.ndarray[int], Ax: np.ndarray[float], symbolic: Symbolic, common: Common) -> Numeric: ...
def solve(symbolic: Symbolic, numeric: Numeric, ldim: int, nrhs: int, B: np.ndarray[float], common: Common) -> int: ...