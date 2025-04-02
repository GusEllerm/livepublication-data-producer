import numpy as np
import pytest
import os
import matplotlib.pyplot as plt
from utils import (
    compute_ndvi,
    rasterize_true_color,
    generate_safe_tiles,
    stitch_tiles,
    save_geotiff,
    plot_image,
    download_safe_tiles,
    SentinelHubRequest
)
from sentinelhub import BBox, CRS
import rasterio
from rasterio.crs import CRS as RioCRS

def test_compute_ndvi_basic():
    """Test NDVI calculation with basic input."""
    red = np.full((2, 2), 0.2)
    nir = np.full((2, 2), 0.6)
    data = np.stack([
        np.zeros((2, 2)),  # B02
        np.zeros((2, 2)),  # B03
        red,               # B04 (Red)
        nir,               # B08 (NIR)
        np.zeros((2, 2)),  # B11
        np.zeros((2, 2)),  # B12
    ], axis=-1)
    ndvi = compute_ndvi(data)
    assert np.allclose(ndvi, 0.5)

def test_rasterize_true_color_range():
    """Test rasterization of true color with basic input."""
    red = np.full((2, 2), 0.1)
    green = np.full((2, 2), 0.3)
    blue = np.full((2, 2), 0.5)
    data = np.stack([blue, green, red] + [np.zeros((2, 2))]*3, axis=-1)
    rgb = rasterize_true_color(data)
    assert rgb.shape == (2, 2, 3)
    assert np.all(rgb <= 1.0)

def test_generate_safe_tiles_basic():
    """Test generation of safe tiles with basic input."""
    aoi = [172.0, -44.0, 172.1, -43.9]
    resolution = 10
    tiles = generate_safe_tiles(aoi, resolution=resolution, max_dim=2500, buffer=1.0)
    assert isinstance(tiles, list)
    assert all(isinstance(t, BBox) for t in tiles)
    assert all(t.crs == CRS.WGS84 for t in tiles)
    for t in tiles:
        assert t.min_x >= aoi[0]
        assert t.min_y >= aoi[1]
        assert t.max_x <= aoi[2]
        assert t.max_y <= aoi[3]
    assert len(tiles) == 1

def test_stitch_tiles(tmp_path):
    """Test stitching tiles with different heights and widths to trigger padding logic."""
    # First row: 2 tiles of height 2
    tile_shape_1 = (2, 2, 3)
    tile_0 = np.ones(tile_shape_1) * 1
    tile_1 = np.ones(tile_shape_1) * 2

    # Second row: 2 tiles of different height (one will trigger resize)
    tile_shape_2a = (2, 2, 3)
    tile_shape_2b = (1, 2, 3)  # shorter to trigger height padding
    tile_2 = np.ones(tile_shape_2a) * 3
    tile_3 = np.ones(tile_shape_2b) * 4

    # Save all tiles
    paths = []
    for i, tile in enumerate([tile_0, tile_1, tile_2, tile_3]):
        path = tmp_path / f"tile_{i:03}.npy"
        np.save(path, tile)
        paths.append(path)

    # BBoxes: First row (lat -1.0), second row (lat -2.0)
    bbox_row1 = -1.0
    bbox_row2 = -2.0
    tile_info = [
        (paths[0].name, BBox([0, bbox_row1, 1, bbox_row1 + 1], crs=CRS.WGS84)),
        (paths[1].name, BBox([1, bbox_row1, 2, bbox_row1 + 1], crs=CRS.WGS84)),
        (paths[2].name, BBox([0, bbox_row2, 1, bbox_row2 + 1], crs=CRS.WGS84)),
        (paths[3].name, BBox([1, bbox_row2, 2, bbox_row2 + 1], crs=CRS.WGS84)),
    ]

    result = stitch_tiles(str(tmp_path), tile_info)

    # Check shape reflects two rows, and all widths aligned
    assert result.shape[0] > 2  # height must increase due to padding
    assert result.shape[1] > 2  # width must increase due to row resize
    assert result.shape[2] == 3

def test_save_geotiff_ndvi(tmp_path):
    """Test saving NDVI as GeoTIFF."""
    array = np.array([[0.1, 0.2], [0.3, 0.4]], dtype=np.float32)
    bbox = (172.0, -44.0, 172.1, -43.9)
    crs = RioCRS.from_epsg(4326)
    out_path = tmp_path / "ndvi_test.tif"
    save_geotiff(array, str(out_path), bbox, crs)
    with rasterio.open(out_path) as src:
        data = src.read(1)
        assert src.crs == crs
        assert src.bounds.left == bbox[0]
        assert src.bounds.bottom == bbox[1]
        assert data.shape == (2, 2)
        assert np.allclose(data, array)

def test_save_geotiff_rgb(tmp_path):
    """Test saving RGB as GeoTIFF."""
    rgb = np.zeros((2, 2, 3), dtype=np.float32)
    rgb[..., 0] = 0.2
    rgb[..., 1] = 0.4
    rgb[..., 2] = 0.6
    bbox = (100.0, 0.0, 100.2, 0.2)
    crs = RioCRS.from_epsg(4326)
    out_path = tmp_path / "rgb_test.tif"
    save_geotiff(rgb, str(out_path), bbox, crs)
    with rasterio.open(out_path) as src:
        data = src.read()
        assert data.shape == (3, 2, 2)
        assert np.allclose(data[0], 0.2)
        assert np.allclose(data[1], 0.4)
        assert np.allclose(data[2], 0.6)

