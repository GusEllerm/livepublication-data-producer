import os

import numpy as np
import pytest
import rasterio
from rasterio.crs import CRS

from utils.file_io import clean_all_outputs, save_geotiff

TEST_OUTPUT_DIR = "test_outputs"
TEST_FILE = os.path.join(TEST_OUTPUT_DIR, "test.tif")

@pytest.fixture(scope="function")
def setup_test_dir():
    os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)
    yield
    clean_all_outputs(TEST_OUTPUT_DIR)
    if os.path.exists(TEST_OUTPUT_DIR):
        os.rmdir(TEST_OUTPUT_DIR)

def test_save_geotiff_grayscale(setup_test_dir):
    array = np.random.rand(50, 50).astype(np.float32)
    bbox = [0.0, 0.0, 1.0, 1.0]
    crs = CRS.from_epsg(4326)

    save_geotiff(array, TEST_FILE, bbox, crs)

    assert os.path.exists(TEST_FILE)

    with rasterio.open(TEST_FILE) as src:
        assert src.count == 1
        assert src.width == 50
        assert src.height == 50
        assert src.crs == crs

def test_save_geotiff_rgb(setup_test_dir):
    array = np.random.rand(50, 50, 3).astype(np.float32)
    bbox = [0.0, 0.0, 1.0, 1.0]
    crs = CRS.from_epsg(4326)

    save_geotiff(array, TEST_FILE, bbox, crs)

    assert os.path.exists(TEST_FILE)

    with rasterio.open(TEST_FILE) as src:
        assert src.count == 3
        assert src.width == 50
        assert src.height == 50

def test_clean_all_outputs_removes_files_and_dirs(tmp_path):
    # Create mock files and folders
    tiles_dir = tmp_path / "tiles_test"
    tiles_dir.mkdir()
    for ext in [".npy", ".tif", ".png"]:
        (tmp_path / f"test{ext}").write_text("mock content")

    # Run cleanup
    clean_all_outputs(str(tmp_path))

    assert not tiles_dir.exists()
    assert not any(tmp_path.glob("*.npy"))
    assert not any(tmp_path.glob("*.tif"))
    assert not any(tmp_path.glob("*.png"))
