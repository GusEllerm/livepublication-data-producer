import os
import shutil
from datetime import datetime
from utils.logging_utils import log_step, log_block

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
    Return a dictionary of standardized output paths based on the job ID.
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
        src_dir: str = ".", 
        label: str = None, 
        files_to_archive=None
    ) -> str:
    """
    Archive output files from a directory into a named or timestamped archive folder.
    Args:
        src_dir (str): Directory containing the files to archive.
        label (str): Optional label for the archive folder name.
        files_to_archive (list): List of filenames to archive.
    Returns:
        str: Path to the created archive folder.
    """
    if files_to_archive is None:
        files_to_archive = ["ndvi.tif", "ndvi.png", "true_color.tif", "true_color.png"]

    archive_base = "archive"
    os.makedirs(archive_base, exist_ok=True)

    archive_name = label if label else datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    archive_path = os.path.join(archive_base, archive_name)

    try:
        os.makedirs(archive_path, exist_ok=False)
        print(f"✅ Created archive folder: {archive_path}")
    except FileExistsError:
        print(f"❌ Archive folder '{archive_name}' already exists. Use a different name.")
        exit(1)

    for fname in files_to_archive:
        candidates = [
            os.path.join(src_dir, fname),
            os.path.join(src_dir, "imagery", fname)
        ]
        src_path = next((p for p in candidates if os.path.exists(p)), None)
        if src_path:
            shutil.copy(src_path, archive_path)
            print(f"✓ Archived {src_path}")
        else:
            print(f"⚠️  Warning: {fname} not found in {src_dir} or imagery/, skipping.")

    print(f"\n📦 Archive complete: {archive_path}")
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