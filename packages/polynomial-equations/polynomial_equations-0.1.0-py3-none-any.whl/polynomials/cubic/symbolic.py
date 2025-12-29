import sympy as sp


class SymbolicCubic:
    """
    Symbolic cubic equation using SymPy.
    """

    def __init__(self, a, b, c, d) -> None:
        self.x = sp.Symbol("x")
        self.expr = a * self.x**3 + b * self.x**2 + c * self.x + d

    def equation(self):
        return sp.Eq(self.expr, 0)

    def roots(self):
        return sp.solve(self.expr, self.x)

    def discriminant(self):
        return sp.discriminant(self.expr, self.x)

    def inflection_point(self):
        second = sp.diff(self.expr, self.x, 2)
        x0 = sp.solve(second, self.x)[0]
        return x0, self.expr.subs(self.x, x0)

    def latex(self) -> str:
        return sp.latex(self.equation())
