import numpy as np
from nbklu import KLUSolver


def main():
    n = 5
    Ap = np.array([0, 2, 5, 9, 10, 12])
    Ai = np.array([0, 1, 0, 2, 4, 1, 2, 3, 4, 2, 1, 4])
    Ax = np.array([2.0, 3.0, 3.0, -1.0, 4.0, 4.0, -3.0, 1.0, 2.0, 2.0, 6.0, 1.0])
    b = np.array([8.0, 45.0, -3.0, 3.0, 19.0])
    B = np.stack([b, b * 2, b * 3, b * 4], axis=0)

    solver = KLUSolver()
    solver.analyze(n, Ap, Ai)
    solver.factor(Ax)
    X = solver.solve(B)
    solver.analyze(n, Ap, Ai)
    solver.factor(Ax)
    X = solver.solve(B)
    solver.analyze(n, Ap, Ai)
    solver.factor(Ax)
    X = solver.solve(B)
    solver.analyze(n, Ap, Ai)
    solver.factor(Ax)
    X = solver.solve_(B)

    print(X)
    print(B)


if __name__ == "__main__":
    main()
