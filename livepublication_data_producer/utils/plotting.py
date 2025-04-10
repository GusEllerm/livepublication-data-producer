import glob
import json
import os
from typing import Any

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from rasterio.plot import show
from shapely.geometry import box
from utils.logging_utils import log_success, log_warning


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


def plot_tile_product_overlay(paths):
    """
    Visualize sub-tile bounding boxes over a stitched image, color-coded by contributing Sentinel-2 product.
    Args:
        paths (dict): Output paths dictionary.
    Returns:
        str: Path to the saved overlay image.
    """
    stitched_image_path = os.path.join(paths["imagery"], "true_color.tif")
    orbit_metadata_dir = paths["metadata"]
    tile_metadata_path = os.path.join(paths["metadata"], "workflow_tile_metadata.json")
    output_path = os.path.join(paths["imagery"], "product_overlay.png")

    with open(tile_metadata_path, "r") as f:
        tile_metadata = json.load(f)

    tile_bbox_lookup = {}
    for tile_key, metadata in tile_metadata.items():
        coords = metadata["bbox"]
        tile_bbox_lookup[tile_key] = box(*coords)

    with rasterio.open(stitched_image_path) as src:
        fig, ax = plt.subplots(figsize=(12, 12))
        show(src.read([1, 2, 3]), transform=src.transform, ax=ax)

        product_to_color = {}
        product_colors = plt.get_cmap('tab20', 20)
        legend_handles = []

        orbit_files = glob.glob(os.path.join(orbit_metadata_dir, "*_selected_orbit.json"))
        for idx, orbit_file in enumerate(orbit_files):
            prefix = os.path.basename(orbit_file).replace("_selected_orbit.json", "")
            tile_key = prefix.split("_")[-1] if "tile" in prefix else prefix
            with open(orbit_file, 'r') as f:
                metadata = json.load(f)

            product_ids = metadata.get("product_ids", [])
            if not product_ids:
                continue

            main_product_id = product_ids[0]
            if main_product_id not in product_to_color:
                color = product_colors(len(product_to_color))
                product_to_color[main_product_id] = color
                legend_handles.append(mpatches.Patch(color=color, label=main_product_id))

            if tile_key in tile_bbox_lookup:
                tile_geom = tile_bbox_lookup[tile_key]
                x, y = tile_geom.exterior.xy
                ax.plot(x, y, color=product_to_color[main_product_id], linewidth=2)

        ax.set_title("Sub-tile Coverage by Product ID")
        ax.legend(handles=legend_handles, loc='upper right', fontsize='small')

        fig.savefig(output_path, bbox_inches='tight', pad_inches=0)
        plt.close(fig)
        
    log_success(f"🗺️ Saved product overlay plot to {output_path}")
    return output_path