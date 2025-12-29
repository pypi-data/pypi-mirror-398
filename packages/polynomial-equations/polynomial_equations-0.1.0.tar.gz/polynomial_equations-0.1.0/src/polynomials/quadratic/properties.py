def vertex(a: float, b: float, c: float):
    x = -b / (2 * a)
    y = a * x * x + b * x + c
    return x, y
