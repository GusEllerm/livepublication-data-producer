import os
import shutil
import tempfile

import numpy as np
import pytest
from rasterio import open as rio_open
from rasterio.enums import Resampling
from sentinelhub import CRS, BBox
from utils.image_utils import (
    compute_ndvi,
    compute_stitched_bbox,
    generate_ndvi_products,
    generate_true_color_products,
    get_stitched_array_path,
    rasterize_true_color,
    stitch_raw_tile_data,
    stitch_tiles,
)


def test_compute_ndvi():
    stitched = np.zeros((2, 2, 4))
    stitched[..., 2] = 0.2  # Red
    stitched[..., 3] = 0.6  # NIR
    ndvi = compute_ndvi(stitched)
    expected = (0.6 - 0.2) / (0.6 + 0.2 + 1e-6)
    assert np.allclose(ndvi, expected)

def test_rasterize_true_color():
    stitched = np.zeros((2, 2, 4))
    stitched[..., 0] = 0.1  # Blue
    stitched[..., 1] = 0.2  # Green
    stitched[..., 2] = 0.3  # Red
    rgb = rasterize_true_color(stitched)
    assert rgb.shape == (2, 2, 3)
    assert np.all((rgb >= 0) & (rgb <= 1))

def test_compute_stitched_bbox():
    tiles = [
        ("tile1.npy", BBox([1, 1, 2, 2], crs=CRS.WGS84)),
        ("tile2.npy", BBox([2, 2, 3, 3], crs=CRS.WGS84))
    ]
    bbox = compute_stitched_bbox(tiles)
    assert bbox == (1, 1, 3, 3)

def test_stitch_tiles():
    temp_dir = tempfile.mkdtemp()
    try:
        tile1 = np.ones((2, 2, 6))
        tile2 = np.ones((2, 2, 6)) * 2
        np.save(os.path.join(temp_dir, "tile1.npy"), tile1)
        np.save(os.path.join(temp_dir, "tile2.npy"), tile2)

        tile_coords = [
            ("tile1.npy", BBox([0, 0, 1, 1], CRS.WGS84)),
            ("tile2.npy", BBox([1, 0, 2, 1], CRS.WGS84))
        ]

        stitched = stitch_tiles(temp_dir, tile_coords)
        assert stitched.shape[0] == 2
        assert stitched.shape[1] == 4
        assert stitched.shape[2] == 6
    finally:
        shutil.rmtree(temp_dir)

def test_stitch_raw_tile_data():
    temp_dir = tempfile.mkdtemp()
    try:
        # Create fake tiles
        tile1 = np.ones((2, 2, 6))
        tile2 = np.ones((2, 2, 6)) * 2
        tile1_path = os.path.join(temp_dir, "tile1.npy")
        tile2_path = os.path.join(temp_dir, "tile2.npy")
        np.save(tile1_path, tile1)
        np.save(tile2_path, tile2)

        tile_info = [
            ("tile1.npy", BBox([0, 0, 1, 1], CRS.WGS84)),
            ("tile2.npy", BBox([1, 0, 2, 1], CRS.WGS84))
        ]
        paths = {"raw_tiles": temp_dir, "stitched": temp_dir}

        # Patch get_stitched_array_path to point to temp_dir
        output_path = os.path.join(temp_dir, "stitched.npy")
        def mock_get_stitched_array_path(paths):
            return output_path

        original = get_stitched_array_path
        try:
            import utils.image_utils
            utils.image_utils.get_stitched_array_path = mock_get_stitched_array_path
            result = stitch_raw_tile_data(paths, tile_info)
        finally:
            utils.image_utils.get_stitched_array_path = original

        assert result.shape == (2, 4, 6)
        assert os.path.exists(output_path)
        saved = np.load(output_path)
        assert np.array_equal(saved, result)
    finally:
        shutil.rmtree(temp_dir)

