import pytest
from datetime import date
from utils import generate_time_intervals, format_time_interval_prefix

def test_generate_monthly_intervals():
    start = date(2022, 1, 1)
    end = date(2022, 3, 31)
    intervals = generate_time_intervals(start, end, "monthly")
    assert len(intervals) == 3
    assert intervals[0] == (date(2022, 1, 1), date(2022, 1, 31))
    assert intervals[2] == (date(2022, 3, 1), date(2022, 3, 31))

def test_generate_invalid_mode():
    with pytest.raises(ValueError):
        generate_time_intervals(date(2022, 1, 1), date(2022, 2, 1), "daily")

def test_format_time_interval_prefix():
    prefix = format_time_interval_prefix(date(2022, 1, 1), date(2022, 1, 31))
    assert prefix == "20220101__20220131"

def test_generate_monthly_intervals_custom_prefix():
    start = date(2022, 1, 1)
    end = date(2022, 3, 31)
    intervals = generate_time_intervals(start, end, "monthly")
    assert len(intervals) == 3
    assert intervals[0] == (date(2022, 1, 1), date(2022, 1, 31))
    assert intervals[1] == (date(2022, 2, 1), date(2022, 2, 28))
    assert intervals[2] == (date(2022, 3, 1), date(2022, 3, 31))

def test_format_time_interval_prefix_custom():
    prefix = format_time_interval_prefix(date(2022, 2, 15), date(2022, 2, 20))
    assert prefix == "20220215__20220220"

def test_generate_invalid_time_series_mode():
    with pytest.raises(ValueError):
        generate_time_intervals(date(2022, 1, 1), date(2022, 2, 1), "invalid_mode")

def test_generate_quarterly_intervals():
    start = date(2022, 1, 1)
    end = date(2022, 12, 31)
    intervals = generate_time_intervals(start, end, "quarterly")
    assert len(intervals) == 4
    assert intervals[0] == (date(2022, 1, 1), date(2022, 3, 31))
    assert intervals[1] == (date(2022, 4, 1), date(2022, 6, 30))
    assert intervals[2] == (date(2022, 7, 1), date(2022, 9, 30))
    assert intervals[3] == (date(2022, 10, 1), date(2022, 12, 31))
