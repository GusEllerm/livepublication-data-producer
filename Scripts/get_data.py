import json
from sentinelhub import SHConfig
from profiles import daily_ndvi_canterbury
from evalscripts import discover_evalscript, evalscript_raw_bands

from utils.job_utils import prepare_job_output_dirs
from utils.tile_utils import generate_safe_tiles, download_orbits_for_tiles
from utils.metadata_utils import discover_metadata_for_tiles, select_orbits_for_tiles
from utils.image_utils import stitch_raw_tile_data, generate_ndvi_products, generate_true_color_products


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
tiles = [tiles[0]]  # For testing, only use the first tile

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