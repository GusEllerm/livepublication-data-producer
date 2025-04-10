from dataclasses import dataclass
from datetime import date
from typing import List, Optional, Tuple

from utils.job_utils import generate_job_id


@dataclass
class DataAcquisitionConfig:
    """
    Configuration class for defining satellite data acquisition jobs.

    Attributes:
        region (str): Name or label for the geographic region of interest.
        bbox (list): Bounding box of the region [min_lon, min_lat, max_lon, max_lat].
        time_interval (Tuple[date, date]): Date range for data acquisition.
        resolution (int): Desired resolution in meters.
        output_base_dir (str): Base directory for output files.
        time_series_mode (Optional[str]): If set, defines how to subdivide the time_interval into intervals for timeseries jobs (e.g., 'daily', 'monthly').
        time_series_custom_intervals (Optional[List[Tuple[date, date]]]): Manually defined list of date intervals to override automatic subdivision.
        orbit_selection_strategy (str): Strategy used to select the optimal orbit from available Sentinel data (e.g., 'least_cloud', 'nearest_date').
        job_id (Optional[str]): Unique identifier automatically generated for the job based on region and time interval. Should not be manually set.
        parent_job_id (Optional[str]): Internal identifier used for timeseries jobs to associate sub-jobs with their parent job. Not intended for user modification.
    """
    region: str
    bbox: list  # [min_lon, min_lat, max_lon, max_lat]
    time_interval: Tuple[date, date]
    resolution: int
    output_base_dir: str
    time_series_mode: Optional[str] = None
    time_series_custom_intervals: Optional[List[Tuple[date, date]]] = None
    orbit_selection_strategy: str = "least_cloud"  # Strategy for selecting best orbit
    job_id: Optional[str] = None
    parent_job_id: Optional[str] = None

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


# === Example non-timeseries ===
daily_ndvi_canterbury = DataAcquisitionConfig(
    region='Canterbury',
    bbox=[46.560745,-19.237253,46.934967,-18.990064],
    time_interval=two_months,
    resolution=10,
    output_base_dir="outputs",
    orbit_selection_strategy='least_cloud'
)
daily_ndvi_canterbury.job_id = generate_job_id(daily_ndvi_canterbury)

monthly_rgb_westcoast = DataAcquisitionConfig(
    region='West Coast',
    bbox=[171.0, -43.5, 171.8, -42.8],
    time_interval=(date(2022, 1, 1), date(2022, 3, 31)),
    resolution=10,
    output_base_dir="outputs",
    orbit_selection_strategy='least_cloud'
)
monthly_rgb_westcoast.job_id = generate_job_id(monthly_rgb_westcoast)

custom_ndvi_test = DataAcquisitionConfig(
    region='Test Area',
    bbox=[172.6, -43.9, 172.8, -43.7],
    time_interval=(date(2022, 6, 1), date(2022, 8, 31)),
    resolution=10,
    output_base_dir="outputs",
    orbit_selection_strategy='least_cloud'
)
custom_ndvi_test.job_id = generate_job_id(custom_ndvi_test)

viti_levu_ndvi = DataAcquisitionConfig(
    region='Viti Levu',
    bbox=[176.901855,-18.508261,179.167786,-17.127667],
    time_interval=(date(2024, 8, 1), date(2025, 4, 1)),
    resolution=10,
    output_base_dir="outputs",
    orbit_selection_strategy='least_cloud'
)
viti_levu_ndvi.job_id = generate_job_id(viti_levu_ndvi)

# ======= example timeseries jobs =======
bi_weekly_ndvi_test = DataAcquisitionConfig(
    region='Two Week Daily',
    bbox=[144.301300,-28.667094,144.681702,-28.392608], 
    time_interval=(date(2022, 4, 1), date(2022, 4, 14)),
    resolution=10,
    output_base_dir="outputs",
    time_series_mode='daily',
    orbit_selection_strategy='least_cloud'
)
bi_weekly_ndvi_test.job_id = generate_job_id(bi_weekly_ndvi_test)

six_months_monthly = DataAcquisitionConfig(
    region='Six Months Monthly',
    bbox=[144.301300,-28.667094,144.681702,-28.392608],
    time_interval=(date(2022, 1, 1), date(2022, 6, 30)),
    resolution=10,
    output_base_dir="outputs",
    time_series_mode='monthly',
    orbit_selection_strategy='least_cloud'
)
six_months_monthly.job_id = generate_job_id(six_months_monthly)

three_years_quarterly = DataAcquisitionConfig(
    region='Three Years Quarterly',
    bbox=[144.301300,-28.667094,144.681702,-28.392608],
    time_interval=(date(2020, 1, 1), date(2023, 1, 1)),
    resolution=10,
    output_base_dir="outputs",
    time_series_mode='quarterly',
    orbit_selection_strategy='least_cloud'
)
three_years_quarterly.job_id = generate_job_id(three_years_quarterly)

# Example custom intervals
custom_intervals = time_series_custom_intervals=[
        (date(2022, 6, 1), date(2022, 6, 15)),
        (date(2022, 6, 16), date(2022, 6, 30)),
        (date(2022, 7, 1), date(2022, 7, 15)),
        (date(2022, 7, 16), date(2022, 7, 31)),
        (date(2022, 8, 1), date(2022, 8, 15)),
        (date(2022, 8, 16), date(2022, 8, 31))
        ]


# ===== Timeseries profiles of events =======

# Example: White Island Eruption
white_island_eruption = DataAcquisitionConfig(
    region='White Island Eruption',
    bbox=[177.126560,-37.556826,177.243462,-37.488344],
    time_interval=(date(2019, 11, 20), date(2020, 1, 31)),
    resolution=10,
    output_base_dir="outputs",
    time_series_mode='daily',
    orbit_selection_strategy='least_cloud'
)
white_island_eruption.job_id = generate_job_id(white_island_eruption)


# Example 2019-2020 Australian Bushfires, New South Wales, Bega Valley
australian_bushfires = DataAcquisitionConfig(
    region='Australian Bushfires',
    bbox=[149.537659,-37.517351,150.085602,-36.831272],
    time_interval=(date(2019, 10, 1), date(2020, 5, 31)),
    resolution=10,
    output_base_dir="outputs",
    time_series_mode='monthly',
    orbit_selection_strategy='least_cloud'
)
australian_bushfires.job_id = generate_job_id(australian_bushfires)