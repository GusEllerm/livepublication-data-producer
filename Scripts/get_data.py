import os
import json
import numpy as np
from rasterio.crs import CRS as RioCRS
from sentinelhub import SHConfig, BBox, CRS
from profiles import daily_ndvi_canterbury, discover_evalscript, evalscript_raw_bands
from utils import generate_safe_tiles, discover_orbit_metadata, select_best_orbit, write_selected_orbit, download_selected_orbits
from utils import stitch_tiles, compute_stitched_bbox, compute_ndvi, plot_image, rasterize_true_color, save_geotiff
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

# === Output directory ===
output_dir = f"./tiles_{profile.region.lower().replace(' ', '_')}"
prefix = profile.region.lower().replace(' ', '_')
os.makedirs(output_dir, exist_ok=True)

# === create a set of 'safe' tiles (e.g. tiles which conform to API reqs) ===
tiles = generate_safe_tiles(
    profile.bbox,
    resolution=profile.resolution,
    max_dim=2500,
    buffer=0.95 
)
print(f"⚙️  Generated {len(tiles)} tiles.")
# tiles = [tiles[0]]  # For testing, only use the first tile

for idx, tile_coords in enumerate(tiles):
    tile = BBox(list(tile_coords), CRS.WGS84)
    tile_prefix = f"{prefix}_tile{idx}"

    # === Discover orbit metadata ===
    print(f"🔍 Discovering orbit metadata for tile {idx}...")
    discover_orbit_metadata(
        tile=tile,
        time_interval=profile.time_interval,
        config=config,
        evalscript=discover_evalscript,
        output_dir=output_dir,
        prefix=tile_prefix,
    )
    metadata_path = os.path.join(output_dir, f"{tile_prefix}_orbit_metadata.json")
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)

#     # === Select the best orbit ===
#     print(f"🔍 Selecting the best orbit for tile {idx}...")
#     best_orbit = select_best_orbit(metadata, strategy=profile.orbit_selection_strategy)
#     print(f"✅ Orbit optimised for {best_orbit['strategy']} and has orbit date {best_orbit['orbit_date']}")
#     write_selected_orbit(best_orbit, output_dir=output_dir, prefix=tile_prefix)

# print("⏬ Downloading selected orbits for all tiles...")
# tile_bboxes = [BBox(list(tile_coords), CRS.WGS84) for tile_coords in tiles]
# tile_info, failed_tiles = download_selected_orbits(
#     tiles=tile_bboxes,
#     profile=profile,
#     config=config,
#     evalscript=evalscript_raw_bands,
#     output_dir_base="./tiles"
# )
# print(f"✅ Download complete: {len(tile_info)} succeeded, {len(failed_tiles)} failed.")

# if tile_info:
#     print("🧵 Stitching tiles...")
#     stitched_image = stitch_tiles(output_dir, tile_info)
#     stitched_path = os.path.join(output_dir, "stitched_raw_bands.npy")
#     np.save(stitched_path, stitched_image)
#     print(f"✅ Stitched image saved to {stitched_path}")

#     print("🌿 Computing NDVI...")
#     ndvi = compute_ndvi(stitched_image)
#     plot_image(ndvi, title="NDVI", cmap="RdYlGn", save_path=os.path.join(output_dir, "ndvi.png"))
#     ndvi_path = os.path.join(output_dir, "ndvi.tif")
#     save_geotiff(
#         ndvi,
#         ndvi_path,
#         compute_stitched_bbox(tile_info),
#         RioCRS.from_epsg(4326)
#     )
#     print(f"✅ NDVI GeoTIFF saved to {ndvi_path}")

#     print("🎨 Rendering true color composite...")
#     rgb = rasterize_true_color(stitched_image)
#     plot_image(rgb, title="True Color Composite", save_path=os.path.join(output_dir, "true_color.png"))
#     rgb_path = os.path.join(output_dir, "true_color.tif")
#     save_geotiff(
#         rgb,
#         rgb_path,
#         compute_stitched_bbox(tile_info),
#         RioCRS.from_epsg(4326)
#     )
#     print(f"✅ True color GeoTIFF saved to {rgb_path}")
# else:
#     print("⚠️ No tiles available to stitch or process.")