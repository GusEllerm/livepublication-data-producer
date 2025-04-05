import os
import shutil
import rasterio
import numpy as np
from rasterio.transform import from_bounds

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

    # Remove all tiles_* directories
    for folder in glob.glob(os.path.join(base_path, "tiles_*")):
        if os.path.isdir(folder):
            shutil.rmtree(folder)
            print(f"🧹 Removed directory: {folder}")
            removed_dirs += 1

    # Remove standalone output files (.npy, .tif, .png)
    for ext in ("*.npy", "*.tif", "*.png"):
        for f in glob.glob(os.path.join(base_path, ext)):
            os.remove(f)
            print(f"🧼 Removed file: {f}")
            removed_files += 1

    print(f"\n✅ Cleanup complete — {removed_dirs} directories and {removed_files} files removed.")