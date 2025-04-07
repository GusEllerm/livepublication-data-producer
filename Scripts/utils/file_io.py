import os
import shutil
import rasterio
import numpy as np
from rasterio.transform import from_bounds
from utils.logging_utils import log_warning

def save_geotiff(array, output_path, bbox, crs, dtype=np.float32):
    """
    Save a NumPy array as a GeoTIFF file.
    Args:
        array (np.ndarray): Input array.
        output_path (str): Output file path.
        bbox (list): Bounding box [min_lon, min_lat, max_lon, max_lat].
        crs (rasterio.crs.CRS): Coordinate reference system.
        dtype (str): Data type of the output file.
    """
    if array.ndim == 2:
        height, width = array.shape
        count = 1
        array = array[np.newaxis, ...]
    else:
        height, width, count = array.shape[0], array.shape[1], array.shape[2]
        array = np.moveaxis(array, -1, 0)

    transform = from_bounds(*bbox, width=width, height=height)

    with rasterio.open(
        output_path,
        'w',
        driver='GTiff',
        height=height,
        width=width,
        count=count,
        dtype=dtype,
        crs=crs,
        transform=transform
    ) as dst:
        dst.write(array)

def clean_all_outputs(base_path: str = "."):
    """
    Remove all tiles_* directories and output files in the specified base path.
    Args:
        base_path (str): Base directory to clean. Defaults to current directory.
    """
    import glob

    removed_dirs = 0
    removed_files = 0

    # Remove legacy tiles_* directories
    for folder in glob.glob(os.path.join(base_path, "tiles_*")):
        if os.path.isdir(folder):
            count = sum(len(files) for _, _, files in os.walk(folder))
            shutil.rmtree(folder)
            print(f"🧹 Removed legacy directory: {folder} ({count} files)")
            removed_dirs += 1
            removed_files += count

    # Remove job-based structured output directories
    outputs_path = os.path.join(base_path, "outputs")
    if os.path.isdir(outputs_path):
        for job_dir in os.listdir(outputs_path):
            full_path = os.path.join(outputs_path, job_dir)
            if os.path.isdir(full_path):
                count = sum(len(files) for _, _, files in os.walk(full_path))
                shutil.rmtree(full_path)
                print(f"🧹 Removed job output directory: {full_path} ({count} files)")
                removed_dirs += 1
                removed_files += count

    # Remove standalone output files (.npy, .tif, .png) in base path
    for ext in ("*.npy", "*.tif", "*.png"):
        for f in glob.glob(os.path.join(base_path, ext)):
            os.remove(f)
            print(f"🧼 Removed file: {f}")
            removed_files += 1

    print(f"\n✅ Cleanup complete — {removed_dirs} directories removed, including {removed_files} total files.")


def remove_output_dir(paths: dict):
    job_output_path = paths["base"]
    if os.path.exists(job_output_path):
        shutil.rmtree(job_output_path)
        log_warning(f"Removed job output directory: {job_output_path}")