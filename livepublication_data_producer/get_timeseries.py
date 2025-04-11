import copy
import json

from sentinelhub import SHConfig

from evalscripts import discover_evalscript, evalscript_raw_bands
from profiles import (
    australian_bushfires,
    bi_weekly_ndvi_test,
    six_months_monthly,
    three_years_quarterly,
    white_island_eruption,
)

from .utils import generate_time_intervals
from .utils.file_io import remove_output_dir
from .utils.image_utils import (
    generate_ndvi_products,
    generate_true_color_products,
    stitch_raw_tile_data,
)
from .utils.job_utils import prepare_job_output_dirs
from .utils.logging_utils import log_warning
from .utils.metadata_utils import (
    discover_metadata_for_tiles,
    discover_orbit_data_metadata,
    has_valid_orbits,
    select_orbits_for_tiles,
)
from .utils.plotting import plot_tile_product_overlay
from .utils.tile_utils import download_orbits_for_tiles, generate_safe_tiles
from .utils.time_interval_utils import create_timeseries_jobs

profile = australian_bushfires
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

    # Generate safe tiles
    tiles = generate_safe_tiles(
        paths=paths,
        aoi=job.bbox,
        resolution=job.resolution
    )
    
    # Discover metadata
    tile_metadata = discover_metadata_for_tiles(
        paths=paths,
        tiles=tiles,
        profile=job,
        config=config,
        evalscript=discover_evalscript
    )

    # Check for valid orbits
    if not has_valid_orbits(tile_metadata):
        # Remove output directory for the job
        remove_output_dir(paths)
        log_warning(f"No valid orbits found for job: {job.job_id}. Skipping job.")
        continue
    
    # Select orbits
    selected_orbits = select_orbits_for_tiles(
        paths=paths,
        metadata_by_tile=tile_metadata,
        profile=job
    )

    product_metadata = discover_orbit_data_metadata(
        paths=paths,
        config=config,
    )

    
    # Download orbits
    tile_info, failed_tiles = download_orbits_for_tiles(
        paths=paths,
        tiles=tiles,
        selected_orbits=selected_orbits,
        profile=job,
        config=config,
        evalscript=evalscript_raw_bands
    )
    
    # Stitch tile data
    stitched_image = stitch_raw_tile_data(
        paths=paths,
        tile_info=tile_info
    )
    
    if stitched_image is not None and tile_info:
        # Generate NDVI and true color products
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
        
        product_overlay = plot_tile_product_overlay(paths)

    else:
        log_warning("Skipping NDVI and true-color generation — no stitched data available.")
