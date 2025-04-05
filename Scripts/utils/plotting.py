import numpy as np
import matplotlib.pyplot as plt
from typing import Any

def plot_image(
    image: np.ndarray,
    factor: float = 1.0,
    clip_range: tuple[float, float] | None = None,
    save_path: str | None = None,
    title: str | None = None,
    **kwargs: Any
) -> None:
    """
    Plot an image with optional clipping and save it to a file.
    Args:
        image (np.ndarray): Image to plot.
        factor (float): Factor to multiply the image by.
        clip_range (tuple): Range to clip the image values.
        save_path (str): Path to save the image.
        title (str): Optional plot title.
        **kwargs: Additional arguments for plt.imshow.
    """
    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(15, 15))
    if clip_range is not None:
        ax.imshow(np.clip(image * factor, *clip_range), **kwargs)
    else:
        ax.imshow(image * factor, **kwargs)

    if title:
        ax.set_title(title)

    ax.set_xticks([])
    ax.set_yticks([])

    if save_path:
        fig.savefig(save_path, bbox_inches='tight', pad_inches=0)
        plt.close(fig)
    else:
        plt.show()