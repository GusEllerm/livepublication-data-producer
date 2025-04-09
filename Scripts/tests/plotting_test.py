import json
import os
import shutil
import tempfile

import numpy as np
import rasterio
from rasterio.transform import from_origin

from utils.plotting import plot_image, plot_tile_product_overlay


def test_plot_image_saves_file_and_clipping():
    temp_dir = tempfile.mkdtemp()
    try:
        image = np.random.rand(100, 100)
        save_path = os.path.join(temp_dir, "test_plot.png")

        # Should save without error
        plot_image(image=image, save_path=save_path, factor=1.0, clip_range=(0, 1), cmap="viridis")

        assert os.path.exists(save_path)
    finally:
        shutil.rmtree(temp_dir)

def test_plot_tile_product_overlay_generates_png():
    temp_dir = tempfile.mkdtemp()
    try:
        imagery_dir = os.path.join(temp_dir, "imagery")
        metadata_dir = os.path.join(temp_dir, "metadata")
        os.makedirs(imagery_dir, exist_ok=True)
        os.makedirs(metadata_dir, exist_ok=True)

        # Create a dummy true_color.tif with RGB bands
        test_img_path = os.path.join(imagery_dir, "true_color.tif")
        dummy_data = np.ones((3, 10, 10), dtype=np.uint8) * 255
        transform = from_origin(0, 10, 1, 1)
        with rasterio.open(
            test_img_path, "w", driver="GTiff", height=10, width=10, count=3, dtype=dummy_data.dtype, transform=transform
        ) as dst:
            dst.write(dummy_data)

        # Create a dummy workflow_tile_metadata.json
        tile_meta_path = os.path.join(metadata_dir, "workflow_tile_metadata.json")
        tile_bbox = [0, 0, 10, 10]
        json.dump({
            "tile0": {
                "bbox": tile_bbox,
                "crs": "EPSG:4326"
            }
        }, open(tile_meta_path, "w"))

        # Create dummy selected_orbit file
        orbit_meta_path = os.path.join(metadata_dir, "tile0_selected_orbit.json")
        json.dump({
            "product_ids": ["PRODUCT_X"]
        }, open(orbit_meta_path, "w"))

        paths = {"imagery": imagery_dir, "metadata": metadata_dir}
        output_path = plot_tile_product_overlay(paths)

        assert os.path.exists(output_path)
    finally:
        shutil.rmtree(temp_dir)
