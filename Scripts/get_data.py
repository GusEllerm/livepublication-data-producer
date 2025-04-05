import os
import json
import numpy as np
from rasterio.crs import CRS as RioCRS
from sentinelhub import SHConfig, BBox, CRS
from profiles import daily_ndvi_canterbury, discover_evalscript, evalscript_raw_bands

from utils.image_utils import stitch_tiles, compute_ndvi, compute_stitched_bbox, rasterize_true_color, stitch_raw_tile_data, generate_ndvi_products, generate_true_color_products
from utils.metadata_utils import discover_metadata_for_tiles, select_orbits_for_tiles
from utils.tile_utils import generate_safe_tiles, download_orbits_for_tiles, convert_tiles_to_bboxes
from utils.job_utils import get_job_output_paths, prepare_job_output_dirs
from utils.job_utils import get_tile_prefix, get_orbit_metadata_path, get_stitched_array_path
from utils.file_io import save_geotiff
from utils.plotting import plot_image

import matplotlib.pyplot as plt

# === Load config profile ===
profile = daily_ndvi_canterbury

with open("secrets.json") as f:
    secrets = json.load(f)

config = SHConfig()
config.sh_client_id = secrets["sh_client_id"]
config.sh_client_secret = secrets["sh_client_secret"]
config.sh_base_url = secrets["sh_base_url"]
config.sh_token_url = secrets["sh_token_url"]

# === Output directory structure (job-based) ===
paths = prepare_job_output_dirs(profile)

# === create a set of 'safe' tiles (e.g. tiles which conform to API reqs) ===
tiles = generate_safe_tiles(
    profile.bbox,
    resolution=profile.resolution,
    max_dim=2500,
    buffer=0.95 
)
# tiles = [tiles[0]]  # For testing, only use the first tile

tile_metadata = discover_metadata_for_tiles(
    tiles=tiles,
    profile=profile,
    config=config,
    paths=paths,
    evalscript=discover_evalscript
)

selected_orbits = select_orbits_for_tiles(
    metadata_by_tile=tile_metadata,
    strategy=profile.orbit_selection_strategy,
    output_dir=paths["metadata"]
)

tile_info, failed_tiles = download_orbits_for_tiles(
    tiles=tiles,
    selected_orbits=selected_orbits,
    profile=profile,
    config=config,
    evalscript=evalscript_raw_bands,
    paths=paths
)

stitched_image = stitch_raw_tile_data(
    tile_info=tile_info,
    input_dir=paths["raw_tiles"],
    paths=paths
)

generate_ndvi_products(stitched_image, tile_info, paths)
generate_true_color_products(stitched_image, tile_info, paths)