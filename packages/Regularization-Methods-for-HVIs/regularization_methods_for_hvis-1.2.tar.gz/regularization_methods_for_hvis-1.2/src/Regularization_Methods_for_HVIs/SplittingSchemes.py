import numpy as np
import scipy as sp
from .AuxProblemSolver import AuxProblemSolver

class _ForwardBackward(AuxProblemSolver):
    def __init__(self, aux_problem):
        assert aux_problem.get_number_non_smooth() == 1, f"{self.__name__} requires exactly one non-smooth operator"

        # Extract smooth and non-smooth operators
        self.smooth = aux_problem.evaluate_smooth
        self.J_non_smooth = aux_problem.evaluate_resolvents(0)

        # Determine step-size and contraction factor
        L = aux_problem.get_L()
        mu = aux_problem.get_mu()
        self.gamma = mu / L ** 2
        self.q = np.sqrt(1 - self.gamma * (2 * mu - self.gamma * L ** 2))

        super().__init__(self.q, self.iterate, self.final_operator)

    def iterate(self, x):
        forward_step = x - self.gamma * self.smooth(x)
        backward_step = self.J_non_smooth(forward_step, self.gamma)
        return backward_step

    def final_operator(self, x):
        return x


class _BackwardForward(AuxProblemSolver):
    def __init__(self, aux_problem):
        self.smooth = aux_problem.evaluate_smooth
        L = aux_problem.get_L()
        mu = aux_problem.get_mu()

        assert aux_problem.get_number_non_smooth() == 1, f"{self.__name__} requires exactly one non-smooth operator"
        self.J_non_smooth = aux_problem.evaluate_resolvents(0)

        assert L > 0, "BackwardForward requires a positive Lipschitz constant of the smooth part"
        self.gamma = mu / L ** 2

        assert mu > 0, "BackwardForward requires a positive strong monotonicity constant of the smooth part"
        assert mu < L, "BackwardForward requires strong monotonicity constant to be less than Lipschitz constant"
        self.q = np.sqrt(1 - self.gamma * (2 * mu - self.gamma * L ** 2))

        super().__init__(self.q, self.iterate, self.final_operator)

    def iterate(self, x):
        backward_step = self.J_non_smooth(x, self.gamma)
        forward_step = backward_step - self.gamma * self.smooth(backward_step)
        return forward_step

    def final_operator(self, x):
        return self.J_non_smooth(x, self.gamma)


class _DouglasRachford(AuxProblemSolver):
    """
    Douglas-Rachford splitting scheme.

    NOTE: We assume the Lipschitz monotone operator part is linear in the implementation!
    """

    def __init__(self, aux_problem):
        assert aux_problem.get_number_non_smooth() == 1, f"{self.__name__} requires exactly one non-smooth operator"

        # Extract smooth part with its resolvent and reflected resolvent
        self.smooth = aux_problem.evaluate_smooth

        def J_smooth(Y, gamma):
            IgF = lambda X: X + gamma * self.smooth(X).flatten()
            LinOpIRR = sp.sparse.linalg.LinearOperator((len(Y.flatten()), len(Y.flatten())), matvec=IgF, rmatvec=IgF)
            return sp.sparse.linalg.cg(LinOpIRR, Y)[0].reshape(*Y.shape)

        self.J_smooth = J_smooth
        self.R_smooth = lambda Y, gamma: 2 * self.J_smooth(Y, gamma) - Y

        # Extract non-smooth part with its resolvent and reflected resolvent
        self.J_non_smooth = aux_problem.evaluate_resolvents(0)
        self.R_non_smooth = lambda Y, gamma: 2 * self.J_non_smooth(Y, gamma) - Y

        # Determine step-size and contraction factor
        L = aux_problem.get_L()
        mu = aux_problem.get_mu()
        self.gamma = 1
        self.q = 1 / 2 + 1 / 2 * np.sqrt((1 - 2 * mu + L ** 2) / (1 + 2 * mu + L ** 2))

        super().__init__(self.q, self.iterate, self.final_operator)

    def iterate(self, x):
        return 1 / 2 * (x + self.R_smooth(self.R_non_smooth(x, self.gamma), self.gamma))

    def final_operator(self, x):
        return self.J_non_smooth(x, self.gamma)


class _ThreeOperatorSplitting(AuxProblemSolver):
    """
    Three-Operator splitting scheme from Davis & Yin (2017).

    NOTE:   This scheme does not strictly fall under the theoretical analysis, as the operator is merely nonexpansive
            and not contractive. It does however work in practice.
    """

    def __init__(self, aux_problem):
        assert aux_problem.get_number_non_smooth() == 2, f"{self.__name__} requires exactly two non-smooth operators"

        # Extract smooth and both non-smooth parts
        self.smooth = aux_problem.evaluate_smooth
        self.J_A = aux_problem.evaluate_resolvents(0)
        self.J_B = aux_problem.evaluate_resolvents(1)

        # Determine step-size and contraction factor
        self.gamma = 1 / aux_problem.get_L()
        self.q = 1

        super().__init__(self.q, self.iterate, self.final_operator)

    def iterate(self, x):
        J_B_x = self.J_B(x, self.gamma)
        forward_step = 2 * J_B_x - x - self.gamma * self.smooth(J_B_x)
        backward_step = x - J_B_x + self.J_A(forward_step, self.gamma)
        return backward_step

    def final_operator(self, x):
        return self.J_B(x, self.gamma)

splitting_schemes = {
    "FB": _ForwardBackward,
    "BF": _BackwardForward,
    "DR": _DouglasRachford,
    "TOS": _ThreeOperatorSplitting
}