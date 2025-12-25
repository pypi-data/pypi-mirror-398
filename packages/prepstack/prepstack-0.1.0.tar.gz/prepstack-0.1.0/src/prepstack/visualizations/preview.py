import matplotlib.pyplot as plt
import numpy as np

def preview_theme():
    x = np.linspace(0, 10, 100)
    y = np.sin(x)

    fig, axs = plt.subplots(1, 2, figsize=(12,5))

    axs[0].plot(x, y)
    axs[0].set_title("Line Plot Preview")

    axs[1].bar([1,2,3], [3,5,2])
    axs[1].set_title("Bar Chart Preview")

    plt.show()
