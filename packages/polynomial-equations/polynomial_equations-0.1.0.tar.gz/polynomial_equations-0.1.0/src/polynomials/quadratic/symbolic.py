import sympy as sp


class SymbolicQuadratic:
    def __init__(self, a, b, c):
        x = sp.Symbol("x")
        self.expr = a * x**2 + b * x + c
        self.x = x

    def roots(self):
        return sp.solve(self.expr, self.x)

    def latex(self) -> str:
        return sp.latex(self.expr)
