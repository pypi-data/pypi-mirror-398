import numpy as np

class Scheduler:
    """
    Scheduler class to compute decaying beta sequences of the form 1 / (n+1) ** eta.
    """

    def __init__(self, eta=1, base=1):
        """
        Initialize the Scheduler with a given exponent.

        :param eta: Exponent for the beta calculation.
        """
        self.eta = eta
        self.base = base

    def get(self, n):
        """
        Calculate the beta value for the given step t.

        :param t: The current step in the training process.

        :return: The beta value calculated as 1 / (n + 1) ** eta.
        """
        beta_t = self.base / (n + 1) ** self.eta
        return beta_t

    def get_average(self, N, iterates):
        """
        Calculate the weighted average of the given iterates using the beta sequence.

        :param N: Number of iterates in average.
        :param iterates: List of iterates to average.

        :return: The weighted average of the iterates.
        """
        assert N < len(iterates), "N must be strictly less than the number of iterates."

        if N == 0:
            return iterates[0]

        betas = np.array([self.get(n) for n in range(N)])
        average = sum(w * x for w, x in zip(betas, iterates[1:])) / sum(betas)
        return average