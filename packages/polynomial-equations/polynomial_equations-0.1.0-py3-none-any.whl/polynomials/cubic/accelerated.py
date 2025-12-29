from numba import njit


@njit(cache=True, fastmath=True)
def cubic_value(
    a: float,
    b: float,
    c: float,
    d: float,
    x: float,
) -> float:
    """
    Fast cubic evaluation.
    """
    return a * x**3 + b * x**2 + c * x + d
