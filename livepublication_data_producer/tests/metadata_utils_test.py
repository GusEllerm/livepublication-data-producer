import json
import os
import tempfile
from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from sentinelhub import BBox, SHConfig
from shapely.geometry import Polygon, box
from utils.metadata_utils import (
    compute_orbit_bbox,
    discover_metadata_for_tiles,
    discover_orbit_data_metadata,
    discover_orbit_metadata,
    has_valid_orbits,
    select_best_orbit,
    select_orbits_for_tiles,
    write_selected_orbit,
    write_workflow_tile_metadata,
)


def test_compute_orbit_bbox_with_valid_tiles():
    # Create mock tile data in EPSG:4326
    polygon = Polygon([
        (149.75, -37.30),
        (149.76, -37.30),
        (149.76, -37.31),
        (149.75, -37.31),
        (149.75, -37.30)
    ])
    orbit = {
        "tiles": [
            {
                "dataGeometry": {
                    "type": "Polygon",
                    "crs": {
                        "type": "name",
                        "properties": {
                            "name": "EPSG:4326"
                        }
                    },
                    "coordinates": [list(polygon.exterior.coords)]
                }
            }
        ]
    }

    result = compute_orbit_bbox(orbit)
    assert result.bounds == polygon.bounds
    assert result.contains(polygon)

def test_compute_orbit_bbox_with_no_tiles():
    orbit = {"tiles": []}
    with pytest.raises(ValueError, match="No valid geometries found in orbit."):
        compute_orbit_bbox(orbit)

@patch("utils.metadata_utils.SentinelHubRequest")
def test_discover_orbit_metadata(mock_request_cls):
    temp_dir = tempfile.mkdtemp()
    try:
        paths = {"metadata": os.path.join(temp_dir, "metadata")}
        os.makedirs(paths["metadata"], exist_ok=True)

        bbox = BBox(bbox=[149.75, -37.31, 149.76, -37.30], crs="EPSG:4326")
        time_interval = (date(2022, 1, 1), date(2022, 1, 2))
        config = SHConfig()
        evalscript = "// dummy evalscript"
        prefix = "test_tile"

        mock_response = {"userdata.json": {"orbit_id": "orbit123"}}
        mock_request_instance = MagicMock()
        mock_request_instance.get_data.return_value = [mock_response]
        mock_request_cls.return_value = mock_request_instance

        metadata = discover_orbit_metadata(
            paths=paths,
            tile=bbox,
            time_interval=time_interval,
            config=config,
            evalscript=evalscript,
            prefix=prefix,
        )

        expected_path = os.path.join(paths["metadata"], "test_tile_orbit_metadata.json")
        assert os.path.exists(expected_path)

        with open(expected_path) as f:
            saved = json.load(f)
        assert saved["orbit_id"] == "orbit123"
        assert "tile_bbox" in saved
        assert saved["tile_bbox"] == list(bbox)

    finally:
        import shutil
        shutil.rmtree(temp_dir)

def test_select_best_orbit_least_cloud():
    class DummyProfile:
        orbit_selection_strategy = "least_cloud"

    metadata = {
        "orbits": [
            {
                "dateFrom": "2022-01-01T00:00:00Z",
                "tiles": [
                    {"cloudCoverage": 50.0, "productId": "A", "tileId": 1},
                    {"cloudCoverage": 40.0, "productId": "B", "tileId": 2}
                ],
                "orbitGeometry": {},
                "tilesBBox": [[149.75, -37.31, 149.76, -37.30]]
            },
            {
                "dateFrom": "2022-01-02T00:00:00Z",
                "tiles": [
                    {"cloudCoverage": 20.0, "productId": "C", "tileId": 3},
                    {"cloudCoverage": 30.0, "productId": "D", "tileId": 4}
                ]
            }
        ]
    }

    # Inject compute_orbit_bbox patch to simulate full tile coverage
    with patch("utils.metadata_utils.compute_orbit_bbox") as mock_bbox:
        mock_bbox.return_value = box(149.75, -37.31, 149.76, -37.30)  # Perfect match
        tile_bbox = [149.75, -37.31, 149.76, -37.30]
        result = select_best_orbit(metadata, DummyProfile(), tile_bbox)

    assert result["strategy"] == "least_cloud"
    assert result["orbit_date"] == "2022-01-02"
    assert result["cloud_coverage"] == 25.0
    assert result["product_ids"] == ["C", "D"]
    assert result["tile_ids"] == [3, 4]

