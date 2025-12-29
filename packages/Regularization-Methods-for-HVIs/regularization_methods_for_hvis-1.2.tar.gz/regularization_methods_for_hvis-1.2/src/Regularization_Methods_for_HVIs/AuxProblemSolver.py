import scipy as sp
import numpy as np


class AuxProblemSolver:
    # Maximum number of iterations for sub-problem
    MAX_SUB_ITERATIONS = 100

    def __init__(self, q, iterate, final_operator):
        self.q = q
        self.iterate = iterate
        self.final_operator = final_operator

        self.number_iterations = 0

    def _determine_tau(self, theta):
        Q = 1 - theta + theta * self.q ** 2
        tau = sp.optimize.fsolve(
            lambda x: Q * x * (1 + x) + theta * x * (1 - x) - Q * theta * (1 - x) - 1e-4, 0.5)
        return tau[0] if isinstance(tau, np.ndarray) else tau

    def solve_to_accuracy_with_acceleration(self, initial, theta, eps):
        tau = self._determine_tau(theta)

        # Perform sub-iterations to solve auxiliary problem
        v0 = initial
        v1 = initial
        z0 = np.zeros_like(initial)

        for _ in range(self.MAX_SUB_ITERATIONS):
            self.number_iterations += 1
            if np.linalg.norm(v1 - z0) <= eps: break
            z0 = v1 + tau * (v1 - v0)
            v0 = v1
            v1 = (1 - theta) * z0 + theta * self.iterate(z0)
        else:
            print(f"WARNING: Maximum number of sub-iterations ({self.MAX_SUB_ITERATIONS}) reached")

        return self.final_operator(z0)