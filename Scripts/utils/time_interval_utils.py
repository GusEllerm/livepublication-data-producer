from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

def generate_time_intervals(start_date: date, end_date: date, mode: str, strict_provenance: bool = False) -> list[tuple[date, date]]:
    """
    Generate time intervals between start_date and end_date based on the specified mode.
    Args:
        start_date (date): Start date as a date object.
        end_date (date): End date as a date object.
        mode (str): Time series mode, e.g., 'monthly', 'quarterly'.
        strict_provenance (bool): If True, generate 1-day intervals regardless of mode.
    Returns:
        list of (start, end) date tuples as date objects.
    """
    if start_date > end_date:
        raise ValueError("start_date must be before end_date")

    intervals = []
    current = start_date

    if strict_provenance:
        while current <= end_date:
            intervals.append((current, current))
            current += timedelta(days=1)
        return intervals

    if mode == "monthly":
        while current <= end_date:
            next_month = current + relativedelta(months=1)
            interval_end = min(next_month - timedelta(days=1), end_date)
            intervals.append((current, interval_end))
            current = next_month

    elif mode == "quarterly":
        while current <= end_date:
            next_quarter = current + relativedelta(months=3)
            interval_end = min(next_quarter - timedelta(days=1), end_date)
            intervals.append((current, interval_end))
            current = next_quarter

    else:
        raise ValueError(f"Unsupported time_series_mode: {mode}")

    return intervals


def format_time_interval_prefix(start: date, end: date) -> str:
    """
    Format a string prefix from a time interval.
    Args:
        start (date): Start date as a date object.
        end (date): End date as a date object.
    Returns:
        str: Formatted prefix.
    """
    return f"{start.strftime('%Y%m%d')}__{end.strftime('%Y%m%d')}"
