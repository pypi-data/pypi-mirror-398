"""Unit tests for time_utils module."""

import sys
import unittest
from pathlib import Path

# Add the parent directory to the path so we can import the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from soilmoisture.utils.time_utils import utc2local  # noqa: E402


class TestTimeUtils(unittest.TestCase):
    """Test cases for time_utils module."""

    def test_utc2local_positive_longitude(self):
        """Test UTC to local time conversion with positive longitude."""
        # 15 degrees east should be UTC+1
        local_date, local_time = utc2local(15, "20230101", "12:00")
        self.assertEqual(local_date, "20230101")
        self.assertEqual(local_time, "13:00")  # +1 hour

    def test_utc2local_negative_longitude(self):
        """Test UTC to local time conversion with negative longitude."""
        # 30 degrees west should be UTC-2
        local_date, local_time = utc2local(-30, "20230101", "12:00")
        self.assertEqual(local_date, "20230101")
        self.assertEqual(local_time, "10:00")  # -2 hours

    def test_utc2local_date_crossing(self):
        """Test UTC to local time conversion that crosses date boundary."""
        # 165 degrees east should be UTC+11
        local_date, local_time = utc2local(165, "20230101", "20:00")
        self.assertEqual(local_date, "20230102")  # Next day
        self.assertEqual(local_time, "07:00")  # +11 hours

    def test_utc2local_negative_date_crossing(self):
        """Test UTC to local time conversion that crosses date boundary backwards."""
        # 165 degrees west should be UTC-11
        local_date, local_time = utc2local(-165, "20230101", "02:00")
        self.assertEqual(local_date, "20201231")  # Previous day in 2020 (leap year)
        self.assertEqual(local_time, "15:00")  # -11 hours

    def test_utc2local_invalid_date_format(self):
        """Test UTC to local time conversion with invalid date format."""
        with self.assertRaises(ValueError):
            utc2local(0, "invalid_date", "12:00")

    def test_utc2local_invalid_time_format(self):
        """Test UTC to local time conversion with invalid time format."""
        with self.assertRaises(ValueError):
            utc2local(0, "20230101", "invalid_time")

    def test_utc2local_slash_date_format(self):
        """Test UTC to local time conversion with slash date format."""
        local_date, local_time = utc2local(0, "2023/01/01", "12:00")
        self.assertEqual(local_date, "20230101")
        self.assertEqual(local_time, "12:00")


if __name__ == "__main__":
    unittest.main()
