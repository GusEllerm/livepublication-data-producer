import json
import copy
from utils import generate_time_intervals
from utils.time_interval_utils import create_timeseries_jobs

from profiles import weekly_ndvi_test
from evalscripts import discover_evalscript, evalscript_raw_bands
from sentinelhub import SHConfig

from utils.job_utils import generate_job_id, prepare_job_output_dirs
from utils.tile_utils import generate_safe_tiles, download_orbits_for_tiles
from utils.metadata_utils import discover_metadata_for_tiles, select_orbits_for_tiles
from utils.image_utils import stitch_raw_tile_data, generate_ndvi_products, generate_true_color_products

profile = weekly_ndvi_test
start_date, end_date = profile.time_interval

if profile.time_series_mode:
    intervals = generate_time_intervals(profile)
elif profile.time_series_custom_intervals:
    intervals = profile.time_series_custom_intervals
else:
    raise ValueError("Profile must specify a time_series_mode or custom intervals.")

with open("secrets.json") as f:
    secrets = json.load(f)

config = SHConfig()
config.sh_client_id = secrets["sh_client_id"]
config.sh_client_secret = secrets["sh_client_secret"]
config.sh_base_url = secrets["sh_base_url"]
config.sh_token_url = secrets["sh_token_url"]

print(f"📆 Time series configured: {len(intervals)} intervals from {start_date} to {end_date}")

timeseries_jobs = create_timeseries_jobs(profile)

for job in timeseries_jobs:
    print(f"\n⏳ Processing interval: {job.time_interval[0]} to {job.time_interval[1]}")

    # Prepare output directories
    paths = prepare_job_output_dirs(job)

    # === Core workflow steps ===
    tiles = generate_safe_tiles(
        job.bbox, 
        job.resolution
    )
    
    tile_metadata = discover_metadata_for_tiles(
        tiles, 
        job, 
        config, 
        paths, 
        evalscript=discover_evalscript
    )

    selected_orbits = select_orbits_for_tiles(
        metadata_by_tile=tile_metadata, 
        strategy=job.orbit_selection_strategy,
        output_dir=paths["metadata"]
    )
    
    tile_info, failed_tiles = download_orbits_for_tiles(
        tiles, 
        selected_orbits, 
        job, 
        config, 
        paths, 
        evalscript=evalscript_raw_bands
    )
    
    stitched = stitch_raw_tile_data(
        tile_info=tile_info,
        input_dir=paths["raw_tiles"],
        paths=paths 
    )
    
    if stitched is not None and tile_info:
        generate_ndvi_products(stitched, tile_info, paths)
        generate_true_color_products(stitched, tile_info, paths)
    else:
        from utils.logging_utils import log_warning
        log_warning("Skipping NDVI and true-color generation — no stitched data available.")
