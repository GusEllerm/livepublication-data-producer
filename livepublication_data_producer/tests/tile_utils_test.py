import os
import tempfile
from unittest.mock import MagicMock, patch

import numpy as np
from sentinelhub import CRS, BBox, MimeType, SHConfig
from utils.tile_utils import (
    convert_tiles_to_bboxes,
    download_orbits_for_tiles,
    download_safe_tiles,
    generate_safe_tiles,
)


def test_generate_safe_tiles_creates_expected_tiles():
    temp_dir = tempfile.mkdtemp()
    try:
        paths = {"metadata": os.path.join(temp_dir, "metadata")}
        os.makedirs(paths["metadata"], exist_ok=True)

        aoi = [149.75, -37.31, 149.95, -37.10]  # Small bounding box
        tiles = generate_safe_tiles(paths=paths, aoi=aoi, resolution=10, max_dim=1000, buffer=1.0)

        assert isinstance(tiles, list)
        assert all(isinstance(tile, BBox) for tile in tiles)
        assert len(tiles) > 0

        metadata_path = os.path.join(paths["metadata"], "workflow_tile_metadata.json")
        assert os.path.exists(metadata_path)

    finally:
        import shutil
        shutil.rmtree(temp_dir)

@patch("utils.tile_utils.SentinelHubRequest")
def test_download_safe_tiles_with_mocked_request(mock_request_cls):
    temp_dir = tempfile.mkdtemp()
    try:
        paths = {"raw_tiles": os.path.join(temp_dir, "raw_tiles")}
        os.makedirs(paths["raw_tiles"], exist_ok=True)

        tiles = [BBox([149.75, -37.31, 149.76, -37.30], crs=CRS.WGS84)]
        time_interval = ("2022-01-01", "2022-01-02")
        config = SHConfig()
        evalscript = "// fake evalscript"

        dummy_data = np.ones((3, 100, 100), dtype=np.uint8)
        mock_request = MagicMock()
        mock_request.get_data.return_value = [dummy_data]
        mock_request_cls.return_value = mock_request

        tile_info, failed = download_safe_tiles(
            paths=paths,
            tiles=tiles,
            time_interval=time_interval,
            prefix="testprefix",
            config=config,
            evalscript=evalscript
        )

        assert len(tile_info) == 1
        assert len(failed) == 0
        assert tile_info[0][0].endswith(".npy")
        assert os.path.exists(os.path.join(paths["raw_tiles"], tile_info[0][0]))

    finally:
        import shutil
        shutil.rmtree(temp_dir)

@patch("utils.tile_utils.download_safe_tiles")
def test_download_orbits_for_tiles_with_mocked_download(mock_download_safe_tiles):
    temp_dir = tempfile.mkdtemp()
    try:
        paths = {"raw_tiles": os.path.join(temp_dir, "raw_tiles")}
        os.makedirs(paths["raw_tiles"], exist_ok=True)

        tiles = [
            BBox([149.75, -37.31, 149.76, -37.30], crs=CRS.WGS84),
            BBox([149.76, -37.31, 149.77, -37.30], crs=CRS.WGS84)
        ]

        selected_orbits = {
            "test_region_tile0": {"orbit_date": "2022-01-01"},
            "test_region_tile1": {"orbit_date": "2022-01-01"}
        }

        class DummyProfile:
            region = "Test Region"

        dummy_data = [("test_region_tile0_000.npy", tiles[0])]
        mock_download_safe_tiles.return_value = (dummy_data, [])

        config = SHConfig()
        evalscript = "// mock evalscript"

        tile_info, failed = download_orbits_for_tiles(
            paths=paths,
            tiles=tiles,
            selected_orbits=selected_orbits,
            profile=DummyProfile(),
            config=config,
            evalscript=evalscript
        )

        assert len(tile_info) == 2
        assert len(failed) == 0
        assert all(isinstance(item, tuple) for item in tile_info)

    finally:
        import shutil
        shutil.rmtree(temp_dir)

def test_convert_tiles_to_bboxes_creates_bboxes():
    tile_coords_list = [
        [149.75, -37.31, 149.76, -37.30],
        [149.76, -37.31, 149.77, -37.30]
    ]
    bboxes = convert_tiles_to_bboxes(tile_coords_list)
    
    assert isinstance(bboxes, list)
    assert all(isinstance(bbox, BBox) for bbox in bboxes)
    assert len(bboxes) == 2
    assert bboxes[0].lower_left == (149.75, -37.31)
    assert bboxes[1].upper_right == (149.77, -37.30)
