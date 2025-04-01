from __future__ import annotations
import calendar


import os
import cv2  
import rasterio
import shutil
import numpy as np
import matplotlib.pyplot as plt

from typing import Any
from datetime import date
from datetime import datetime, timedelta
from rasterio.transform import from_bounds
from dateutil.relativedelta import relativedelta
from sentinelhub import BBox, CRS, bbox_to_dimensions, SentinelHubRequest, DataCollection, MimeType

def plot_image(
    image: np.ndarray,
    factor: float = 1.0,
    clip_range: tuple[float, float] | None = None,
    save_path: str | None = None,
    **kwargs: Any
) -> None:
    """
    Plot an image with optional clipping and save it to a file.
    Args:
        image (np.ndarray): Image to plot.
        factor (float): Factor to multiply the image by.
        clip_range (tuple): Range to clip the image values.
        save_path (str): Path to save the image.
        **kwargs: Additional arguments for plt.imshow.
    """
    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(15, 15))
    if clip_range is not None:
        ax.imshow(np.clip(image * factor, *clip_range), **kwargs)
    else:
        ax.imshow(image * factor, **kwargs)
    ax.set_xticks([])
    ax.set_yticks([])

    if save_path:
        fig.savefig(save_path, bbox_inches='tight', pad_inches=0)
        plt.close(fig)  # Close the figure to avoid displaying it in notebooks
    else:
        plt.show()


def generate_safe_tiles(aoi, resolution=10, max_dim=2500, buffer=0.95):
    """
    Generate 'safe' tiles for Sentinel Hub API requests.
    Args:
        aoi (list): Area of interest [min_lon, min_lat, max_lon, max_lat].
        resolution (int): Resolution in meters.
        max_dim (int): Maximum dimension of the tile.
        buffer (float): Buffer factor to ensure tiles are safe.
    Returns:
        list: List of BBox objects representing the tiles.
    """
    degrees_per_meter = 1 / 111320
    tile_size_deg = degrees_per_meter * resolution * max_dim * buffer
    min_lon, min_lat, max_lon, max_lat = aoi
    lon_steps = np.arange(min_lon, max_lon, tile_size_deg)
    lat_steps = np.arange(min_lat, max_lat, tile_size_deg)

    tiles = []
    for lon in lon_steps:
        for lat in lat_steps:
            tile = BBox([
                lon, lat,
                min(lon + tile_size_deg, max_lon),
                min(lat + tile_size_deg, max_lat)
            ], crs=CRS.WGS84)
            tiles.append(tile)
    return tiles

def download_safe_tiles(tiles, time_interval, config, evalscript,
                        output_dir="./tiles", prefix="tile"):
    """
    Download Sentinel Hub tiles using the provided evalscript.
    Args:
        tiles (list): List of BBox objects representing the tiles.
        time_interval (tuple): Time interval for the request.
        config (dict): Configuration for Sentinel Hub.
    Returns:
        list: List of tuples containing tile filenames and their bounding boxes.
        list: List of failed tiles.
    """
    os.makedirs(output_dir, exist_ok=True)
    tile_info = []
    failed_tiles = []

    for i, tile in enumerate(tiles):
        size = bbox_to_dimensions(tile, resolution=10)

        request = SentinelHubRequest(
            evalscript=evalscript,
            input_data=[
                SentinelHubRequest.input_data(
                    data_collection=DataCollection.SENTINEL2_L2A.define_from(
                        name="s2l2a", service_url="https://sh.dataspace.copernicus.eu"
                    ),
                    time_interval=time_interval,
                    other_args={"dataFilter": {"mosaickingOrder": "leastCC"}},
                )
            ],
            responses=[SentinelHubRequest.output_response("default", MimeType.TIFF)],
            bbox=tile,
            size=size,
            config=config,
        )

        try:
            data = request.get_data()[0]
            if data is None or np.all(data == 0):
                raise ValueError("Empty or invalid data")
        except Exception as e:
            print(f"⚠️  Failed to get tile {i}: {e}")
            failed_tiles.append((i, tile))
            continue

        npy_path = os.path.join(output_dir, f"{prefix}_{i:03}.npy")
        np.save(npy_path, data)
        tile_info.append((f"{prefix}_{i:03}.npy", tile))
        print(f"✅ Saved {prefix}_{i:03}: shape={data.shape}")

    return tile_info, failed_tiles

