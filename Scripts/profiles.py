from dataclasses import dataclass
from datetime import date
from typing import Tuple, Optional, List

@dataclass
class DataAcquisitionConfig:
    region: str
    bbox: list  # [min_lon, min_lat, max_lon, max_lat]
    time_interval: Tuple[date, date]
    cloud_cover_threshold: int
    mosaicking_order: str
    acquisition_strategy: str
    resolution: int
    index_type: str
    data_level: str
    output_format: str
    cloud_masking: bool
    tile_size_deg: float = None
    time_series_mode: Optional[str] = None
    time_series_custom_intervals: Optional[List[Tuple[date, date]]] = None
    strict_provenance: bool = False

# === Example Presets ===

vegetation_monitoring_monthly = DataAcquisitionConfig(
    region='Canterbury',
    bbox=[172.548523, -43.931033, 173.194656, -43.570442],
    time_interval=(date(2022, 1, 1), date(2022, 12, 31)),
    cloud_cover_threshold=30,
    mosaicking_order='leastCC',
    acquisition_strategy='best_per_tile',
    resolution=10,
    index_type='NDVI',
    data_level='L2A',
    output_format='GeoTIFF',
    cloud_masking=True,
    strict_provenance=False
)

rgb_snapshot_quickview = DataAcquisitionConfig(
    region='Canterbury',
    bbox=[172.548523, -43.931033, 173.194656, -43.570442],
    time_interval=(date(2023, 1, 1), date(2023, 1, 15)),
    cloud_cover_threshold=50,
    mosaicking_order='mostRecent',
    acquisition_strategy='same_day_all_tiles',
    resolution=10,
    index_type='RGB',
    data_level='L1C',
    output_format='PNG',
    cloud_masking=False,
    strict_provenance=False
)

ndvi_high_precision = DataAcquisitionConfig(
    region='South Island',
    bbox=[166.0, -47.2, 174.5, -40.5],
    time_interval=(date(2023, 10, 1), date(2023, 10, 31)),
    cloud_cover_threshold=10,
    mosaicking_order='leastCC',
    acquisition_strategy='same_day_all_tiles',
    resolution=10,
    index_type='NDVI',
    data_level='L2A',
    output_format='GeoTIFF',
    cloud_masking=True,
    strict_provenance=False
)

lilys_profile = DataAcquisitionConfig(
    region='Canterbury',
    bbox=[172.529297,-35.033370,173.546906,-34.313950],
    time_interval=(date(2023, 1, 1), date(2023, 12, 31)),
    cloud_cover_threshold=20,
    mosaicking_order='leastCC',
    acquisition_strategy='best_per_tile',
    resolution=10,
    index_type='NDVI',
    data_level='L2A',
    output_format='GeoTIFF',
    cloud_masking=True,
    strict_provenance=False
)

test_timeseries_profile = DataAcquisitionConfig(
    region='Test Region',
    bbox=[172.548523, -43.931033, 173.194656, -43.570442],  
    time_interval=(date(2022, 6, 1), date(2022, 8, 31)),  # 3 months
    cloud_cover_threshold=40,
    mosaicking_order='leastCC',
    acquisition_strategy='best_per_tile',
    resolution=10,
    index_type='NDVI',
    data_level='L2A',
    output_format='GeoTIFF',
    cloud_masking=True,
    time_series_mode='monthly',
    strict_provenance=False
)

strict_provenance_profile = DataAcquisitionConfig(
    region='Metadata Test Region',
    bbox=[172.6, -43.8, 172.8, -43.6],  # Small test region
    time_interval=(date(2022, 7, 1), date(2022, 7, 5)),  # 5 days
    cloud_cover_threshold=20,
    mosaicking_order='leastCC',
    acquisition_strategy='same_day_all_tiles',
    resolution=10,
    index_type='NDVI',
    data_level='L2A',
    output_format='GeoTIFF',
    cloud_masking=True,
    time_series_mode='daily',
    strict_provenance=True
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