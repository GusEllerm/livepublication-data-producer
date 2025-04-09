import os
import json
from sentinelhub import BBox, CRS, SHConfig
from sentinelhub import SentinelHubRequest, MimeType, DataCollection, bbox_to_dimensions
import numpy as np
from utils.logging_utils import log_step, log_success, log_warning
from utils.job_utils import get_tile_prefix
from utils.logging_utils import log_inline
from utils.metadata_utils import write_workflow_tile_metadata
from datetime import datetime

def generate_safe_tiles(
        paths: dict,
        aoi: BBox, 
        resolution: int = 10, 
        max_dim: int = 2500, 
        buffer: float = 0.95
    ) -> list[BBox]:
    """
    Generate 'safe' tiles for Sentinel Hub API requests.
    Args:
        paths (dict): Dictionary of job output paths.
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
    log_success(f"Generated {len(tiles)} tiles.")
    
    # Persist metadata for transparency
    write_workflow_tile_metadata(paths=paths, tiles=tiles)
    
    return tiles

def download_safe_tiles(
        paths: dict, 
        tiles: list[BBox], 
        time_interval: tuple, 
        prefix: str,
        config: SHConfig, 
        evalscript: str
    ) -> tuple[list[tuple], list[tuple]]:
    """
    Download Sentinel Hub tiles using the provided evalscript.
    Args:
        paths (dict): Dictionary of job output paths.
        tiles (list): List of BBox objects representing the tiles.
        time_interval (tuple): Time interval for the request.
        prefix (str): Prefix for the output filenames.
        config (dict): Configuration for Sentinel Hub.
        evalscript (str): Evalscript to use for downloading imagery.
    Returns:
        list: List of tuples containing tile filenames and their bounding boxes.
        list: List of failed tiles.
    """
    output_dir = paths["raw_tiles"]
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
            print()  # Ensure clean break from inline log
            log_warning(f"⚠️ Failed to download tile {i}: {e}")
            failed_tiles.append((i, tile))
            continue

        npy_path = os.path.join(output_dir, f"{prefix}_{i:03}.npy")
        np.save(npy_path, data)
        tile_info.append((f"{prefix}_{i:03}.npy", tile))

    return tile_info, failed_tiles

def download_orbits_for_tiles(
        paths: dict, 
        tiles: list[BBox], 
        selected_orbits: dict, 
        profile: "DataAcquisitionConfig", 
        config: SHConfig, 
        evalscript: str
    ) -> tuple[list[tuple], list[tuple]]:
    """
    Download imagery for each tile using its selected orbit.
    Args:
        paths (dict): Dictionary of job output paths.
        tiles (list): List of BBox tile geometries.
        selected_orbits (dict): Mapping of tile_prefix -> selected orbit metadata.
        profile: Profile object with region information.
        config: Sentinel Hub config object.
        evalscript (str): Evalscript to use for downloading imagery.
    Returns:
        tuple: (tile_info, failed_tiles)
    """
    if isinstance(tiles[0], tuple):
        from utils.tile_utils import convert_tiles_to_bboxes
        tiles = convert_tiles_to_bboxes(tiles)

    tile_info_all = []
    failed_tiles_all = []

    log_inline(f"⏬ Downloading tiles: 0/{len(tiles)} complete")
    for idx, tile in enumerate(tiles):
        tile_prefix = get_tile_prefix(profile, idx)
        try:
            orbit_data = selected_orbits[tile_prefix]
            orbit_date = orbit_data["orbit_date"]
            time_interval = (orbit_date, orbit_date)
        except KeyError:
            # print()  # Ensure clean break from inline log
            # log_warning(f"⚠️ Skipping tile {tile_prefix} — no selected orbit found.")
            failed_tiles_all.append((idx, tile))
            continue

        tile_info, failed_tiles = download_safe_tiles(
            paths=paths,
            tiles=[tile],
            time_interval=time_interval,
            prefix=tile_prefix,
            config=config,
            evalscript=evalscript
        )

        tile_info_all.extend(tile_info)
        failed_tiles_all.extend(failed_tiles)

        log_inline(f"⏬ Downloading tiles: {len(tile_info_all)}/{len(tiles)} complete")

    if len(failed_tiles_all) == len(tiles):
        print()  # Ensure clean break from inline log
        log_warning(f"All tiles failed for {tile_prefix}. Probably no orbits for day available.")

    return tile_info_all, failed_tiles_all

def convert_tiles_to_bboxes(
        tile_coords_list: list, 
        crs: CRS = CRS.WGS84
    ) -> list:
    """
    Convert a list of tile coordinate tuples to BBox objects.
    Args:
        tile_coords_list (list): List of [min_lon, min_lat, max_lon, max_lat] coordinates.
        crs (CRS): Coordinate reference system. Defaults to WGS84.
    Returns:
        list: List of BBox objects.
    """
    return [BBox(list(coords), crs) for coords in tile_coords_list]