def test_write_selected_orbit_creates_json_file():
    temp_dir = tempfile.mkdtemp()
    try:
        paths = {"metadata": os.path.join(temp_dir, "metadata")}
        orbit_data = {
            "strategy": "least_cloud",
            "orbit_date": "2022-01-02",
            "product_ids": ["C", "D"],
            "tile_ids": [3, 4],
            "cloud_coverage": 25.0,
            "orbit": {"tiles": []}
        }
        prefix = "test_tile"

        write_selected_orbit(paths, orbit_data, prefix)

        expected_path = os.path.join(paths["metadata"], "test_tile_selected_orbit.json")
        assert os.path.exists(expected_path)

        with open(expected_path, "r") as f:
            saved = json.load(f)
        assert saved == orbit_data

    finally:
        import shutil
        shutil.rmtree(temp_dir)

@patch("utils.metadata_utils.discover_orbit_metadata")
@patch("utils.metadata_utils.get_orbit_metadata_path")
def test_discover_metadata_for_tiles(mock_get_metadata_path, mock_discover_metadata):
    temp_dir = tempfile.mkdtemp()
    try:
        paths = {"metadata": os.path.join(temp_dir, "metadata")}
        os.makedirs(paths["metadata"], exist_ok=True)

        # Prepare mock tile BBoxes
        tiles = [
            [149.75, -37.31, 149.76, -37.30],
            [149.76, -37.31, 149.77, -37.30]
        ]

        # Dummy profile with region and time_interval
        class DummyProfile:
            region = "Test Region"
            time_interval = (date(2022, 1, 1), date(2022, 1, 2))

        config = SHConfig()
        evalscript = "// dummy evalscript"

        # Write dummy metadata files to simulate discover_orbit_metadata output
        for i, tile in enumerate(tiles):
            prefix = f"test_region_tile{i}"
            metadata = {"orbit_id": f"orbit_{i}"}
            metadata_path = os.path.join(paths["metadata"], f"{prefix}_orbit_metadata.json")
            with open(metadata_path, "w") as f:
                json.dump(metadata, f)
            mock_get_metadata_path.side_effect = lambda paths, p=prefix: os.path.join(paths["metadata"], f"{p}_orbit_metadata.json")

        result = discover_metadata_for_tiles(
            paths=paths,
            tiles=tiles,
            profile=DummyProfile(),
            config=config,
            evalscript=evalscript
        )

        assert list(result.keys()) == ["test_region_tile0", "test_region_tile1"]
        assert result["test_region_tile0"]["orbit_id"] == "orbit_0"
        assert result["test_region_tile1"]["orbit_id"] == "orbit_1"

    finally:
        import shutil
        shutil.rmtree(temp_dir)

