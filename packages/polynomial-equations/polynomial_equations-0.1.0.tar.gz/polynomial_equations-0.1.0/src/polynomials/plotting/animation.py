import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation


def animate(func):
    fig, ax = plt.subplots()
    x = np.linspace(-10, 10, 400)
    line, = ax.plot([], [])

    def update(frame):
        y = func(x + frame / 10)
        line.set_data(x, y)
        return line,

    FuncAnimation(fig, update, frames=100)
    plt.show()