def stitch_tiles(tile_dir, tile_coords):
    """
    Stitch tiles together based on their bounding boxes.
    Args:
        tile_dir (str): Directory containing the tile files.
        tile_coords (list): List of tuples containing filenames and bounding boxes.
    Returns:
        np.ndarray: Stitched image array.
    """
    sorted_tiles = sorted(tile_coords, key=lambda t: (-t[1].min_y, t[1].min_x))
    rows = []
    current_row = []
    current_lat = None
    epsilon = 1e-4

    for fname, bbox in sorted_tiles:
        lat = bbox.min_y
        if current_lat is None or abs(lat - current_lat) < epsilon:
            current_row.append(fname)
            current_lat = lat
        else:
            rows.append(current_row)
            current_row = [fname]
            current_lat = lat
    if current_row:
        rows.append(current_row)

    final_rows = []
    for row in rows:
        tile_row = [np.load(os.path.join(tile_dir, f)) for f in row]
        max_height = max(t.shape[0] for t in tile_row)
        padded_row = []
        for tile in tile_row:
            if tile.shape[0] != max_height:
                resized = cv2.resize(tile, (tile.shape[1], max_height), interpolation=cv2.INTER_LINEAR)
            else:
                resized = tile
            padded_row.append(resized)
        final_rows.append(np.concatenate(padded_row, axis=1))
    max_width = max(row.shape[1] for row in final_rows)
    for i in range(len(final_rows)):
        if final_rows[i].shape[1] != max_width:
            final_rows[i] = cv2.resize(final_rows[i], (max_width, final_rows[i].shape[0]), interpolation=cv2.INTER_LINEAR)
    full_image = np.concatenate(final_rows, axis=0)
    return full_image

def compute_ndvi(stitched_array):
    """
    Compute NDVI from the stitched array.
    Args:
        stitched_array (np.ndarray): Stitched image array.
    Returns:
        np.ndarray: NDVI array.
    """
    red = stitched_array[..., 2]
    nir = stitched_array[..., 3]
    ndvi = (nir - red) / (nir + red + 1e-6)
    return np.clip(ndvi, -1, 1)

def rasterize_true_color(stitched_array):
    """
    Rasterize true color from the stitched array.
    Args:
        stitched_array (np.ndarray): Stitched image array.
    Returns:
        np.ndarray: RGB array.
    """
    red = stitched_array[..., 2]
    green = stitched_array[..., 1]
    blue = stitched_array[..., 0]
    rgb = np.stack([red, green, blue], axis=-1)
    return np.clip(rgb * 3.5, 0, 1)

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

def generate_time_intervals(start_date: date, end_date: date, mode: str) -> list[tuple[date, date]]:
    """
    Generate time intervals between start_date and end_date based on the specified mode.
    Args:
        start_date (date): Start date as a date object.
        end_date (date): End date as a date object.
        mode (str): Time series mode, e.g., 'monthly', 'quarterly'.
    Returns:
        list of (start, end) date tuples as date objects.
    """
    intervals = []

    if mode == "monthly":
        current = start_date
        while current <= end_date:
            last_day = calendar.monthrange(current.year, current.month)[1]
            interval_end = date(current.year, current.month, last_day)
            if interval_end > end_date:
                interval_end = end_date
            intervals.append((current, interval_end))
            current = interval_end + timedelta(days=1)

    elif mode == "quarterly":
        current = start_date
        while current <= end_date:
            month = ((current.month - 1) // 3) * 3 + 1
            first_month = date(current.year, month, 1)
            last_month = month + 2
            year = current.year if last_month <= 12 else current.year + 1
            last_month = last_month if last_month <= 12 else last_month - 12
            last_day = calendar.monthrange(year, last_month)[1]
            interval_end = date(year, last_month, last_day)
            if interval_end > end_date:
                interval_end = end_date
            intervals.append((first_month, interval_end))
            current = interval_end + timedelta(days=1)

    else:
        raise ValueError(f"Unsupported time_series_mode: {mode}")

    return intervals

def format_time_interval_prefix(start: date, end: date) -> str:
    """
    Format a string prefix from a time interval.
    Args:
        start (date): Start date as a date object.
        end (date): End date as a date object.
    Returns:
        str: Formatted prefix.
    """
    return f"{start.strftime('%Y%m%d')}__{end.strftime('%Y%m%d')}"

def compute_stitched_bbox(tile_info: list[tuple[str, BBox]]) -> tuple[float, float, float, float]:
    """
    Compute the bounding box from a list of tile bounding boxes.

    Args:
        tile_info (list): List of (filename, BBox) tuples.

    Returns:
        tuple: (min_lon, min_lat, max_lon, max_lat)
    """
    all_bboxes = [bbox for _, bbox in tile_info]
    min_lon = min(b.min_x for b in all_bboxes)
    min_lat = min(b.min_y for b in all_bboxes)
    max_lon = max(b.max_x for b in all_bboxes)
    max_lat = max(b.max_y for b in all_bboxes)
    return (min_lon, min_lat, max_lon, max_lat)

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