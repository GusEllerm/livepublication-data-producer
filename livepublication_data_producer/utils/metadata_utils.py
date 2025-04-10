import glob
import json
import os
from datetime import date

from pyproj import CRS as pyprojCRS
from pyproj import Transformer
from sentinelhub import (
    CRS,
    BBox,
    DataCollection,
    MimeType,
    SentinelHubCatalog,
    SentinelHubRequest,
    SHConfig,
    bbox_to_dimensions,
)
from shapely.geometry import box, shape
from shapely.ops import transform, unary_union
from utils.job_utils import get_orbit_metadata_path, get_tile_prefix
from utils.logging_utils import log_inline, log_step, log_success, log_warning


def compute_orbit_bbox(orbit: dict) -> box:
    """
    Computes the bounding box that covers all tiles in an orbit.
    Args:
        orbit (dict): Orbit dictionary with tile geometries.
        debug_path (str, optional): Path to write debug JSON file.
    Returns:
        tuple: Bounding box (minx, miny, maxx, maxy) covering all tile geometries.
    """
    orbit_geometries = []

    for tile in orbit.get("tiles", []):
        geometry_data = tile.get("dataGeometry")
        if not geometry_data:
            continue

        geom = shape(geometry_data)
        source_crs = pyprojCRS.from_user_input(geometry_data["crs"]["properties"]["name"])
        target_crs = pyprojCRS.from_epsg(4326)
        transformer = Transformer.from_crs(source_crs, target_crs, always_xy=True)
        geom_wgs84 = transform(transformer.transform, geom)
        orbit_geometries.append(geom_wgs84)

    if not orbit_geometries:
        raise ValueError("No valid geometries found in orbit.")

    return unary_union(orbit_geometries)

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
            metadata["tile_bbox"] = list(tile)  # Inject tile_bbox into metadata
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
        profile: "DataAcquisitionConfig",
        tile_bbox: list
    ) -> dict:
    """
    Select the best orbit from the provided metadata using a specific strategy.
    Args:
        metadata (dict): Orbit metadata dictionary loaded from a metadata.json file.
        profile: The profile object with orbit selection strategy.
        tile_bbox: The bounding box of the tile.
    Returns:
        dict: Selected orbit dictionary.
    """
    orbits = metadata.get("orbits", [])
    strategy = profile.orbit_selection_strategy

    if not orbits:
        raise ValueError("No orbits found in metadata")

    if strategy == "least_cloud":
        def avg_cloud(orbit):
            clouds = [tile.get("cloudCoverage", 100.0) for tile in orbit.get("tiles", [])]
            return sum(clouds) / len(clouds) if clouds else 100.0
        
        def filter_orbits(metadata, tile_bbox):
            """
            Filter orbits based on spatial coverage over the tile.
            Args:
                metadata (dict): Orbit metadata dictionary.
                tile_bbox (list): Tile bounding box coordinates.
            Returns:
                list: Filtered orbits with sufficient spatial coverage.
            """
            filtered_orbits = []
            for orbit in metadata["orbits"]:                
                orbit_geom = compute_orbit_bbox(orbit)

                intersection_area = orbit_geom.intersection(box(*tile_bbox)).area
                percentage_coverage = intersection_area / box(*tile_bbox).area

                # Check if the orbit covers more than 90% of the tile
                if percentage_coverage > 0.9:
                    filtered_orbits.append(orbit)
                
            if not filtered_orbits:
                raise ValueError("No valid orbits with sufficient spatial coverage.")
            return filtered_orbits

        valid_orbits = filter_orbits(metadata, tile_bbox)
        best_orbit = min(valid_orbits, key=avg_cloud)

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
    
    workflow_tile_path = os.path.join(paths["metadata"], "workflow_tile_metadata.json")
    with open(workflow_tile_path, "r") as f:
        tile_bboxes = json.load(f)

    for tile_prefix, metadata in metadata_by_tile.items():
        try:
            normalized_tile_key = tile_prefix.split("_")[-1] if "tile" in tile_prefix else tile_prefix
            tile_bbox = tile_bboxes[normalized_tile_key]["bbox"]
            orbit = select_best_orbit(metadata=metadata, profile=profile, tile_bbox=tile_bbox)
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


def has_valid_orbits(metadata_by_tile: dict) -> bool:
    """
    Check if any tile has valid orbit metadata.
    Args:
        metadata_by_tile (dict): Mapping of tile_prefix -> metadata dict.
    Returns:
        bool: True if any tile has valid orbit metadata, False otherwise.
    """
    return any(
        metadata.get("orbits", []) 
        for metadata in metadata_by_tile.values()
    )

def discover_orbit_data_metadata(paths: dict, config: SHConfig) -> None:
    """
    Discover detailed product metadata for all unique Sentinel products used across all selected orbits.
    Args:
        paths (dict): Output directory structure dictionary.
        config: SentinelHub config object.
    Returns:
        dict: Mapping of product_id -> detailed metadata.
    """
    log_step("🔎 Discovering unique product metadata across all selected orbits...")

    metadata_dir = paths["metadata"]
    orbit_files = glob.glob(os.path.join(metadata_dir, "*_selected_orbit.json"))

    if not orbit_files:
        log_warning("No selected orbit metadata files found.")
        return {}

    catalog = SentinelHubCatalog(config=config)

    seen_product_ids = set()
    product_metadata = {}

    for orbit_file in orbit_files:
        with open(orbit_file, 'r') as f:
            selected_orbit = json.load(f)

        product_ids = selected_orbit.get("product_ids", [])
        for product_id in product_ids:
            if product_id in seen_product_ids:
                continue
            try:
                results = list(catalog.search(collection=DataCollection.SENTINEL2_L2A, ids=[product_id]))
                if results:
                    product_metadata[product_id] = results[0]
                    seen_product_ids.add(product_id)
                    log_inline(f"📥 Retrieved metadata for product: {product_id}")
                    print()  # newline for logging clarity
                else:
                    log_warning(f"No metadata found for product {product_id}")
            except Exception as e:
                log_warning(f"Error fetching metadata for {product_id}: {e}")

    output_path = os.path.join(metadata_dir, "product_metadata.json")
    with open(output_path, 'w') as f:
        json.dump(product_metadata, f, indent=4)

    log_success(f"📦 Saved metadata for {len(product_metadata)} unique products to {output_path}")
    return product_metadata

def write_workflow_tile_metadata(paths: dict, tiles: list[BBox]) -> None:
    """
    Write the bounding boxes of workflow-defined tiles to disk for diagnostics and transparency.

    Args:
        paths (dict): Output directory structure dictionary.
        tiles (list[BBox]): List of BBox tile objects.
    """
    tile_metadata = {
        f"tile{i}": {
            "bbox": list(tile),
            "crs": str(tile.crs)
        }
        for i, tile in enumerate(tiles)
    }

    os.makedirs(paths["metadata"], exist_ok=True)
    output_path = os.path.join(paths["metadata"], "workflow_tile_metadata.json")
    with open(output_path, "w") as f:
        json.dump(tile_metadata, f, indent=2)

    log_success(f"📦 Saved workflow tile metadata to {output_path}")
