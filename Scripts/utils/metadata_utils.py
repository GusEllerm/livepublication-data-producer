import os
import json
from datetime import date
from utils.logging_utils import log_step, log_warning, log_inline
from utils.job_utils import get_tile_prefix, get_orbit_metadata_path
from sentinelhub import BBox, MimeType, SentinelHubRequest, DataCollection, bbox_to_dimensions, CRS, SHConfig

def discover_orbit_metadata(
    paths: dict,
    tile: BBox,
    time_interval: tuple[date, date],
    config: SHConfig,
    evalscript: str,
    prefix: str, 
) -> dict:
    """
    Discover orbit metadata for a given tile and time interval using Mosaicking.ORBIT mode.
    Args:
        paths (dict): Output directory structure dictionary.
        tile (BBox): Tile bounding box to query.
        time_interval (tuple): Tuple of (start_date, end_date).
        config: SentinelHub config object.
        evalscript (str): Evalscript to use for metadata request.
        prefix (str): Prefix for the metadata file.
    Returns:
        dict: Parsed orbit metadata.
    """
    size = bbox_to_dimensions(tile, resolution=10)

    request = SentinelHubRequest(
        evalscript=evalscript,
        input_data=[
            SentinelHubRequest.input_data(
                data_collection=DataCollection.SENTINEL2_L2A.define_from(
                    name="s2l2a", service_url="https://sh.dataspace.copernicus.eu"
                ),
                time_interval=time_interval,
            )
        ],
        responses=[
            SentinelHubRequest.output_response("userdata", MimeType.JSON)
        ],
        bbox=tile,
        size=size,
        config=config
    )

    try:
        response = request.get_data()[0]
        if isinstance(response, dict) and "userdata.json" in response:
            metadata = response["userdata.json"]
        else:
            metadata = response  # Fallback if JSON is returned directly
    except Exception as e:
        log_warning(f"Failed to retrieve orbit metadata: {e}")
        raise

    os.makedirs(paths["metadata"], exist_ok=True)
    metadata_path = os.path.join(paths["metadata"], f"{prefix}_orbit_metadata.json")
    
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=4)

    return metadata

def select_best_orbit(
        metadata: dict, 
        profile: "DataAcquisitionConfig"
    ) -> dict:
    """
    Select the best orbit from the provided metadata using a specific strategy.
    Args:
        metadata (dict): Orbit metadata dictionary loaded from a metadata.json file.
        profile: The profile object with orbit selection strategy.
    Returns:
        dict: Selected orbit dictionary.
    """
    orbits = metadata.get("orbits", [])
    strategy = profile.orbit_selection_strategy

    if not orbits:
        raise ValueError("No orbits found in metadata")

    if strategy == "least_cloud":
        # Compute average cloud coverage for each orbit
        def avg_cloud(orbit):
            clouds = [tile.get("cloudCoverage", 100.0) for tile in orbit.get("tiles", [])]
            return sum(clouds) / len(clouds) if clouds else 100.0

        best_orbit = min(orbits, key=avg_cloud)
        return {
            "strategy": "least_cloud",
            "orbit_date": best_orbit["dateFrom"][:10],
            "product_ids": [tile["productId"] for tile in best_orbit["tiles"]],
            "tile_ids": [tile["tileId"] for tile in best_orbit["tiles"]],
            "cloud_coverage": round(avg_cloud(best_orbit), 2),
            "orbit": best_orbit
        }

    elif strategy in {"nearest_date", "max_coverage", "composite_score"}:
        raise NotImplementedError(f"Strategy '{strategy}' is not implemented yet.")
    else:
        raise ValueError(f"Unknown orbit selection strategy: {strategy}")
    
def write_selected_orbit(
        paths: dict, 
        orbit_data: dict, 
        prefix: str
    ) -> None:
    """
    Write selected orbit information to a JSON file.
    Args:
        paths (dict): Output directory structure dictionary.
        orbit_data (dict): Data for the selected orbit.
        prefix (str): Prefix for the output file name.
    """
    os.makedirs(paths["metadata"], exist_ok=True)
    file_path = os.path.join(paths["metadata"], f"{prefix}_selected_orbit.json")
    with open(file_path, "w") as f:
        json.dump(orbit_data, f, indent=4)

def discover_metadata_for_tiles(
        paths: dict, 
        tiles: list[BBox], 
        profile: "DataAcquisitionConfig", 
        config: SHConfig, 
        evalscript: str
    ) -> dict:
    """
    Discover and load orbit metadata for all tiles in a workflow.

    Args:
        paths (dict): Output directory structure dictionary.
        tiles (list): List of tile coordinates (BBox-like tuples).
        profile: The profile object with region and time_interval.
        config: SentinelHub config object.
        evalscript (str): Evalscript to use for metadata request.
    Returns:
        dict: Mapping of tile_prefix -> parsed orbit metadata.
    """
    log_step("🔎 Discovering orbit metadata for tiles...")
    metadata_by_tile = {}
    log_inline(f"📡 Discovering metadata: 0/{len(tiles)} tiles complete")
    for idx, tile_coords in enumerate(tiles):
        tile = BBox(list(tile_coords), CRS.WGS84)
        tile_prefix = get_tile_prefix(profile, idx)

        discover_orbit_metadata(
            tile=tile,
            time_interval=profile.time_interval,
            config=config,
            evalscript=evalscript,
            paths=paths,
            prefix=tile_prefix,
        )

        metadata_path = get_orbit_metadata_path(paths, tile_prefix)
        with open(metadata_path, 'r') as f:
            metadata_by_tile[tile_prefix] = json.load(f)

        log_inline(f"📡 Discovering metadata: {idx + 1}/{len(tiles)} tiles complete")

    print() # for newline after inline logging
    return metadata_by_tile

def select_orbits_for_tiles(
        paths: dict,
        metadata_by_tile: dict, 
        profile: "DataAcquisitionConfig"
    ) -> dict:
    """
    Select the best orbit for each tile's metadata and write results to file.
    Args:
        paths (dict): Output directory structure dictionary.
        metadata_by_tile (dict): Mapping of tile_prefix -> metadata dict.
        profile: The profile object with region and time_interval.
    Returns:
        dict: Mapping of tile_prefix -> selected orbit data.
    """

    log_step(f"🔎 Selecting best orbits using strategy: {profile.orbit_selection_strategy}")
    selected_orbits = {}
    failures = []

    log_inline(f"🎯 Selecting orbits: 0/{len(metadata_by_tile)} tiles complete")
    for tile_prefix, metadata in metadata_by_tile.items():
        try:
            orbit = select_best_orbit(metadata=metadata, profile=profile)
            write_selected_orbit(paths=paths, orbit_data=orbit, prefix=tile_prefix)
            selected_orbits[tile_prefix] = orbit
            log_inline(f"🎯 Selected orbits: {len(selected_orbits)}/{len(metadata_by_tile)} complete")
        except Exception as e:
            failures.append((tile_prefix, str(e)))

    print() # for newline after inline logging

    if failures:
        error_messages = [msg for _, msg in failures]
        unique_errors = set(error_messages)
        if len(unique_errors) == 1:
            log_warning(f"{list(unique_errors)[0]} for {len(failures)} tiles. Orbit selection skipped.")
        else:
            for tile_prefix, msg in failures:
                log_warning(f"Failed to select orbit for {tile_prefix}: {msg}")

    return selected_orbits