from __future__ import annotations

from typing import Tuple
from polynomials.base.polynomial import Polynomial
from polynomials.base.roots import quadratic_roots
from polynomials.base.validation import require_non_zero


class QuadraticEquation(Polynomial):
    """ax² + bx + c = 0"""

    def __init__(self, a: float, b: float, c: float) -> None:
        require_non_zero(a, "a")
        self.a = a
        self.b = b
        self.c = c

    def degree(self) -> int:
        return 2

    def coefficients(self) -> Tuple[float, float, float]:
        return self.a, self.b, self.c

    def value_at(self, x: float) -> float:
        return self.a * x * x + self.b * x + self.c

    def roots(self):
        return quadratic_roots(self.a, self.b, self.c)

    def __str__(self) -> str:
        return f"{self.a}x² + {self.b}x + {self.c} = 0"

    def __latex__(self) -> str:
        return f"{self.a}x^2 + {self.b}x + {self.c} = 0"
