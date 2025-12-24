"""Unit tests for geo_utils module."""

import sys
import unittest
from pathlib import Path

import numpy as np

# Add the parent directory to the path so we can import the module
sys.path.insert(0, str(Path(__file__).parent.parent))

from soilmoisture.utils.geo_utils import get_location  # noqa: E402


class TestGeoUtils(unittest.TestCase):
    """Test cases for geo_utils module."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a simple grid for testing
        self.lat_grid = np.linspace(-90, 90, 181)  # 1 degree resolution
        self.lon_grid = np.linspace(-180, 180, 361)  # 1 degree resolution

    def test_get_location_exact_match(self):
        """Test getting location with exact match."""
        # Test with a point that exists exactly on the grid
        lat, lon = 0.0, 0.0
        row, col = get_location(lat, lon, self.lat_grid, self.lon_grid)
        self.assertEqual(row, 90)  # 0 degrees is at index 90 (90 + 0)
        self.assertEqual(col, 180)  # 0 degrees is at index 180 (180 + 0)

    def test_get_location_approximate_match(self):
        """Test getting location with approximate match."""
        # Test with a point that doesn't exist exactly on the grid
        lat, lon = 0.4, 0.4
        row, col = get_location(lat, lon, self.lat_grid, self.lon_grid)
        self.assertEqual(row, 90)  # Should round to 0 degrees (index 90)
        self.assertEqual(col, 180)  # Should round to 0 degrees (index 180)

    def test_get_location_edge_case_positive(self):
        """Test getting location at the positive edge of the grid."""
        lat, lon = 90.0, 180.0
        row, col = get_location(lat, lon, self.lat_grid, self.lon_grid)
        self.assertEqual(row, 180)  # 90 degrees is at index 180 (90 + 90)
        self.assertEqual(col, 360)  # 180 degrees is at index 360 (180 + 180)

    def test_get_location_edge_case_negative(self):
        """Test getting location at the negative edge of the grid."""
        lat, lon = -90.0, -180.0
        row, col = get_location(lat, lon, self.lat_grid, self.lon_grid)
        self.assertEqual(row, 0)  # -90 degrees is at index 0
        self.assertEqual(col, 0)  # -180 degrees is at index 0

    def test_get_location_longitude_wrap_around(self):
        """Test getting location with longitude wrap-around."""
        # Test with a point just west of the dateline
        lat, lon = 0.0, 179.9
        row, col = get_location(lat, lon, self.lat_grid, self.lon_grid)
        self.assertEqual(col, 360)  # Should wrap around to -180 degrees (index 0)

    def test_get_location_invalid_lat(self):
        """Test getting location with invalid latitude."""
        with self.assertRaises(ValueError):
            get_location(100.0, 0.0, self.lat_grid, self.lon_grid)  # Invalid latitude

    def test_get_location_invalid_lon(self):
        """Test getting location with invalid longitude."""
        with self.assertRaises(ValueError):
            get_location(0.0, 200.0, self.lat_grid, self.lon_grid)  # Invalid longitude

    def test_get_location_empty_grid(self):
        """Test getting location with empty grid."""
        with self.assertRaises(ValueError):
            get_location(0.0, 0.0, np.array([]), np.array([]))  # Empty grids


if __name__ == "__main__":
    unittest.main()
