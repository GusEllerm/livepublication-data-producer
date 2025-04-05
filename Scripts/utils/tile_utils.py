import os
import json
from sentinelhub import BBox, CRS
from sentinelhub import SentinelHubRequest, MimeType, DataCollection, bbox_to_dimensions
import numpy as np

def generate_safe_tiles(aoi, resolution=10, max_dim=2500, buffer=0.95):
    """
    Generate 'safe' tiles for Sentinel Hub API requests.
    Args:
        aoi (list): Area of interest [min_lon, min_lat, max_lon, max_lat].
        resolution (int): Resolution in meters.
        max_dim (int): Maximum dimension of the tile.
        buffer (float): Buffer factor to ensure tiles are safe.
    Returns:
        list: List of BBox objects representing the tiles.
    """
    degrees_per_meter = 1 / 111320
    tile_size_deg = degrees_per_meter * resolution * max_dim * buffer
    min_lon, min_lat, max_lon, max_lat = aoi
    lon_steps = np.arange(min_lon, max_lon, tile_size_deg)
    lat_steps = np.arange(min_lat, max_lat, tile_size_deg)

    tiles = []
    for lon in lon_steps:
        for lat in lat_steps:
            tile = BBox([
                lon, lat,
                min(lon + tile_size_deg, max_lon),
                min(lat + tile_size_deg, max_lat)
            ], crs=CRS.WGS84)
            tiles.append(tile)
    return tiles

def download_safe_tiles(tiles, time_interval, config, evalscript,
                        output_dir="./tiles", prefix="tile"):
    """
    Download Sentinel Hub tiles using the provided evalscript.
    Args:
        tiles (list): List of BBox objects representing the tiles.
        time_interval (tuple): Time interval for the request.
        config (dict): Configuration for Sentinel Hub.
    Returns:
        list: List of tuples containing tile filenames and their bounding boxes.
        list: List of failed tiles.
    """
    os.makedirs(output_dir, exist_ok=True)
    tile_info = []
    failed_tiles = []

    for i, tile in enumerate(tiles):
        size = bbox_to_dimensions(tile, resolution=10)

        request = SentinelHubRequest(
            evalscript=evalscript,
            input_data=[
                SentinelHubRequest.input_data(
                    data_collection=DataCollection.SENTINEL2_L2A.define_from(
                        name="s2l2a", service_url="https://sh.dataspace.copernicus.eu"
                    ),
                    time_interval=time_interval,
                    other_args={"dataFilter": {"mosaickingOrder": "leastCC"}},
                )
            ],
            responses=[SentinelHubRequest.output_response("default", MimeType.TIFF)],
            bbox=tile,
            size=size,
            config=config,
        )

        try:
            data = request.get_data()[0]
            if data is None or np.all(data == 0):
                raise ValueError("Empty or invalid data")
        except Exception as e:
            print(f"⚠️  Failed to get tile {i}: {e}")
            failed_tiles.append((i, tile))
            continue

        npy_path = os.path.join(output_dir, f"{prefix}_{i:03}.npy")
        np.save(npy_path, data)
        tile_info.append((f"{prefix}_{i:03}.npy", tile))
        print(f"✅ Saved {prefix}_{i:03}: shape={data.shape}")

    return tile_info, failed_tiles

def download_selected_orbits(
    tiles: list[BBox],
    profile,
    config,
    evalscript: str,
    paths: dict
):
    """
    Download Sentinel Hub tiles using pre-selected orbits for each sub-bbox tile.

    Args:
        tiles (list): List of BBox tile geometries.
        profile: Profile object containing region and strategy info.
        config: Sentinel Hub config object.
        evalscript (str): Evalscript to use for downloading imagery.
        paths (dict): Dictionary of job paths.
    
    Returns:
        list: List of tuples containing tile filenames and their bounding boxes.
        list: List of failed tiles.
    """
    tile_info_all = []
    failed_tiles_all = []

    for idx, tile in enumerate(tiles):
        prefix = f"{profile.region.lower().replace(' ', '_')}_tile{idx}"
        orbit_json_path = os.path.join(paths["metadata"], f"{prefix}_selected_orbit.json")

        try:
            with open(orbit_json_path, "r") as f:
                orbit_data = json.load(f)
            orbit_date = orbit_data["orbit_date"]
        except Exception as e:
            print(f"⚠️  Skipping tile {idx} — could not load orbit metadata: {e}")
            failed_tiles_all.append((idx, tile))
            continue

        time_interval = (orbit_date, orbit_date)
        tile_info, failed_tiles = download_safe_tiles(
            tiles=[tile],
            time_interval=time_interval,
            config=config,
            evalscript=evalscript,
            output_dir=paths["raw_tiles"],
            prefix=prefix
        )

        tile_info_all.extend(tile_info)
        failed_tiles_all.extend(failed_tiles)

    return tile_info_all, failed_tiles_all