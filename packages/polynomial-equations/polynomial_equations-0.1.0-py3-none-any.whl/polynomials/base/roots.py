from typing import Tuple
import cmath


def quadratic_roots(a: float, b: float, c: float) -> Tuple[complex, complex]:
    d = b * b - 4 * a * c
    sqrt_d = cmath.sqrt(d)
    return (
        (-b + sqrt_d) / (2 * a),
        (-b - sqrt_d) / (2 * a),
    )
