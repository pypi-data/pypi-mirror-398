import numpy as np
import nbklu._ext as klu


def main():
    n = 5
    Ap = np.array([0, 2, 5, 9, 10, 12])
    Ai = np.array([0, 1, 0, 2, 4, 1, 2, 3, 4, 2, 1, 4])
    Ax = np.array([2.0, 3.0, 3.0, -1.0, 4.0, 4.0, -3.0, 1.0, 2.0, 2.0, 6.0, 1.0])
    b = np.array([8.0, 45.0, -3.0, 3.0, 19.0])

    common = klu.Common()
    common.defaults()
    symbolic = klu.analyze(n, Ap, Ai, common)
    numeric = klu.factor(Ap, Ai, Ax, symbolic, common)
    klu.solve(symbolic, numeric, n, 1, b, common)
    numeric.free(common)
    symbolic.free(common)
    print(b)


if __name__ == "__main__":
    main()
