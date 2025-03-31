import os
import numpy as np
import json

with open("secrets.json") as f:
    secrets = json.load(f)

from rasterio.crs import CRS as RioCRS
from sentinelhub import SHConfig, BBox, CRS, bbox_to_dimensions, SentinelHubCatalog, DataCollection, SentinelHubRequest, MimeType
from utils import plot_image, generate_safe_tiles, download_safe_tiles, stitch_tiles, compute_ndvi, rasterize_true_color, save_geotiff, clean_output_dir
from profiles import rgb_snapshot_quickview, vegetation_monitoring_monthly, ndvi_high_precision, evalscript_raw_bands, lilys_profile

# === Load config profile ===
profile = vegetation_monitoring_monthly

# example change
config = SHConfig()
config.sh_client_id = secrets["sh_client_id"]
config.sh_client_secret = secrets["sh_client_secret"]
config.sh_base_url = secrets["sh_base_url"]
config.sh_token_url = secrets["sh_token_url"]

# === Output directory ===
output_dir = f"./tiles_{profile.region.lower().replace(' ', '_')}"
clean_output_dir(output_dir) # !!!!!!!!! removes files from output_dir !!!!!!!!!
prefix = profile.region.lower().replace(' ', '_')
os.makedirs(output_dir, exist_ok=True)

# === create a set of 'safe' tiles (e.g. tiles which conform to API reqs) ===
tiles = generate_safe_tiles(
    profile.bbox,
    resolution=profile.resolution,
    max_dim=2500,
    buffer=0.95 if not profile.tile_size_deg else 1.0
)
print(f"⚙️  Generated {len(tiles)} tiles.")

# === Donwload raw band files for tiles ===
tile_info, failed_tiles = download_safe_tiles(
    tiles=tiles,
    time_interval=profile.time_interval,
    config=config,
    evalscript=evalscript_raw_bands,
    output_dir=output_dir,
    prefix=prefix
)

if not tile_info:
    print("❌ No tiles were successfully downloaded. Aborting.")
    exit(1)
if failed_tiles:
    print(f"⚠️ Warning: {len(failed_tiles)} out of {len(tiles)} tiles failed.")
    for idx, bbox in failed_tiles:
        print(f"   - Failed tile {idx}: {bbox}")

# === Stitch tiles together ===
stitched_image = stitch_tiles(output_dir, tile_info)
np.save(os.path.join(output_dir, "stitched_raw_bands.npy"), stitched_image)
print(f"✅ Stitched raw band matrix saved: shape={stitched_image.shape}")

all_bboxes = [bbox for _, bbox in tile_info]
min_lon = min(b.min_x for b in all_bboxes)
min_lat = min(b.min_y for b in all_bboxes)
max_lon = max(b.max_x for b in all_bboxes)
max_lat = max(b.max_y for b in all_bboxes)
stitched_bbox = (min_lon, min_lat, max_lon, max_lat)
from rasterio.crs import CRS as RioCRS
stitched_crs = RioCRS.from_epsg(4326)

# === Postprocessing ===
# NDVI example
ndvi = compute_ndvi(stitched_image)
np.save(os.path.join(output_dir, "ndvi.npy"), ndvi)
plot_image(
    ndvi,
    factor=1.0,
    clip_range=(-1, 1),
    save_path=os.path.join(output_dir, "ndvi.png")
)
save_geotiff(
    ndvi,
    os.path.join(output_dir, "ndvi.tif"),
    stitched_bbox,
    stitched_crs
)
print("✅ NDVI computed and saved.")

# Rasterise true color
rgb = rasterize_true_color(stitched_image)
plot_image(
    rgb,
    factor=1.0,
    clip_range=(0, 1),
    save_path=os.path.join(output_dir, "true_color.png")
)
save_geotiff(
    rgb,
    os.path.join(output_dir, "true_color.tif"),
    stitched_bbox,
    stitched_crs
)
print("✅ True color image rendered and saved.")