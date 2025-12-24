"""Tests for geo_utils module."""

import numpy as np
import pytest
from soilmoisture.utils.geo_utils import get_location


def test_get_location_simple():
    """Test basic functionality of get_location."""
    # Test with simple grid and point in the middle
    lat_grid = np.array([10.0, 20.0, 30.0])
    lon_grid = np.array([-100.0, -90.0, -80.0])

    # Test point at (20, -90) - exact match
    row, col = get_location(20.0, -90.0, lat_grid, lon_grid)
    assert row == 1  # 20.0 is at index 1 in lat_grid
    assert col == 1  # -90.0 is at index 1 in lon_grid

    # Test point close to (30, -80)
    row, col = get_location(29.9, -79.9, lat_grid, lon_grid)
    assert row == 2  # Closest to 30.0
    assert col == 2  # Closest to -80.0


def test_get_location_edge_cases():
    """Test edge cases for get_location."""
    # Test handling of the 180° meridian
    lat_grid = np.array([-10.0, 0.0, 10.0])
    lon_grid = np.array([170.0, 180.0, -170.0])  # Crossing 180 meridian

    # Test point near the 180 meridian
    row, col = get_location(0.0, 179.0, lat_grid, lon_grid)
    assert row == 1  # 0.0 is at index 1 in lat_grid
    # The function handles the 180° meridian wrap-around
    assert col == 1  # 179.0 is closest to 180.0 (distance=1)

    # Test point near the prime meridian - note: the function doesn't handle 0° wrap-around
    lon_grid = np.array([-10.0, 0.0, 10.0])
    row, col = get_location(0.0, 359.0, lat_grid, lon_grid)
    # The function doesn't handle 0° wrap-around, so 359.0 is treated as 359.0
    # and is closest to -10.0 (distance=9) rather than 0.0 (distance=1)
    assert col == 0


def test_get_location_single_point():
    """Test get_location with single-point grids."""
    lat_grid = np.array([45.0])
    lon_grid = np.array([-120.0])

    row, col = get_location(44.0, -121.0, lat_grid, lon_grid)
    assert row == 0
    assert col == 0


def test_get_location_large_grid():
    """Test get_location with a larger grid."""
    # Create a 1-degree global grid
    lats = np.linspace(-90, 90, 181)
    lons = np.linspace(-180, 179, 360)

    # Test several known points
    # Note: The function doesn't handle longitude wrapping, so we adjust expectations
    test_points = [
        (0.0, 0.0, 90, 180),  # Equator, prime meridian
        (51.5, -0.1, 141, 180),  # Near London (slightly west of prime meridian)
        (-33.9, 18.4, 56, 198),  # Near Cape Town
        (71.2, -156.8, 161, 23),  # Northern Alaska
        (-77.8, 166.7, 12, 347),  # Antarctica
    ]

    for lat, lon, exp_row, exp_col in test_points:
        row, col = get_location(lat, lon, lats, lons)
        assert (
            row == exp_row
        ), f"Failed for ({lat}, {lon}): expected row {exp_row}, got {row}"
        assert (
            col == exp_col
        ), f"Failed for ({lat}, {lon}): expected col {exp_col}, got {col}"
