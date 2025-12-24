"""Tests for time_utils module."""

import pytest
from soilmoisture.utils.time_utils import utc2local


def test_utc2local_positive_longitude():
    """Test UTC to local time conversion for positive longitude."""
    # Test with longitude in Eastern Hemisphere (UTC+8)
    lon = 120.0  # 120°E is UTC+8
    utc_date = "20230101"
    utc_time = "12:00"

    local_date, local_time = utc2local(lon, utc_date, utc_time)

    assert local_date == "20230101"
    assert local_time == "20:00"  # 12:00 UTC + 8 hours


def test_utc2local_negative_longitude():
    """Test UTC to local time conversion for negative longitude."""
    # Test with longitude in Western Hemisphere (UTC-5)
    lon = -75.0  # 75°W is UTC-5
    utc_date = "20230101"
    utc_time = "12:00"

    local_date, local_time = utc2local(lon, utc_date, utc_time)

    assert local_date == "20230101"
    assert local_time == "07:00"  # 12:00 UTC - 5 hours


def test_utc2local_date_crossing():
    """Test UTC to local time conversion when crossing date boundaries."""
    # Test crossing to next day
    lon = 150.0  # UTC+10
    utc_date = "20230101"
    utc_time = "20:00"

    local_date, local_time = utc2local(lon, utc_date, utc_time)

    assert local_date == "20230102"  # Crossed to next day
    assert local_time == "06:00"

    # Test crossing to previous day
    lon = -150.0  # UTC-10
    utc_date = "20230101"
    utc_time = "02:00"

    local_date, local_time = utc2local(lon, utc_date, utc_time)

    # The function should go back to the previous day (2022-12-31)
    assert local_date == "20221231"
    assert local_time == "16:00"


def test_utc2local_date_format():
    """Test UTC to local time conversion with different date formats."""
    # Test with YYYY/MM/DD format
    lon = 0.0
    utc_date = "2023/01/01"
    utc_time = "12:00"

    local_date, local_time = utc2local(lon, utc_date, utc_time)

    assert local_date == "20230101"
    assert local_time == "12:00"


def test_utc2local_edge_cases():
    """Test edge cases for UTC to local time conversion."""
    # Test at prime meridian (UTC+0)
    lon = 0.0
    utc_date = "20230101"
    utc_time = "12:00"

    local_date, local_time = utc2local(lon, utc_date, utc_time)
    assert local_date == "20230101"
    assert local_time == "12:00"

    # Test at international date line (should be UTC+12 or UTC-12)
    lon = 180.0
    local_date, local_time = utc2local(lon, utc_date, utc_time)
    assert local_date == "20230102"  # +12 hours from UTC
    assert local_time == "00:00"

    lon = -180.0
    local_date, local_time = utc2local(lon, utc_date, utc_time)
    # -12 hours from UTC should be the same date since we're at the date line
    assert local_date == "20230101"
    assert local_time == "00:00"
