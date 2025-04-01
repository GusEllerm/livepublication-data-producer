import json
import os
from datetime import date
from utils import (
    generate_time_intervals,
    format_time_interval_prefix,
    generate_safe_tiles,
    download_safe_tiles,
    stitch_tiles,
    compute_ndvi,
    rasterize_true_color,
    save_geotiff,
    plot_image,
    compute_stitched_bbox
)
from profiles import test_timeseries_profile, evalscript_raw_bands
from sentinelhub import SHConfig, CRS
from rasterio.crs import CRS as RioCRS

with open("secrets.json") as f:
    secrets = json.load(f)

# === Load profile ===
profile = test_timeseries_profile
start_date, end_date = profile.time_interval

if profile.time_series_mode:
    intervals = generate_time_intervals(start_date, end_date, profile.time_series_mode)
elif profile.time_series_custom_intervals:
    intervals = profile.time_series_custom_intervals
else:
    raise ValueError("Profile must specify a time_series_mode or custom intervals.")

print(f"📆 Time series configured: {len(intervals)} intervals from {start_date} to {end_date}")

config = SHConfig()
config.sh_client_id = secrets["sh_client_id"]
config.sh_client_secret = secrets["sh_client_secret"]
config.sh_base_url = secrets["sh_base_url"]
config.sh_token_url = secrets["sh_token_url"]

# === Output base directory ===
base_output_dir = f"./tiles_{profile.region.lower().replace(' ', '_')}"
os.makedirs(base_output_dir, exist_ok=True)

# === New implementation for time series processing ===
if profile.time_series_mode or profile.time_series_custom_intervals:
    for start, end in intervals:
        time_prefix = format_time_interval_prefix(start, end)
        output_dir = os.path.join(base_output_dir, time_prefix)
        os.makedirs(output_dir, exist_ok=True)

        # === Create a set of 'safe' tiles (e.g. tiles which conform to API reqs) ===
        tiles = generate_safe_tiles(
            profile.bbox, 
            resolution=profile.resolution,
            max_dim=2500,
            buffer=0.95 if not profile.tile_size_deg else 1.0)
        
        print(f"⚙️  Generated {len(tiles)} tiles for interval {time_prefix}.")
        print(f"⬇️  Downloading {len(tiles)} tiles for interval {time_prefix} ({start} to {end})...")

        # === Download raw band files for tiles ===
        tile_info, failed = download_safe_tiles(
            tiles=tiles,
            time_interval=(start, end),
            config=config,
            evalscript=evalscript_raw_bands,
            output_dir=output_dir,
            prefix=time_prefix
        )

        print(f"📦 Downloaded {len(tile_info)} tiles; {len(failed)} failed.")

        if not tile_info:
            print(f"❌ No tiles downloaded for {time_prefix}")
            continue

        stitched_image = stitch_tiles(output_dir, tile_info)
        ndvi = compute_ndvi(stitched_image)
        rgb = rasterize_true_color(stitched_image)

        bbox = compute_stitched_bbox(tile_info)
        crs = RioCRS.from_epsg(4326)

        save_geotiff(ndvi, os.path.join(output_dir, "ndvi.tif"), bbox, crs)
        save_geotiff(rgb, os.path.join(output_dir, "true_color.tif"), bbox, crs)
        print(f"✅ Completed processing for interval {time_prefix}. NDVI and true color outputs saved to: {output_dir}")
