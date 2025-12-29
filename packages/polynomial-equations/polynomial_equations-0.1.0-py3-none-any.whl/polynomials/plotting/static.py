import numpy as np
import matplotlib.pyplot as plt


def plot_function(func, x_range=(-10, 10)) -> None:
    x = np.linspace(*x_range, 400)
    y = [func(v) for v in x]
    plt.plot(x, y)
    plt.show()
