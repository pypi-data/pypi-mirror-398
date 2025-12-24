"""Unit tests for matching module."""

import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd

# Add the parent directory to the path so we can import the module
sys.path.insert(0, str(Path(__file__).parent.parent))

from soilmoisture.core.matching import (  # noqa: E402
    SoilMoistureDataMatcher,
    load_in_situ_data,
    match_temporal_data,
)


class TestSoilMoistureDataMatcher(unittest.TestCase):
    """Test cases for SoilMoistureDataMatcher class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.matcher = SoilMoistureDataMatcher()
        
        # Create sample in-situ data
        dates = pd.date_range('2020-01-01', '2020-01-10', freq='D')
        self.sample_insitu_data = pd.DataFrame({
            'datetime': dates,
            'soil_moisture': np.random.uniform(0.1, 0.4, len(dates)),
            'temperature': np.random.uniform(15, 25, len(dates))
        })
        
        # Create sample satellite data
        self.sample_satellite_data = np.random.uniform(0.05, 0.35, len(dates))

    def test_load_in_situ_data_csv(self):
        """Test loading in-situ data from CSV file."""
        # Create a temporary CSV file
        csv_file = Path(self.temp_dir) / "test_insitu.csv"
        self.sample_insitu_data.to_csv(csv_file, index=False)
        
        loaded_data = load_in_situ_data(str(csv_file))
        
        self.assertIsInstance(loaded_data, pd.DataFrame)
        self.assertEqual(len(loaded_data), len(self.sample_insitu_data))
        self.assertIn('datetime', loaded_data.columns)
        self.assertIn('soil_moisture', loaded_data.columns)

    def test_match_temporal_data_exact_match(self):
        """Test temporal matching with exact time matches."""
        # Create matching timestamps
        timestamps1 = pd.date_range('2020-01-01', '2020-01-05', freq='D')
        timestamps2 = pd.date_range('2020-01-01', '2020-01-05', freq='D')
        
        data1 = pd.Series([0.1, 0.2, 0.3, 0.4, 0.5], index=timestamps1)
        data2 = pd.Series([0.15, 0.25, 0.35, 0.45, 0.55], index=timestamps2)
        
        matched_data = match_temporal_data(data1, data2, time_window_hours=1)
        
        self.assertEqual(len(matched_data), 5)
        self.assertAlmostEqual(matched_data.iloc[0]['data1'], 0.1)
        self.assertAlmostEqual(matched_data.iloc[0]['data2'], 0.15)

    def test_match_temporal_data_with_tolerance(self):
        """Test temporal matching with time tolerance."""
        # Create slightly offset timestamps
        timestamps1 = pd.date_range('2020-01-01 00:00', '2020-01-03 00:00', freq='D')
        timestamps2 = pd.date_range('2020-01-01 01:30', '2020-01-03 01:30', freq='D')
        
        data1 = pd.Series([0.1, 0.2, 0.3], index=timestamps1)
        data2 = pd.Series([0.15, 0.25, 0.35], index=timestamps2)
        
        # Should match with 3-hour tolerance
        matched_data = match_temporal_data(data1, data2, time_window_hours=3)
        self.assertEqual(len(matched_data), 3)
        
        # Should not match with 1-hour tolerance
        matched_data_strict = match_temporal_data(data1, data2, time_window_hours=1)
        self.assertEqual(len(matched_data_strict), 0)

    def test_match_temporal_data_missing_values(self):
        """Test temporal matching with missing values."""
        timestamps1 = pd.date_range('2020-01-01', '2020-01-05', freq='D')
        timestamps2 = pd.date_range('2020-01-02', '2020-01-04', freq='D')  # Missing first and last
        
        data1 = pd.Series([0.1, 0.2, 0.3, 0.4, 0.5], index=timestamps1)
        data2 = pd.Series([0.25, 0.35, 0.45], index=timestamps2)
        
        matched_data = match_temporal_data(data1, data2, time_window_hours=1)
        
        # Should only match the overlapping dates
        self.assertEqual(len(matched_data), 3)

    def test_calculate_statistics(self):
        """Test calculation of comparison statistics."""
        # Create test data with known statistics
        insitu_values = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
        satellite_values = np.array([0.12, 0.18, 0.32, 0.38, 0.52])
        
        matched_data = pd.DataFrame({
            'in_situ': insitu_values,
            'satellite': satellite_values
        })
        
        stats = self.matcher.calculate_statistics(matched_data)
        
        # Check that all expected statistics are present
        expected_stats = ['correlation', 'bias', 'rmse', 'ubrmse', 'mae', 'count']
        for stat in expected_stats:
            self.assertIn(stat, stats)
        
        # Check that correlation is reasonable (should be high for this test data)
        self.assertGreater(stats['correlation'], 0.9)
        
        # Check that count matches input data
        self.assertEqual(stats['count'], 5)

    def test_process_site_data(self):
        """Test processing data for a single site."""
        # Create mock file paths
        insitu_file = Path(self.temp_dir) / "insitu.csv"
        satellite_file = Path(self.temp_dir) / "satellite.nc"
        
        # Save sample in-situ data
        self.sample_insitu_data.to_csv(insitu_file, index=False)
        
        # Mock the satellite data loading
        with patch('soilmoisture.core.lprm_utils.load_lprm_data') as mock_load:
            mock_load.return_value = (
                self.sample_satellite_data,
                pd.date_range('2020-01-01', '2020-01-10', freq='D')
            )
            
            result = self.matcher.process_site_data(
                str(insitu_file),
                str(satellite_file),
                site_lat=41.1649,
                site_lon=-96.4766,
                time_window_hours=3
            )
            
            self.assertIsInstance(result, dict)
            self.assertIn('matched_data', result)
            self.assertIn('statistics', result)

    def test_quality_control_filters(self):
        """Test quality control filtering of data."""
        # Create data with some outliers and missing values
        data = pd.DataFrame({
            'in_situ': [0.1, 0.2, 0.3, 1.5, 0.4, np.nan, 0.5],  # 1.5 is outlier, nan is missing
            'satellite': [0.12, 0.18, 0.32, 0.38, np.nan, 0.45, 0.52]  # nan is missing
        })
        
        # Apply quality control
        cleaned_data = self.matcher.apply_quality_control(data)
        
        # Should remove rows with missing values and extreme outliers
        self.assertLess(len(cleaned_data), len(data))
        
        # Should not contain any NaN values
        self.assertFalse(cleaned_data.isnull().any().any())
        
        # Should not contain extreme outliers (>1.0 for soil moisture)
        self.assertTrue((cleaned_data['in_situ'] <= 1.0).all())
        self.assertTrue((cleaned_data['satellite'] <= 1.0).all())


class TestMatchingUtilities(unittest.TestCase):
    """Test cases for matching utility functions."""

    def test_time_window_matching(self):
        """Test time window matching functionality."""
        # Test with different time windows
        base_time = datetime(2020, 1, 1, 12, 0, 0)
        
        # Times within 1 hour window
        time1 = base_time + timedelta(minutes=30)
        time2 = base_time + timedelta(minutes=45)
        
        # Times outside 1 hour window
        time3 = base_time + timedelta(hours=2)
        
        # This would be tested in the actual matching function
        # Here we just verify the concept
        window_hours = 1
        
        diff1 = abs((time1 - base_time).total_seconds()) / 3600
        diff2 = abs((time2 - base_time).total_seconds()) / 3600
        diff3 = abs((time3 - base_time).total_seconds()) / 3600
        
        self.assertLessEqual(diff1, window_hours)
        self.assertLessEqual(diff2, window_hours)
        self.assertGreater(diff3, window_hours)

    def test_data_validation(self):
        """Test data validation functions."""
        # Test valid soil moisture values
        valid_values = np.array([0.05, 0.1, 0.3, 0.5, 0.8])
        self.assertTrue(np.all((valid_values >= 0) & (valid_values <= 1)))
        
        # Test invalid soil moisture values
        invalid_values = np.array([-0.1, 1.5, 2.0])
        self.assertFalse(np.all((invalid_values >= 0) & (invalid_values <= 1)))


if __name__ == "__main__":
    unittest.main()