@patch("utils.metadata_utils.select_best_orbit")
@patch("utils.metadata_utils.write_selected_orbit")
def test_select_orbits_for_tiles(mock_write_orbit, mock_select_orbit):
    temp_dir = tempfile.mkdtemp()
    try:
        paths = {"metadata": os.path.join(temp_dir, "metadata")}
        os.makedirs(paths["metadata"], exist_ok=True)

        metadata_by_tile = {
            "test_region_tile0": {"orbits": ["dummy"]},
            "test_region_tile1": {"orbits": ["dummy"]}
        }

        tile_bboxes = {
            "tile0": {"bbox": [149.75, -37.31, 149.76, -37.30]},
            "tile1": {"bbox": [149.76, -37.31, 149.77, -37.30]}
        }

        with open(os.path.join(paths["metadata"], "workflow_tile_metadata.json"), "w") as f:
            json.dump(tile_bboxes, f)

        class DummyProfile:
            orbit_selection_strategy = "least_cloud"
            time_interval = (date(2022, 1, 1), date(2022, 1, 2))
            region = "Test Region"

        mock_select_orbit.side_effect = lambda metadata, profile, tile_bbox: {
            "strategy": profile.orbit_selection_strategy,
            "orbit_date": "2022-01-01",
            "product_ids": ["X", "Y"],
            "tile_ids": [1, 2],
            "cloud_coverage": 42.0,
            "orbit": {"tiles": []}
        }

        result = select_orbits_for_tiles(paths, metadata_by_tile, DummyProfile())

        assert list(result.keys()) == ["test_region_tile0", "test_region_tile1"]
        for orbit in result.values():
            assert orbit["strategy"] == "least_cloud"
            assert orbit["orbit_date"] == "2022-01-01"
            assert orbit["product_ids"] == ["X", "Y"]

    finally:
        import shutil
        shutil.rmtree(temp_dir)

@patch("utils.metadata_utils.SentinelHubCatalog")
def test_discover_orbit_data_metadata(mock_catalog_cls):
    temp_dir = tempfile.mkdtemp()
    try:
        paths = {"metadata": os.path.join(temp_dir, "metadata")}
        os.makedirs(paths["metadata"], exist_ok=True)

        # Create two selected orbit files with overlapping and unique product IDs
        orbit_1 = {
            "product_ids": ["A", "B"]
        }
        orbit_2 = {
            "product_ids": ["B", "C"]
        }
        with open(os.path.join(paths["metadata"], "tile0_selected_orbit.json"), "w") as f:
            json.dump(orbit_1, f)
        with open(os.path.join(paths["metadata"], "tile1_selected_orbit.json"), "w") as f:
            json.dump(orbit_2, f)

        # Mock catalog responses
        mock_catalog = MagicMock()
        mock_catalog.search.side_effect = lambda collection, ids: [{"id": ids[0], "mock": True}]
        mock_catalog_cls.return_value = mock_catalog

        config = SHConfig()
        result = discover_orbit_data_metadata(paths, config)

        expected_path = os.path.join(paths["metadata"], "product_metadata.json")
        assert os.path.exists(expected_path)

        with open(expected_path, "r") as f:
            saved = json.load(f)

        assert len(saved) == 3
        assert set(saved.keys()) == {"A", "B", "C"}
        for metadata in saved.values():
            assert metadata["mock"] is True

    finally:
        import shutil
        shutil.rmtree(temp_dir)

def test_has_valid_orbits_true_and_false_cases():
    valid_metadata = {
        "tile1": {"orbits": [{"orbit_id": "A"}]},
        "tile2": {"orbits": []}
    }
    invalid_metadata = {
        "tile1": {"orbits": []},
        "tile2": {"orbits": []}
    }
    assert has_valid_orbits(valid_metadata) is True
    assert has_valid_orbits(invalid_metadata) is False

def test_write_workflow_tile_metadata_creates_expected_file():
    temp_dir = tempfile.mkdtemp()
    try:
        paths = {"metadata": os.path.join(temp_dir, "metadata")}
        tiles = [
            BBox([149.75, -37.31, 149.76, -37.30], crs="EPSG:4326"),
            BBox([149.76, -37.31, 149.77, -37.30], crs="EPSG:4326")
        ]

        write_workflow_tile_metadata(paths, tiles)

        metadata_path = os.path.join(paths["metadata"], "workflow_tile_metadata.json")
        assert os.path.exists(metadata_path)

        with open(metadata_path, "r") as f:
            content = json.load(f)

        assert "tile0" in content
        assert content["tile0"]["bbox"] == [149.75, -37.31, 149.76, -37.30]
        assert content["tile0"]["crs"] == "EPSG:4326"
        assert "tile1" in content

    finally:
        import shutil
        shutil.rmtree(temp_dir)
