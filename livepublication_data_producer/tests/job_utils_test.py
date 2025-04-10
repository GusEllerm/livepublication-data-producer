import datetime
import os
import shutil
import zipfile

from utils.job_utils import (
    archive_job_outputs,
    generate_job_id,
    get_job_output_paths,
    get_orbit_metadata_path,
    get_stitched_array_path,
    get_tile_prefix,
    prepare_job_output_dirs,
)


class DummyConfig:
    def __init__(self, region, time_interval, parent_job_id=None):
        self.region = region
        self.time_interval = time_interval
        self.parent_job_id = parent_job_id

def test_generate_job_id_basic():
    config = DummyConfig("Test Region", (datetime.date(2023, 1, 1), datetime.date(2023, 1, 31)))
    job_id = generate_job_id(config)
    assert job_id == "test_region__20230101_20230131"

def test_generate_job_id_with_interval_override():
    config = DummyConfig("Another Region", (datetime.date(2022, 5, 1), datetime.date(2022, 5, 10)))
    override = (datetime.date(2022, 6, 1), datetime.date(2022, 6, 15))
    job_id = generate_job_id(config, interval=override)
    assert job_id == "another_region__20220601_20220615"

def test_generate_job_id_with_parent():
    config = DummyConfig("Example Area", (datetime.date(2023, 3, 1), datetime.date(2023, 3, 15)), parent_job_id="parent123")
    job_id = generate_job_id(config)
    assert job_id == "parent123/example_area__20230301_20230315"

def test_get_job_output_paths():
    class DummyConfigWithJobID:
        def __init__(self, job_id):
            self.job_id = job_id
            self.output_base_dir = "outputs"

    config = DummyConfigWithJobID("test_region__20230101_20230131")
    paths = get_job_output_paths(config)

    expected_base = os.path.join("outputs", "test_region__20230101_20230131")
    assert paths["base"] == expected_base
    assert paths["raw_tiles"] == os.path.join(expected_base, "raw_tiles")
    assert paths["imagery"] == os.path.join(expected_base, "imagery")
    assert paths["metadata"] == os.path.join(expected_base, "metadata")
    assert paths["stitched"] == os.path.join(expected_base, "stitched")

def test_prepare_job_output_dirs():
    class DummyConfigWithJobID:
        def __init__(self, job_id):
            self.job_id = job_id
            self.output_base_dir = "outputs"

    job_id = "test_region__20230101_20230131"
    config = DummyConfigWithJobID(job_id)
    base_path = os.path.join("outputs", job_id)

    try:
        paths = prepare_job_output_dirs(config)

        # Check all directories exist
        for key in ["base", "raw_tiles", "imagery", "metadata", "stitched"]:
            assert os.path.exists(paths[key])
            assert os.path.isdir(paths[key])
    finally:
        # Cleanup
        if os.path.exists(base_path):
            shutil.rmtree(base_path)

def test_archive_job_outputs():
    job_id = "test_region__20230101_20230131"
    base_dir = os.path.join("outputs", job_id)
    os.makedirs(base_dir, exist_ok=True)
    dummy_file_path = os.path.join(base_dir, "dummy.txt")

    with open(dummy_file_path, "w") as f:
        f.write("test")

    try:
        archive_path = archive_job_outputs(output_dir=base_dir, label="test_archive_job")
        assert os.path.exists(archive_path)
        assert zipfile.is_zipfile(archive_path)

        with zipfile.ZipFile(archive_path, 'r') as zipf:
            assert "dummy.txt" in zipf.namelist()
    finally:
        if os.path.exists(base_dir):
            shutil.rmtree(base_dir)
        archive_file = os.path.join("archive", "test_archive_job.zip")
        if os.path.exists(archive_file):
            os.remove(archive_file)

def test_get_tile_prefix():
    class DummyConfig:
        def __init__(self, region):
            self.region = region

    config = DummyConfig("Canterbury Plains")
    prefix = get_tile_prefix(config, 0)
    assert prefix == "canterbury_plains_tile0"

    prefix2 = get_tile_prefix(config, 5)
    assert prefix2 == "canterbury_plains_tile5"

def test_get_orbit_metadata_path():
    paths = {
        "metadata": "outputs/test_region__20230101_20230131/metadata"
    }
    tile_prefix = "testregion_tile0"
    expected_path = os.path.join(paths["metadata"], "testregion_tile0_orbit_metadata.json")
    assert get_orbit_metadata_path(paths, tile_prefix) == expected_path

def test_get_stitched_array_path():
    paths = {
        "stitched": "outputs/test_region__20230101_20230131/stitched"
    }
    expected_path = os.path.join(paths["stitched"], "stitched_raw_bands.npy")
    assert get_stitched_array_path(paths) == expected_path
