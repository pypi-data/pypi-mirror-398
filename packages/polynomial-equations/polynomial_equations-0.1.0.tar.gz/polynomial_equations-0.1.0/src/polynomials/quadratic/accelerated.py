from numba import njit


@njit(cache=True)
def quadratic_value(a: float, b: float, c: float, x: float) -> float:
    return a * x * x + b * x + c
