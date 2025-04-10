import json
import os

import cv2
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from pyproj import CRS, Transformer
from rasterio.crs import CRS as RioCRS
from rasterio.plot import show
from sentinelhub import BBox
from shapely.geometry import Polygon

from .file_io import save_geotiff
from .job_utils import get_stitched_array_path
from .logging_utils import log_step, log_success
from .plotting import plot_image


def stitch_tiles(
        tile_dir: str, 
        tile_coords: list[tuple[str, BBox]]
    ) -> np.ndarray:
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

def compute_stitched_bbox(
        tile_info: list[tuple[str, BBox]]
    ) -> tuple[float, float, float, float]:
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

def compute_ndvi(
        stitched_array
    ) -> np.ndarray:
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

def rasterize_true_color(
        stitched_array
    ) -> np.ndarray:
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

def stitch_raw_tile_data(
        paths: dict,
        tile_info: list[tuple[str, BBox]], 
    ) -> np.ndarray:
    """
    Stitch raw tile arrays into a single image and save to disk.
    Args:
        tile_info (list): List of (filename, BBox) tuples.
        paths (dict, optional): Output directory structure used to determine default path if `output_path` is not provided.
    Returns:
        np.ndarray: The stitched image array.
    """
    from utils.logging_utils import log_warning
    try:
        if not tile_info:
            raise ValueError("No tiles available to stitch or process.")

        if paths is None:
            raise ValueError("Paths dictionary is required to save the stitched image.")
        output_path = get_stitched_array_path(paths)

        print() # for newline after inline logging
        log_step("🧵 Stitching tiles...")
        stitched_array = stitch_tiles(paths["raw_tiles"], tile_info)
        np.save(output_path, stitched_array)
        log_success(f"Stitched tiles saved to {output_path}")
        return stitched_array

    except Exception as e:
        log_warning(f"Stitching skipped: {e}")
        return None

def generate_ndvi_products(
        paths: dict,
        tile_info: list[tuple[str, BBox]],
        stitched_image: np.ndarray
    ) -> None:
    """
    Compute and save NDVI imagery as PNG and GeoTIFF.
    Args:
        paths (dict): Dictionary of output directory paths.
        tile_info (list): List of (filename, BBox) tuples.
        stitched_image (np.ndarray): Stitched satellite image.
    """
    if stitched_image is None or tile_info is None or len(tile_info) == 0:
        from utils.logging_utils import log_warning
        log_warning("⚠️ Skipping NDVI generation: no stitched image or tile info provided.")
        return
    log_step("🧪 Generating NDVI imagery...")
    ndvi = compute_ndvi(stitched_image)

    scl = stitched_image[..., -1].astype(np.uint8)
    cloud_mask = np.isin(scl, [3, 8, 9, 10])  # cloud shadows, medium/high clouds, cirrus
    ndvi_masked = np.where(cloud_mask, np.nan, ndvi)

    mask_preview_path = os.path.join(paths["imagery"], "ndvi_cloud_mask.png")
    plot_image(image=cloud_mask.astype(np.uint8), cmap="gray", save_path=mask_preview_path)

    ndvi_png_path = os.path.join(paths["imagery"], "ndvi.png")
    plot_image(image=ndvi_masked, cmap="RdYlGn", save_path=ndvi_png_path)

    ndvi_tif_path = os.path.join(paths["imagery"], "ndvi.tif")
    bbox = compute_stitched_bbox(tile_info)
    save_geotiff(ndvi_masked, ndvi_tif_path, bbox, RioCRS.from_epsg(4326))

    log_success("NDVI imagery saved.")

def generate_true_color_products(
        paths: dict,
        tile_info: list[tuple[str, BBox]], 
        stitched_image: np.ndarray
    ) -> None:
    """
    Compute and save true-color composite imagery as PNG and GeoTIFF.
    Args:
        paths (dict): Dictionary of output directory paths.
        tile_info (list): List of (filename, BBox) tuples.
        stitched_image (np.ndarray): Stitched satellite image.
    """
    if stitched_image is None or tile_info is None or len(tile_info) == 0:
        from utils.logging_utils import log_warning
        log_warning("⚠️ Skipping true-color generation: no stitched image or tile info provided.")
        return
    log_step("🎨 Generating true-color imagery...")
    rgb = rasterize_true_color(stitched_image)

    rgb_png_path = os.path.join(paths["imagery"], "true_color.png")
    plot_image(rgb, save_path=rgb_png_path)

    rgb_tif_path = os.path.join(paths["imagery"], "true_color.tif")
    bbox = compute_stitched_bbox(tile_info)
    save_geotiff(rgb, rgb_tif_path, bbox, RioCRS.from_epsg(4326))

    log_success("True-color imagery saved.")

def validate_image_coverage_with_tile_footprints(
    stitched_image_path: str,
    selected_orbit_path: str,
    output_path: str | None = None
) -> None:
    """
    Validates stitched image coverage against the contributing tile dataEnvelopes.
    Overlays tile footprints onto the true-color image and optionally saves a diagnostic PNG.
    Args:
        stitched_image_path (str): Path to the stitched GeoTIFF image (e.g. true_color.tif).
        selected_orbit_path (str): Path to the *_selected_orbit.json file containing dataEnvelope info.
        output_path (str | None): Optional path to save the output PNG. If None, the figure will be shown.
    """
    with rasterio.open(stitched_image_path) as src:
        image = src.read([1, 2, 3])  # RGB bands
        image_crs = src.crs
        fig, ax = plt.subplots(figsize=(10, 10))
        show(image, transform=src.transform, ax=ax)

        with open(selected_orbit_path, "r") as f:
            orbit_data = json.load(f)

        for i, tile in enumerate(orbit_data.get("orbit", {}).get("tiles", [])):
            coords = tile["dataEnvelope"]["coordinates"][0]
            tile_crs_str = tile["dataEnvelope"]["crs"]["properties"]["name"]
            tile_crs = CRS.from_user_input(tile_crs_str)

            print("Tile CRS:", tile_crs)
            print("Image CRS:", image_crs)
            transformer = Transformer.from_crs(tile_crs, image_crs, always_xy=True)
            transformed_coords = [transformer.transform(x, y) for x, y in coords]
            poly = Polygon(transformed_coords)
            x, y = poly.exterior.xy
            ax.plot(x, y, color='red', linewidth=2, label='Tile' if i == 0 else "")

            print("Raw tile coords:", coords)
            print("Transformed coords:", transformed_coords)

        ax.set_title("Stitched Image with Tile Footprints")
        ax.legend()

        if output_path:
            fig.savefig(output_path, bbox_inches='tight', pad_inches=0)
            plt.close(fig)
        else:
            plt.show()
