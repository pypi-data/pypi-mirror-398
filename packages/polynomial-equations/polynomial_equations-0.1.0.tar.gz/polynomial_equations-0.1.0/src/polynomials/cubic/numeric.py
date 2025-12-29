from __future__ import annotations

import cmath
from typing import Tuple, Literal, List

from polynomials.base.polynomial import Polynomial
from polynomials.base.validation import require_non_zero


class CubicEquation(Polynomial):
    """
    Represents a cubic equation:
        ax³ + bx² + cx + d = 0
    """

    def __init__(self, a: float, b: float, c: float, d: float) -> None:
        require_non_zero(a, "a")
        self.a = float(a)
        self.b = float(b)
        self.c = float(c)
        self.d = float(d)

    # ------------------------------------------------------------------
    # Polynomial API
    # ------------------------------------------------------------------
    def degree(self) -> int:
        return 3

    def coefficients(self) -> Tuple[float, float, float, float]:
        return self.a, self.b, self.c, self.d

    def value_at(self, x: float) -> float:
        return (
            self.a * x**3
            + self.b * x**2
            + self.c * x
            + self.d
        )

    # ------------------------------------------------------------------
    # Algebra
    # ------------------------------------------------------------------
    def discriminant(self) -> float:
        """
        Return the discriminant of the cubic equation.
        """
        a, b, c, d = self.a, self.b, self.c, self.d
        return (
            18 * a * b * c * d
            - 4 * b**3 * d
            + b**2 * c**2
            - 4 * a * c**3
            - 27 * a**2 * d**2
        )

    def root_nature(self) -> Literal[
        "three real",
        "one real two complex",
        "multiple real",
    ]:
        disc = self.discriminant()
        if disc > 0:
            return "three real"
        if disc == 0:
            return "multiple real"
        return "one real two complex"

    # ------------------------------------------------------------------
    # Roots (Cardano)
    # ------------------------------------------------------------------
    def roots(self) -> Tuple[complex, complex, complex]:
        """
        Compute roots using Cardano's method.
        """
        a, b, c, d = self.a, self.b, self.c, self.d

        # Normalize
        p = (3 * a * c - b**2) / (3 * a**2)
        q = (2 * b**3 - 9 * a * b * c + 27 * a**2 * d) / (27 * a**3)

        delta = (q / 2)**2 + (p / 3)**3
        sqrt_delta = cmath.sqrt(delta)

        u = (-q / 2 + sqrt_delta) ** (1 / 3)
        v = (-q / 2 - sqrt_delta) ** (1 / 3)

        omega = complex(-0.5, cmath.sqrt(3) / 2)

        t1 = u + v
        t2 = u * omega + v * omega.conjugate()
        t3 = u * omega.conjugate() + v * omega

        shift = -b / (3 * a)

        return (
            t1 + shift,
            t2 + shift,
            t3 + shift,
        )

    # ------------------------------------------------------------------
    # Geometry & Calculus
    # ------------------------------------------------------------------
    def derivative(self) -> Tuple[float, float, float]:
        """
        First derivative:
            f'(x) = 3ax² + 2bx + c
        """
        return 3 * self.a, 2 * self.b, self.c

    def second_derivative(self) -> Tuple[float, float]:
        """
        Second derivative:
            f''(x) = 6ax + 2b
        """
        return 6 * self.a, 2 * self.b

    def inflection_point(self) -> Tuple[float, float]:
        """
        Return inflection point (x, y).
        """
        x = -self.b / (3 * self.a)
        return x, self.value_at(x)

    def critical_points(self) -> List[float]:
        """
        Return x-values of local extrema (if any).
        """
        a, b, c = self.derivative()
        disc = b**2 - 4 * a * c

        if disc < 0:
            return []

        sqrt_d = disc**0.5
        return [
            (-b + sqrt_d) / (2 * a),
            (-b - sqrt_d) / (2 * a),
        ]

    # ------------------------------------------------------------------
    # Representations
    # ------------------------------------------------------------------
    def __str__(self) -> str:
        return f"{self.a}x³ + {self.b}x² + {self.c}x + {self.d} = 0"

    def __latex__(self) -> str:
        return f"{self.a}x^3 + {self.b}x^2 + {self.c}x + {self.d} = 0"
