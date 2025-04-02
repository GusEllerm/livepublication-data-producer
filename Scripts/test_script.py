from sentinelhub import SentinelHubRequest, MimeType, CRS, BBox, DataCollection, SHConfig

import json
with open("secrets.json") as f:
    secrets = json.load(f)

config = SHConfig()
config.sh_client_id = secrets["sh_client_id"]
config.sh_client_secret = secrets["sh_client_secret"]
config.sh_base_url = secrets["sh_base_url"]
config.sh_token_url = secrets["sh_token_url"]

data_collection = DataCollection.SENTINEL2_L2A.define_from(
    name="s2l2a-cdse",
    service_url="https://sh.dataspace.copernicus.eu"
)

bbox = BBox([13.822174, 45.850803, 14.559345, 46.291917], crs=CRS.WGS84)  # Small region in Slovenia
time_interval = ('2022-06-01', '2022-06-10')
evalscript = """//VERSION=3
function setup() {
  return {
    input: ["B04", "B08"],
    output: { bands: 2 }
  };
}
function evaluatePixel(sample) {
  return [sample.B04, sample.B08];
}"""

request = SentinelHubRequest(
    evalscript=evalscript,
    input_data=[
        SentinelHubRequest.input_data(
            data_collection=data_collection,
            time_interval=time_interval,
            other_args={"dataFilter": {"mosaickingOrder": "leastCC"}}
        )
    ],
    responses=[SentinelHubRequest.output_response("default", MimeType.TIFF)],
    bbox=bbox,
    size=(100, 100),
    config=config,
    data_folder="./debug_tile"
)

response = request.get_data(save_data=True)

for item in request.download_list:
    meta = {
        "url": item.url,
        "headers": item.headers,
        "request_type": item.request_type.value,
        "data_type": item.data_type.value,
        "payload": item.post_values,
        "save_path": item.filename or "N/A",
        "folder": item.data_folder
    }
    
    # Write to JSON file
    with open("debug_tile/tile_metadata.json", "w") as f:
        json.dump(meta, f, indent=2)