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
    red = np.full((2, 2), 0.1)
    green = np.full((2, 2), 0.3)
    blue = np.full((2, 2), 0.5)
    data = np.stack([blue, green, red] + [np.zeros((2, 2))]*3, axis=-1)
    rgb = rasterize_true_color(data)
    assert rgb.shape == (2, 2, 3)
    assert np.all(rgb <= 1.0)

def test_generate_safe_tiles_basic():
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
    tile_shape = (2, 2, 3)
    tile_0 = np.ones(tile_shape) * 1
    tile_1 = np.ones(tile_shape) * 2
    path_0 = tmp_path / "tile_000.npy"
    path_1 = tmp_path / "tile_001.npy"
    np.save(path_0, tile_0)
    np.save(path_1, tile_1)
    bbox_0 = BBox([0, 0, 1, 1], crs=CRS.WGS84)
    bbox_1 = BBox([1, 0, 2, 1], crs=CRS.WGS84)
    tile_info = [(path_0.name, bbox_0), (path_1.name, bbox_1)]
    result = stitch_tiles(str(tmp_path), tile_info)
    assert result.shape == (2, 4, 3)
    assert np.all(result[:, :2, :] == 1)
    assert np.all(result[:, 2:, :] == 2)

def test_save_geotiff_ndvi(tmp_path):
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
    # Monkeypatch plt.show to prevent GUI window
    monkeypatch.setattr(plt, "show", lambda: None)
    image = np.ones((2, 2, 3), dtype=np.float32)
    plot_image(image, factor=1.0)

def test_plot_image_with_save(tmp_path):
    image = np.ones((2, 2, 3), dtype=np.float32)
    out_path = tmp_path / "test_image.png"
    plot_image(image, factor=1.0, save_path=str(out_path))
    assert out_path.exists()

# def test_download_safe_tiles_success(tmp_path, monkeypatch):
#     from utils import download_safe_tiles
#     from sentinelhub import BBox, CRS

#     tiles = [BBox([0, 0, 0.1, 0.1], crs=CRS.WGS84)]
#     time_interval = ("2022-01-01", "2022-01-31")
#     config = None
#     evalscript = "// mock script"

#     class DummyRequest:
#         def __init__(self, **kwargs): pass
#         def get_data(self): return [np.ones((2, 2, 3))]

#     monkeypatch.setattr("utils.SentinelHubRequest", DummyRequest)

#     tile_info, failed_tiles = download_safe_tiles(
#         tiles, time_interval, config, evalscript, output_dir=tmp_path, prefix="test"
#     )

#     assert len(tile_info) == 1
#     assert len(failed_tiles) == 0
#     saved_file = tmp_path / "test_000.npy"
#     assert saved_file.exists()
#     data = np.load(saved_file)
#     assert data.shape == (2, 2, 3)

# def test_download_safe_tiles_failure(tmp_path, monkeypatch):
#     from utils import download_safe_tiles
#     from sentinelhub import BBox, CRS

#     tiles = [BBox([0, 0, 0.1, 0.1], crs=CRS.WGS84)]
#     time_interval = ("2022-01-01", "2022-01-31")
#     config = None
#     evalscript = "// mock script"

#     class DummyRequest:
#         def __init__(self, **kwargs): pass
#         def get_data(self): raise RuntimeError("Simulated API failure")

#     monkeypatch.setattr("utils.SentinelHubRequest", lambda *args, **kwargs: DummyRequest())

#     tile_info, failed_tiles = download_safe_tiles(
#         tiles, time_interval, config, evalscript, output_dir=tmp_path, prefix="fail"
#     )

#     assert len(tile_info) == 0
#     assert len(failed_tiles) == 1