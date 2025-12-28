import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg


def fig2im(fig, tight_layout=True):
    canvas = FigureCanvasAgg(fig)
    if tight_layout:
        fig.tight_layout(pad=0.0)
    canvas.draw()
    image = np.frombuffer(canvas.buffer_rgba(), dtype=np.uint8)
    image = image.reshape(canvas.get_width_height()[::-1] + (4,))  # Shape: (H, W, 4)
    plt.close(fig)
    return image
