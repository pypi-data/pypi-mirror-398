class Operator:
    def __init__(self, *args, **kwargs):
        self.smooth = kwargs.get('smooth', _LipschitzMonotoneOperator())
        self.non_smooth = kwargs.get('non_smooth', [])

    def __add__(self, other):
        if isinstance(other, Operator):
            return Operator(
                smooth=self.smooth + other.smooth,
                non_smooth=self.non_smooth + other.non_smooth
            )
        else:
            raise TypeError("Can only add another Operator instance.")

    def __mul__(self, other):
        if isinstance(other, float) or isinstance(other, int):
            return Operator(
                smooth=other * self.smooth,
                non_smooth=[other * ns_op for ns_op in self.non_smooth]
            )

    def __rmul__(self, other):
        return self.__mul__(other)

    def evaluate_smooth(self, x):
        if self.smooth.evaluate:
            return self.smooth.evaluate(x)
        else:
            raise NotImplementedError("Smooth evaluation not implemented.")

    def evaluate_resolvents(self, idx):
        def evaluate(x, gamma):
            if idx < len(self.non_smooth):
                return self.non_smooth[idx].evaluate_resolvent(x, gamma)
            else:
                raise IndexError("Index out of range for non-smooth operators.")
        return evaluate

    def get_number_non_smooth(self):
        return len(self.non_smooth)

    def get_L(self):
        return self.smooth.L

    def get_mu(self):
        return self.smooth.mu

class _LipschitzMonotoneOperator:
    def __init__(self, evaluate=lambda x: 0, L=0.0, mu=0.0):
        self.evaluate = evaluate
        self.L = L
        self.mu = mu

    def __add__(self, other):
        if isinstance(other, _LipschitzMonotoneOperator):
            return _LipschitzMonotoneOperator(evaluate=lambda x: self.evaluate(x) + other.evaluate(x),
                                              L=self.L + other.L, mu=self.mu + other.mu)
        else:
            raise TypeError("Can only add another _LipschitzMonotoneOperator instance.")

    def __mul__(self, other):
        if isinstance(other, float) or isinstance(other, int):
            return _LipschitzMonotoneOperator(evaluate=lambda x: other * self.evaluate(x), L=other * self.L, mu=other * self.mu)
        else:
            raise TypeError("Can only multiply by a float.")

    def __rmul__(self, other):
        return self.__mul__(other)

class _MaximallyMonotoneOperator:
    def __init__(self, evaluate_resolvent):
        self.evaluate_resolvent = evaluate_resolvent

    def __mul__(self, other):
        if isinstance(other, float) or isinstance(other, int):
            return _MaximallyMonotoneOperator(evaluate_resolvent=lambda x, gamma: self.evaluate_resolvent(x, other * gamma))
        else:
            raise TypeError("Can only multiply by a float.")

    def __rmul__(self, other):
        return self.__mul__(other)


class LipschitzMonotoneOperator(Operator):
    def __init__(self, evaluate, L):
        super().__init__(smooth=_LipschitzMonotoneOperator(evaluate, L))

class LipschitzStronglyMonotoneOperator(Operator):
    def __init__(self, evaluate, L, mu):
        super().__init__(smooth=_LipschitzMonotoneOperator(evaluate, L, mu))

class MaximallyMonotoneOperator(Operator):
    def __init__(self, evaluate_resolvent):
        super().__init__(non_smooth=[_MaximallyMonotoneOperator(evaluate_resolvent)])

class ShiftedIdentityOperator(LipschitzStronglyMonotoneOperator):
    def __init__(self, shift):
        super().__init__(evaluate=lambda x: x - shift, L=1.0, mu=1.0)
