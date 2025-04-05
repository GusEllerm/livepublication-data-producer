from dataclasses import dataclass
from datetime import date
from typing import Tuple, Optional, List
from utils.job_utils import generate_job_id

@dataclass
class DataAcquisitionConfig:
    region: str
    bbox: list  # [min_lon, min_lat, max_lon, max_lat]
    time_interval: Tuple[date, date]
    resolution: int
    time_series_mode: Optional[str] = None
    time_series_custom_intervals: Optional[List[Tuple[date, date]]] = None
    orbit_selection_strategy: str = "least_cloud"  # Strategy for selecting best orbit
    job_id: Optional[str] = None

# === Orbit Selection Strategies ===
# "least_cloud": Select orbit with lowest average cloud coverage.
# "nearest_date": Select orbit closest to the midpoint of the time interval.
# "max_coverage": (Planned) Select orbit with maximum spatial coverage of bbox.
# "composite_score": (Planned) Combine multiple heuristics for scoring and ranking.

# === Example Bboxes ===
Small_bbox = [171.739011,-42.889392,171.771498,-42.866717]
big_bbox = [172.5, -44.0, 173.2, -43.5]
auckland = [174.089355,-37.727280,175.989990,-36.253133]
# === Example Time Intervals ===
ten_days = (date(2022, 1, 1), date(2022, 1, 10))
two_months = (date(2022, 1, 1), date(2022, 3, 31))
six_months = (date(2022, 1, 1), date(2022, 6, 30))


# === Example Presets ===
daily_ndvi_canterbury = DataAcquisitionConfig(
    region='Canterbury',
    bbox=auckland,
    time_interval=six_months,
    resolution=10,
    time_series_mode='daily',
    orbit_selection_strategy='least_cloud'
)
daily_ndvi_canterbury.job_id = generate_job_id(daily_ndvi_canterbury)

monthly_rgb_westcoast = DataAcquisitionConfig(
    region='West Coast',
    bbox=[171.0, -43.5, 171.8, -42.8],
    time_interval=(date(2022, 1, 1), date(2022, 3, 31)),
    resolution=10,
    time_series_mode='monthly',
    orbit_selection_strategy='least_cloud'
)
monthly_rgb_westcoast.job_id = generate_job_id(monthly_rgb_westcoast)

custom_ndvi_test = DataAcquisitionConfig(
    region='Test Area',
    bbox=[172.6, -43.9, 172.8, -43.7],
    time_interval=(date(2022, 6, 1), date(2022, 8, 31)),
    resolution=10,
    time_series_custom_intervals=[
        (date(2022, 6, 1), date(2022, 6, 15)),
        (date(2022, 6, 16), date(2022, 6, 30)),
        (date(2022, 7, 1), date(2022, 7, 15)),
        (date(2022, 7, 16), date(2022, 7, 31)),
        (date(2022, 8, 1), date(2022, 8, 15)),
        (date(2022, 8, 16), date(2022, 8, 31))
    ],
    orbit_selection_strategy='least_cloud'
)
custom_ndvi_test.job_id = generate_job_id(custom_ndvi_test)