def test_plot_image_no_save(monkeypatch):
    """Test plotting an image without saving."""
    # Monkeypatch plt.show to prevent GUI window
    monkeypatch.setattr(plt, "show", lambda: None)
    image = np.ones((2, 2, 3), dtype=np.float32)
    plot_image(image, factor=1.0)

def test_plot_image_with_save(tmp_path):
    """Test plotting an image and saving it."""
    image = np.ones((2, 2, 3), dtype=np.float32)
    out_path = tmp_path / "test_image.png"
    plot_image(image, factor=1.0, save_path=str(out_path))
    assert out_path.exists()

def test_download_safe_tiles_success(tmp_path, monkeypatch):
    """Test that download_safe_tiles function successfully downloads safe tiles using a mocked SentinelHubRequest.
    
    This test verifies that:
    - The function correctly processes a valid, mocked request.
    - A .npy file is created with the expected shape and data.
    - The returned tile_info list contains the correct tile information.
    - No failed tiles are reported.
    """
    from utils import download_safe_tiles
    from sentinelhub import BBox, CRS
    import utils  # for monkeypatch target

    tiles = [BBox([0, 0, 0.1, 0.1], crs=CRS.WGS84)]
    time_interval = ("2022-01-01", "2022-01-31")
    config = None
    evalscript = "// mock script"

    # Dummy response class
    class DummyRequest:
        def __init__(self, **kwargs): pass
        def get_data(self): return [np.ones((2, 2, 3))]

        @classmethod
        def input_data(cls, **kwargs): return kwargs
        @classmethod
        def output_response(cls, *args, **kwargs): return args

    # Patch the entire class
    monkeypatch.setattr(utils, "SentinelHubRequest", DummyRequest)

    tile_info, failed_tiles = download_safe_tiles(
        tiles, time_interval, config, evalscript, output_dir=tmp_path, prefix="test"
    )

    assert len(tile_info) == 1
    assert len(failed_tiles) == 0
    saved_file = tmp_path / "test_000.npy"
    assert saved_file.exists()
    data = np.load(saved_file)
    assert data.shape == (2, 2, 3)

def test_download_safe_tiles_failure(tmp_path, monkeypatch):
    """Test that download_safe_tiles gracefully handles failed API calls."""
    from utils import download_safe_tiles
    from sentinelhub import BBox, CRS
    import utils  # for monkeypatch target

    tiles = [BBox([0, 0, 0.1, 0.1], crs=CRS.WGS84)]
    time_interval = ("2022-01-01", "2022-01-31")
    config = None
    evalscript = "// mock script"

    class DummyRequest:
        def __init__(self, **kwargs): pass
        def get_data(self): raise RuntimeError("Simulated API failure")

        @classmethod
        def input_data(cls, **kwargs): return kwargs
        @classmethod
        def output_response(cls, *args, **kwargs): return args

    monkeypatch.setattr(utils, "SentinelHubRequest", DummyRequest)

    tile_info, failed_tiles = download_safe_tiles(
        tiles, time_interval, config, evalscript, output_dir=tmp_path, prefix="fail"
    )

    assert len(tile_info) == 0
    assert len(failed_tiles) == 1

def test_compute_stitched_bbox():
    """Test computing stitched bounding box from tile_info."""
    from utils import compute_stitched_bbox
    from sentinelhub import BBox, CRS

    tile_info = [
        ("tile_001.npy", BBox([100.0, 0.0, 100.1, 0.1], crs=CRS.WGS84)),
        ("tile_002.npy", BBox([100.1, 0.0, 100.2, 0.1], crs=CRS.WGS84)),
        ("tile_003.npy", BBox([100.0, 0.1, 100.1, 0.2], crs=CRS.WGS84))
    ]

    stitched_bbox = compute_stitched_bbox(tile_info)

    expected_bbox = (100.0, 0.0, 100.2, 0.2)
    assert stitched_bbox == expected_bbox

def test_clean_all_outputs(tmp_path, capsys):
    """Test clean_all_outputs removes tiles_* dirs and .npy/.tif/.png files."""
    from utils import clean_all_outputs

    # Setup test files and folders
    tile_dir = tmp_path / "tiles_testregion"
    tile_dir.mkdir()
    (tile_dir / "dummy.npy").write_text("data")

    for ext in [".npy", ".tif", ".png"]:
        (tmp_path / f"output{ext}").write_text("data")

    # Run cleanup
    clean_all_outputs(base_path=str(tmp_path))

    # Assert removals
    assert not tile_dir.exists()
    for ext in [".npy", ".tif", ".png"]:
        assert not (tmp_path / f"output{ext}").exists()

    # Check output messages
    captured = capsys.readouterr()
    assert "Removed directory" in captured.out
    assert "Removed file" in captured.out
    assert "Cleanup complete" in captured.out