def test_generate_ndvi_products():
    temp_dir = tempfile.mkdtemp()
    try:
        imagery_path = os.path.join(temp_dir, "imagery")
        os.makedirs(imagery_path, exist_ok=True)
        paths = {"imagery": imagery_path}

        # Create dummy stitched image with NDVI bands
        stitched_image = np.zeros((2, 2, 5))  # [B02, B03, B04, B08, SCL]
        stitched_image[..., 2] = 0.2  # Red (B04)
        stitched_image[..., 3] = 0.6  # NIR (B08)
        stitched_image[..., 4] = 1    # SCL (no clouds)

        tile_info = [("tile1.npy", BBox([0, 0, 1, 1], CRS.WGS84))]

        generate_ndvi_products(paths, tile_info, stitched_image)

        assert os.path.exists(os.path.join(imagery_path, "ndvi_cloud_mask.png"))
        assert os.path.exists(os.path.join(imagery_path, "ndvi.png"))
        assert os.path.exists(os.path.join(imagery_path, "ndvi.tif"))

        with rio_open(os.path.join(imagery_path, "ndvi.tif")) as src:
            ndvi_read = src.read(1, resampling=Resampling.nearest)
            assert ndvi_read.shape == (2, 2)
    finally:
        shutil.rmtree(temp_dir)

from utils.image_utils import generate_true_color_products


def test_generate_true_color_products():
    temp_dir = tempfile.mkdtemp()
    try:
        imagery_path = os.path.join(temp_dir, "imagery")
        os.makedirs(imagery_path, exist_ok=True)
        paths = {"imagery": imagery_path}

        # Create dummy stitched image with RGB bands
        stitched_image = np.zeros((2, 2, 4))  # [B02, B03, B04, B08]
        stitched_image[..., 0] = 0.1  # Blue (B02)
        stitched_image[..., 1] = 0.2  # Green (B03)
        stitched_image[..., 2] = 0.3  # Red (B04)

        tile_info = [("tile1.npy", BBox([0, 0, 1, 1], CRS.WGS84))]

        generate_true_color_products(paths, tile_info, stitched_image)

        assert os.path.exists(os.path.join(imagery_path, "true_color.png"))
        assert os.path.exists(os.path.join(imagery_path, "true_color.tif"))

        with rio_open(os.path.join(imagery_path, "true_color.tif")) as src:
            rgb_read = src.read()
            assert rgb_read.shape[1:] == (2, 2)
    finally:
        shutil.rmtree(temp_dir)

import json

import rasterio
from rasterio.transform import from_origin
from utils.image_utils import validate_image_coverage_with_tile_footprints


def test_validate_image_coverage_with_tile_footprints():
    temp_dir = tempfile.mkdtemp()
    try:
        stitched_path = os.path.join(temp_dir, "true_color.tif")
        orbit_json_path = os.path.join(temp_dir, "selected_orbit.json")
        output_png_path = os.path.join(temp_dir, "diagnostic.png")

        # Create a dummy stitched GeoTIFF with RGB data
        data = np.ones((3, 2, 2), dtype=np.uint8) * 100
        transform = from_origin(149.75, -37.30, 0.01, 0.01)
        with rasterio.open(
            stitched_path, 'w', driver='GTiff', height=2, width=2, count=3,
            dtype='uint8', crs='EPSG:4326', transform=transform
        ) as dst:
            dst.write(data)

        # Create a dummy orbit JSON with a simple tile footprint
        orbit_data = {
            "orbit": {
                "tiles": [
                    {
                        "dataEnvelope": {
                            "type": "Polygon",
                            "crs": {
                                "type": "name",
                                "properties": {
                                    "name": "EPSG:4326"
                                }
                            },
                            "coordinates": [[
                                [149.75, -37.30],
                                [149.76, -37.30],
                                [149.76, -37.31],
                                [149.75, -37.31],
                                [149.75, -37.30]
                            ]]
                        }
                    }
                ]
            }
        }
        with open(orbit_json_path, "w") as f:
            json.dump(orbit_data, f)

        # Run function and check PNG output
        validate_image_coverage_with_tile_footprints(
            stitched_image_path=stitched_path,
            selected_orbit_path=orbit_json_path,
            output_path=output_png_path
        )

        assert os.path.exists(output_png_path)
    finally:
        shutil.rmtree(temp_dir)