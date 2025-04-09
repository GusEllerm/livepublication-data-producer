import os
import shutil
import zipfile
from datetime import datetime

from utils.logging_utils import log_block, log_step


def generate_job_id(
        config: "DataAcquisitionConfig", 
        interval: tuple = None
    ) -> str:
    """
    Generate a human-readable job ID from a DataAcquisitionConfig object.
    Optionally override the time interval to customize the job ID.
    Args:
        config (DataAcquisitionConfig): The configuration object for a data acquisition job.
        interval (tuple, optional): Optional (start_date, end_date) to override default time_interval.
    Returns:
        str: A standardized job ID string.
    """
    start_date, end_date = interval if interval else config.time_interval
    start = start_date.strftime('%Y%m%d')
    end = end_date.strftime('%Y%m%d')
    region = config.region.lower().replace(" ", "_")
    base_id = f"{region}__{start}_{end}"
    if hasattr(config, "parent_job_id") and config.parent_job_id:
        return f"{config.parent_job_id}/{base_id}"
    return base_id

def get_job_output_paths(
        config: "DataAcquisitionConfig"
    ) -> dict:
    """
    Return a dictionary of standardised output paths based on the job ID.
    Args:
        config (DataAcquisitionConfig): The configuration object for a data acquisition job.
    Returns:
        dict: A dictionary of output paths keyed by content type.
    """
    base = os.path.join("outputs", config.job_id)
    return {
        "base": base,
        "raw_tiles": os.path.join(base, "raw_tiles"),
        "imagery": os.path.join(base, "imagery"),
        "metadata": os.path.join(base, "metadata"),
        "stitched": os.path.join(base, "stitched"),
    }

def prepare_job_output_dirs(
        config: "DataAcquisitionConfig"
    ) -> dict:
    """
    Prepare the output directories for a job based on its configuration.
    Creates a directory structure for raw tiles, imagery, metadata, and stitched outputs.
    Args:
        config (DataAcquisitionConfig): The configuration object for a data acquisition job.
    Returns:
        dict: A dictionary of output paths keyed by content type.
    """
    lines = []
    paths = get_job_output_paths(config)
    last_key = list(paths)[-1]
    for key, val in paths.items():
        connector = "└──" if key == last_key else "├──"
        lines.append(f"{connector} {val}/")
    log_block(header="📁 Output directory structure:", lines=lines)
    for path in paths.values():
        os.makedirs(path, exist_ok=True)
    return paths

def archive_job_outputs(
        output_dir: str = None,
        label: str = None
    ) -> str:
    """
    Archive the full contents of a job output directory into a zip file.

    Args:
        output_dir (str, optional): Path to the job's base output directory (e.g., outputs/<job_id>).
                                    If None, archives the first job found in outputs/.
        label (str): Optional name override for the archive file (no extension).

    Returns:
        str: Path to the created archive zip file.
    """
    if not output_dir:
        output_base = "outputs"
        jobs = sorted(
            [os.path.join(output_base, d) for d in os.listdir(output_base)
             if os.path.isdir(os.path.join(output_base, d))]
        )
        if not jobs:
            print("❌ No job directories found in outputs/. Cannot archive.")
            exit(1)
        output_dir = jobs[0]
        print(f"ℹ️  No output_dir specified. Defaulting to: {output_dir}")
    else:
        output_dir = os.path.abspath(output_dir)

    if not os.path.exists(output_dir):
        print(f"❌ Job directory '{output_dir}' does not exist.")
        exit(1)

    archive_base = "archive"
    os.makedirs(archive_base, exist_ok=True)

    archive_name = label if label else os.path.basename(output_dir)
    archive_path = os.path.join(archive_base, f"{archive_name}.zip")

    if os.path.exists(archive_path):
        print(f"❌ Archive '{archive_path}' already exists. Use a different label or remove the existing archive.")
        exit(1)

    with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                full_path = os.path.join(root, file)
                arcname = os.path.relpath(full_path, start=output_dir)
                zipf.write(full_path, arcname)
                print(f"✓ Archived {arcname}")

    print(f"\n📦 Archive created: {archive_path}")
    return archive_path

def get_tile_prefix(
        config: "DataAcquisitionConfig", 
        idx: int
    ) -> str:
    """
    Generate a consistent tile-specific prefix using the profile's region and tile index.
    Args:
        config (DataAcquisitionConfig): The data acquisition config with region info.
        idx (int): Index of the tile.
    Returns:
        str: A standardized prefix like 'canterbury_tile0'
    """
    region = config.region.lower().replace(" ", "_")
    return f"{region}_tile{idx}"

def get_orbit_metadata_path(
        paths: dict, 
        tile_prefix: str
    ) -> str:
    """
    Construct the full file path for a tile's orbit metadata JSON.
    Args:
        paths (dict): Dictionary of output paths from prepare_job_output_dirs.
        tile_prefix (str): The tile-specific prefix string.
    Returns:
        str: Full file path to the orbit metadata file.
    """
    return os.path.join(paths["metadata"], f"{tile_prefix}_orbit_metadata.json")

def get_stitched_array_path(
        paths: dict
    ) -> str:
    """
    Construct the full file path for the stitched raw bands .npy output.
    Args:
        paths (dict): Dictionary of output paths from prepare_job_output_dirs.
    Returns:
        str: Full file path to the stitched .npy array.
    """
    return os.path.join(paths["stitched"], "stitched_raw_bands.npy")