import json
from sentinelhub import SHConfig
from profiles import daily_ndvi_canterbury, viti_levu_ndvi
from evalscripts import discover_evalscript, evalscript_raw_bands

from utils.job_utils import prepare_job_output_dirs
from utils.plotting import plot_tile_product_overlay
from utils.tile_utils import generate_safe_tiles, download_orbits_for_tiles
from utils.metadata_utils import discover_metadata_for_tiles, select_orbits_for_tiles, discover_orbit_data_metadata
from utils.image_utils import stitch_raw_tile_data, generate_ndvi_products, generate_true_color_products, validate_image_coverage_with_tile_footprints

# === Load config profile ===
profile = daily_ndvi_canterbury

with open("secrets.json") as f:
    secrets = json.load(f)

config = SHConfig()
config.sh_client_id = secrets["sh_client_id"]
config.sh_client_secret = secrets["sh_client_secret"]
config.sh_base_url = secrets["sh_base_url"]
config.sh_token_url = secrets["sh_token_url"]

# validate_image_coverage_with_tile_footprints(
#     stitched_image_path="/Users/eller/Projects/Geo_LivePub/Scripts/outputs/australian_bushfires__20191001_20200531/australian_bushfires__20191001_20191031/imagery/true_color.tif",
#     selected_orbit_path="/Users/eller/Projects/Geo_LivePub/Scripts/outputs/australian_bushfires__20191001_20200531/australian_bushfires__20191001_20191031/metadata/australian_bushfires_tile0_selected_orbit.json",
# )

# === Output directory structure (job-based) ===
paths = prepare_job_output_dirs(profile)

# === create a set of 'safe' tiles (e.g. tiles which conform to API reqs) ===
tiles = generate_safe_tiles(
    paths=paths,
    aoi=profile.bbox,  
    resolution=profile.resolution
)

tile_metadata = discover_metadata_for_tiles(
    paths=paths,
    tiles=tiles,
    profile=profile,
    config=config,
    evalscript=discover_evalscript
)

selected_orbits = select_orbits_for_tiles(
    paths=paths,
    metadata_by_tile=tile_metadata,
    profile=profile,
)

product_metadata = discover_orbit_data_metadata(
    paths=paths,
    config=config,
)

tile_info, failed_tiles = download_orbits_for_tiles(
    paths=paths,
    tiles=tiles,
    selected_orbits=selected_orbits,
    profile=profile,
    config=config,
    evalscript=evalscript_raw_bands,
)

stitched_image = stitch_raw_tile_data(
    paths=paths,
    tile_info=tile_info,
)

generate_ndvi_products(
    paths=paths,
    tile_info=tile_info,
    stitched_image=stitched_image
)

generate_true_color_products(
    paths=paths,
    tile_info=tile_info,
    stitched_image=stitched_image
)

# === Diagnostic overlay showing which product contributed to which tile ===
overlay_path = plot_tile_product_overlay(paths)
