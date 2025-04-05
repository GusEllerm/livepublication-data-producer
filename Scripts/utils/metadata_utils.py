import os
import json
from datetime import date
from sentinelhub import BBox, MimeType, SentinelHubRequest, DataCollection, bbox_to_dimensions

def discover_orbit_metadata(
    tile: BBox,
    time_interval: tuple[date, date],
    config,
    evalscript: str,
    output_dir: str,
    prefix: str, 
    ) -> dict:
    """
    Discover orbit metadata for a given tile and time interval using Mosaicking.ORBIT mode.
    
    Args:
        tile (BBox): Tile bounding box to query.
        time_interval (tuple): Tuple of (start_date, end_date).
        config: SentinelHub config object.
        output_dir (str): Path to save orbit metadata JSON file.
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
        print(f"⚠️  Failed to retrieve orbit metadata: {e}")
        raise

    os.makedirs(output_dir, exist_ok=True)
    metadata_path = os.path.join(output_dir, f"{prefix}_orbit_metadata.json")
    
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=4)

    print(f"✅ Orbit metadata saved to: {metadata_path}")
    return metadata

def select_best_orbit(metadata: dict, strategy: str = "least_cloud") -> dict:
    """
    Select the best orbit from the provided metadata using a specific strategy.

    Args:
        metadata (dict): Orbit metadata dictionary loaded from a metadata.json file.
        strategy (str): Strategy name to use for selection.

    Returns:
        dict: Selected orbit dictionary.

    Raises:
        ValueError: If strategy is unknown or metadata is malformed.
    """
    orbits = metadata.get("orbits", [])
    if not orbits:
        raise ValueError("No orbits found in metadata.")

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
    

def write_selected_orbit(orbit_data: dict, output_dir: str, prefix: str):
    """
    Write selected orbit information to a JSON file.
    Args:
        orbit_data (dict): Data for the selected orbit.
        output_dir (str): Directory where the JSON will be saved.
        prefix (str): Prefix for the output file name.
    """
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, f"{prefix}_selected_orbit.json")
    with open(file_path, "w") as f:
        json.dump(orbit_data, f, indent=4)
    print(f"✅ Selected orbit saved to: {file_path}")

  