from typing import Tuple, List


def inflection_point(a: float, b: float, c: float, d: float) -> Tuple[float, float]:
    """
    Compute inflection point of cubic.
    """
    x = -b / (3 * a)
    y = a * x**3 + b * x**2 + c * x + d
    return x, y


def critical_points(a: float, b: float, c: float) -> List[float]:
    """
    Return x-values of local extrema.
    """
    disc = (2 * b)**2 - 4 * 3 * a * c
    if disc < 0:
        return []

    sqrt_d = disc**0.5
    return [
        (-2 * b + sqrt_d) / (6 * a),
        (-2 * b - sqrt_d) / (6 * a),
    ]
