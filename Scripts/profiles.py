from dataclasses import dataclass
from typing import Tuple

@dataclass
class DataAcquisitionConfig:
    region: str
    bbox: list  # [min_lon, min_lat, max_lon, max_lat]
    time_interval: Tuple[str, str]
    temporal_granularity: str  # 'monthly', 'weekly', etc.
    cloud_cover_threshold: int  # %
    mosaicking_order: str       # 'leastCC', 'mostRecent', etc.
    acquisition_strategy: str   # 'same_day_all_tiles', 'best_per_tile'
    resolution: int             # in meters
    index_type: str             # 'NDVI', 'EVI', etc.
    data_level: str             # 'L1C' or 'L2A'
    output_format: str          # 'GeoTIFF', 'NumPy', 'PNG'
    cloud_masking: bool
    tile_size_deg: float = None  # optional override for tile size

# === Example Presets ===

vegetation_monitoring_monthly = DataAcquisitionConfig(
    region='Canterbury',
    bbox=[172.548523, -43.931033, 173.194656, -43.570442],
    time_interval=('2022-01-01', '2022-12-31'),
    temporal_granularity='monthly',
    cloud_cover_threshold=30,
    mosaicking_order='leastCC',
    acquisition_strategy='best_per_tile',
    resolution=10,
    index_type='NDVI',
    data_level='L2A',
    output_format='GeoTIFF',
    cloud_masking=True
)

rgb_snapshot_quickview = DataAcquisitionConfig(
    region='Canterbury',
    bbox=[172.548523, -43.931033, 173.194656, -43.570442],
    time_interval=('2023-01-01', '2023-01-15'),
    temporal_granularity='single',
    cloud_cover_threshold=50,
    mosaicking_order='mostRecent',
    acquisition_strategy='same_day_all_tiles',
    resolution=10,
    index_type='RGB',
    data_level='L1C',
    output_format='PNG',
    cloud_masking=False
)

ndvi_high_precision = DataAcquisitionConfig(
    region='South Island',
    bbox=[166.0, -47.2, 174.5, -40.5],
    time_interval=('2023-10-01', '2023-10-31'),
    temporal_granularity='weekly',
    cloud_cover_threshold=10,
    mosaicking_order='leastCC',
    acquisition_strategy='same_day_all_tiles',
    resolution=10,
    index_type='NDVI',
    data_level='L2A',
    output_format='GeoTIFF',
    cloud_masking=True
)

lilys_profile = DataAcquisitionConfig(
    region='Canterbury',
    bbox=[172.529297,-35.033370,173.546906,-34.313950],
    time_interval=('2023-01-01', '2023-12-31'),
    temporal_granularity='monthly',
    cloud_cover_threshold=20,
    mosaicking_order='leastCC',
    acquisition_strategy='best_per_tile',
    resolution=10,
    index_type='NDVI',
    data_level='L2A',
    output_format='GeoTIFF',
    cloud_masking=True
)

# === Evalscript for raw bands (for postprocessing) ===
evalscript_raw_bands = """
//VERSION=3
function setup() {
  return {
    input: [{ bands: ["B02", "B03", "B04", "B08", "B11", "B12"] }],
    output: { bands: 6, sampleType: "FLOAT32" }
  };
}
function evaluatePixel(sample) {
  return [sample.B02, sample.B03, sample.B04, sample.B08, sample.B11, sample.B12];
}
"""