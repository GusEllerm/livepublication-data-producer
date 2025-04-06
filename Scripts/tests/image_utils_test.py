

import os
import numpy as np
import tempfile
import shutil
import pytest
from sentinelhub import BBox, CRS

from utils.image_utils import (
    compute_ndvi,
    rasterize_true_color,
    compute_stitched_bbox,
    stitch_tiles
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