from copy import deepcopy
from datetime import date, timedelta
from utils.job_utils import generate_job_id
from dateutil.relativedelta import relativedelta

def generate_time_intervals(
        profile
    ) -> list[tuple[date, date]]:
    """
    Generate time intervals for a given profile using its time_series_mode or explicit intervals.
    All modes follow strict provenance, meaning each interval corresponds to a separate retrieval.
    Args:
        profile (DataAcquisitionConfig): The configured profile.
    Returns:
        list of (start_date, end_date) tuples
    """
    start_date, end_date = profile.time_interval

    if start_date > end_date:
        raise ValueError("start_date must be before end_date")

    # If custom intervals are defined, return them directly
    if profile.time_series_custom_intervals:
        return profile.time_series_custom_intervals

    # Otherwise, use time_series_mode to derive intervals
    mode = profile.time_series_mode or "monthly"
    intervals = []

    if mode == "daily":
        return [(d, d) for d in daterange(start_date, end_date)]

    elif mode == "monthly":
        current = start_date
        while current <= end_date:
            next_month = current + relativedelta(months=1)
            interval_end = min(next_month - timedelta(days=1), end_date)
            intervals.append((current, interval_end))
            current = next_month

    elif mode == "quarterly":
        current = start_date
        while current <= end_date:
            next_quarter = current + relativedelta(months=3)
            interval_end = min(next_quarter - timedelta(days=1), end_date)
            intervals.append((current, interval_end))
            current = next_quarter

    else:
        raise ValueError(f"Unsupported time_series_mode: {mode}")

    return intervals

def daterange(
        start: date, 
        end: date
    ) -> list[date]:
    """
    Generate a list of dates between start and end, inclusive.
    Args:
        start (date): Start date.
        end (date): End date.
    Returns:
        list of dates
    """
    return [start + timedelta(days=i) for i in range((end - start).days + 1)]

def create_timeseries_jobs(
        profile
    ) -> list:
    """
    Create a list of sub-profiles (DataAcquisitionConfig) for each time interval based on the profile's time series mode.
    Each returned profile represents an individual job with its own job_id and a reference to the parent job.
    Args:
        profile (DataAcquisitionConfig): The original timeseries profile.
    Returns:
        list[DataAcquisitionConfig]: A list of derived job profiles with modified time intervals and job metadata.
    """
    from profiles import DataAcquisitionConfig  # Local import to avoid circular dependency
    time_intervals = generate_time_intervals(profile)
    timeseries_jobs = []

    for interval in time_intervals:
        sub_profile = deepcopy(profile)
        sub_profile.time_interval = interval
        sub_profile.parent_job_id = profile.job_id
        sub_profile.job_id = generate_job_id(sub_profile)
        timeseries_jobs.append(sub_profile)

    return timeseries_jobs
