import os
import cv2
import numpy as np
from sentinelhub import BBox

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
