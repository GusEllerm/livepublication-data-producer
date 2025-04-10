from datetime import date

from utils.job_utils import generate_job_id
from utils.time_interval_utils import (
    create_timeseries_jobs,
    daterange,
    generate_time_intervals,
)


def test_generate_time_intervals_with_monthly_mode():
    class DummyProfile:
        time_interval = (date(2023, 1, 1), date(2023, 3, 15))
        time_series_mode = "monthly"
        time_series_custom_intervals = None

    intervals = generate_time_intervals(DummyProfile())
    assert len(intervals) == 3
    assert intervals[0] == (date(2023, 1, 1), date(2023, 1, 31))
    assert intervals[1] == (date(2023, 2, 1), date(2023, 2, 28))
    assert intervals[2] == (date(2023, 3, 1), date(2023, 3, 15))

def test_daterange_inclusive():
    start = date(2023, 1, 1)
    end = date(2023, 1, 3)
    dates = daterange(start, end)
    assert dates == [date(2023, 1, 1), date(2023, 1, 2), date(2023, 1, 3)]

def test_create_timeseries_jobs_creates_unique_jobs():
    class DummyProfile:
        region = "Test Region"
        time_interval = (date(2023, 1, 1), date(2023, 2, 15))
        time_series_mode = "monthly"
        time_series_custom_intervals = None
        job_id = None

    jobs = create_timeseries_jobs(DummyProfile())

    assert len(jobs) == 2
    for job in jobs:
        assert job.time_interval[0].month in [1, 2]
        assert hasattr(job, "job_id")
        assert job.parent_job_id == generate_job_id(DummyProfile())
