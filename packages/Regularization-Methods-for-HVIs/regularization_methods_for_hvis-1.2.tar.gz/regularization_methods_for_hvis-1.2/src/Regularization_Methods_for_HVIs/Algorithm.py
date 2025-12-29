import numpy as np

from .SplittingSchemes import splitting_schemes
from .Operators import ShiftedIdentityOperator

class Algorithm:
    def __init__(self, problem, max_iterations, beta, epsilon):
        self.problem = problem
        self.max_iterations = max_iterations
        self.beta = beta
        self.epsilon = epsilon

        self.total_inner_iterations = 0

    def solve(self, w0, theta, alpha, progress=None, method="FB"):
        wts = [w0]

        for t in progress(range(self.max_iterations)) if progress else range(self.max_iterations):
            # Get the beta and epsilon values for the current iteration
            beta_t = self.beta.get(t)
            eps_t = self.epsilon.get(t)

            # Write out the operator of the sub-problem
            subproblem_operator = self.problem.follower + beta_t * self.problem.leader + alpha * ShiftedIdentityOperator(wts[-1])


            if method in splitting_schemes.keys():
                T = splitting_schemes[method](subproblem_operator)
            else:
                raise ValueError("Method not implemented")

            # Solve the sub-problem using the Forward-Backward operator
            wts += [T.solve_to_accuracy_with_acceleration(wts[-1], theta, eps_t)]

            self.total_inner_iterations += T.number_iterations

        return np.array(wts)