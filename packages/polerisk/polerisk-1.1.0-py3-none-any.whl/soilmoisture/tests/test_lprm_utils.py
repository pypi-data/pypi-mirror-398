"""Unit tests for lprm_utils module."""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd

# Add the parent directory to the path so we can import the module
sys.path.insert(0, str(Path(__file__).parent.parent))

from soilmoisture.core.lprm_utils import (  # noqa: E402
    LPRMDataLoader,
    extract_pixel_data,
    find_nearest_valid_pixel,
)


class TestLPRMDataLoader(unittest.TestCase):
    """Test cases for LPRMDataLoader class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.loader = LPRMDataLoader()
        
        # Create mock grid coordinates
        self.lat_grid = np.linspace(-89.5, 89.5, 180)  # 1 degree resolution
        self.lon_grid = np.linspace(-179.5, 179.5, 360)  # 1 degree resolution

    @patch('netCDF4.Dataset')
    def test_load_netcdf_file(self, mock_dataset):
        """Test loading NetCDF file."""
        # Mock NetCDF dataset
        mock_nc = MagicMock()
        mock_nc.variables = {
            'soil_moisture': np.random.uniform(0.1, 0.4, (10, 180, 360)),
            'latitude': self.lat_grid,
            'longitude': self.lon_grid,
            'time': np.arange(10)
        }
        mock_dataset.return_value.__enter__.return_value = mock_nc
        
        data = self.loader.load_netcdf_file('/fake/path/test.nc')
        
        self.assertIsInstance(data, dict)
        self.assertIn('soil_moisture', data)
        self.assertIn('latitude', data)
        self.assertIn('longitude', data)

    def test_extract_pixel_data_valid_location(self):
        """Test extracting pixel data for valid location."""
        # Create test data
        soil_moisture_data = np.random.uniform(0.1, 0.4, (10, 180, 360))
        target_lat, target_lon = 41.1649, -96.4766
        
        # Mock the grid finding function
        with patch('soilmoisture.utils.geo_utils.get_location') as mock_get_loc:
            mock_get_loc.return_value = (90, 180)  # Mock grid indices
            
            pixel_data = extract_pixel_data(
                soil_moisture_data, target_lat, target_lon, 
                self.lat_grid, self.lon_grid
            )
            
            self.assertEqual(len(pixel_data), 10)  # Should have 10 time steps
            self.assertTrue(np.all(pixel_data >= 0))  # Soil moisture should be non-negative

    def test_extract_pixel_data_invalid_location(self):
        """Test extracting pixel data for invalid location."""
        soil_moisture_data = np.random.uniform(0.1, 0.4, (10, 180, 360))
        target_lat, target_lon = 100.0, 200.0  # Invalid coordinates
        
        with patch('soilmoisture.utils.geo_utils.get_location') as mock_get_loc:
            mock_get_loc.side_effect = ValueError("Invalid coordinates")
            
            with self.assertRaises(ValueError):
                extract_pixel_data(
                    soil_moisture_data, target_lat, target_lon,
                    self.lat_grid, self.lon_grid
                )

    def test_find_nearest_valid_pixel(self):
        """Test finding nearest valid pixel when target pixel has missing data."""
        # Create data with missing values at target location
        soil_moisture_data = np.random.uniform(0.1, 0.4, (5, 180, 360))
        soil_moisture_data[:, 90, 180] = np.nan  # Target location has missing data
        
        target_row, target_col = 90, 180
        
        valid_data = find_nearest_valid_pixel(
            soil_moisture_data, target_row, target_col, search_radius=3
        )
        
        # Should find valid data from nearby pixels
        self.assertIsNotNone(valid_data)
        self.assertEqual(len(valid_data), 5)
        self.assertFalse(np.any(np.isnan(valid_data)))

    def test_find_nearest_valid_pixel_no_valid_data(self):
        """Test finding nearest valid pixel when no valid data exists in search radius."""
        # Create data with all missing values in search area
        soil_moisture_data = np.full((5, 180, 360), np.nan)
        target_row, target_col = 90, 180
        
        valid_data = find_nearest_valid_pixel(
            soil_moisture_data, target_row, target_col, search_radius=2
        )
        
        # Should return None when no valid data found
        self.assertIsNone(valid_data)

    def test_data_quality_filtering(self):
        """Test data quality filtering functionality."""
        # Create data with some invalid values
        test_data = np.array([0.1, 0.2, -0.1, 1.5, 0.3, np.nan, 0.4])
        
        # Apply quality control (values should be between 0 and 1)
        valid_mask = (test_data >= 0) & (test_data <= 1) & ~np.isnan(test_data)
        filtered_data = test_data[valid_mask]
        
        expected_valid_data = np.array([0.1, 0.2, 0.3, 0.4])
        np.testing.assert_array_equal(filtered_data, expected_valid_data)

    @patch('netCDF4.Dataset')
    def test_load_multiple_files(self, mock_dataset):
        """Test loading multiple NetCDF files."""
        # Mock multiple files
        mock_nc = MagicMock()
        mock_nc.variables = {
            'soil_moisture': np.random.uniform(0.1, 0.4, (5, 180, 360)),
            'latitude': self.lat_grid,
            'longitude': self.lon_grid,
            'time': np.arange(5)
        }
        mock_dataset.return_value.__enter__.return_value = mock_nc
        
        file_list = ['/fake/path/file1.nc', '/fake/path/file2.nc']
        combined_data = self.loader.load_multiple_files(file_list)
        
        self.assertIsInstance(combined_data, dict)
        self.assertIn('soil_moisture', combined_data)
        # Should have combined time dimension (5 + 5 = 10)
        self.assertEqual(combined_data['soil_moisture'].shape[0], 10)

    def test_temporal_interpolation(self):
        """Test temporal interpolation of missing data."""
        # Create time series with missing values
        dates = pd.date_range('2020-01-01', '2020-01-10', freq='D')
        values = np.array([0.1, 0.2, np.nan, np.nan, 0.5, 0.6, np.nan, 0.8, 0.9, 1.0])
        
        time_series = pd.Series(values, index=dates)
        
        # Interpolate missing values
        interpolated = time_series.interpolate(method='linear')
        
        # Check that missing values were filled
        self.assertFalse(interpolated.isnull().any())
        
        # Check that interpolated values are reasonable
        self.assertAlmostEqual(interpolated.iloc[2], 0.3, places=1)  # Linear interpolation
        self.assertAlmostEqual(interpolated.iloc[3], 0.4, places=1)

    def test_spatial_aggregation(self):
        """Test spatial aggregation of pixel data."""
        # Create a small grid of data
        grid_data = np.random.uniform(0.1, 0.4, (5, 10, 10))
        
        # Test mean aggregation over spatial dimensions
        spatial_mean = np.nanmean(grid_data, axis=(1, 2))
        
        self.assertEqual(len(spatial_mean), 5)  # Should have 5 time steps
        self.assertTrue(np.all(spatial_mean >= 0.1))
        self.assertTrue(np.all(spatial_mean <= 0.4))

    def test_coordinate_conversion(self):
        """Test coordinate system conversions."""
        # Test conversion between different coordinate systems
        lat_deg = 41.1649
        lon_deg = -96.4766
        
        # Convert to grid indices (simplified)
        lat_idx = int((lat_deg + 90) * 2)  # Assuming 0.5 degree resolution
        lon_idx = int((lon_deg + 180) * 2)
        
        # Convert back to degrees
        lat_converted = (lat_idx / 2) - 90
        lon_converted = (lon_idx / 2) - 180
        
        # Should be close to original coordinates
        self.assertAlmostEqual(lat_converted, lat_deg, places=0)
        self.assertAlmostEqual(lon_converted, lon_deg, places=0)


class TestDataProcessingPipeline(unittest.TestCase):
    """Test cases for the complete data processing pipeline."""

    def setUp(self):
        """Set up test fixtures."""
        self.loader = LPRMDataLoader()

    def test_complete_processing_pipeline(self):
        """Test the complete data processing pipeline."""
        # This would test the integration of all components
        target_lat, target_lon = 41.1649, -96.4766
        start_date = '2020-01-01'
        end_date = '2020-01-31'
        
        # Mock the entire pipeline
        with patch.object(self.loader, 'load_netcdf_file') as mock_load:
            mock_data = {
                'soil_moisture': np.random.uniform(0.1, 0.4, (31, 180, 360)),
                'latitude': np.linspace(-89.5, 89.5, 180),
                'longitude': np.linspace(-179.5, 179.5, 360),
                'time': pd.date_range(start_date, end_date, freq='D')
            }
            mock_load.return_value = mock_data
            
            # Process the data
            result = self.loader.process_location_data(
                '/fake/path/data.nc', target_lat, target_lon
            )
            
            self.assertIsInstance(result, dict)
            self.assertIn('time_series', result)
            self.assertIn('metadata', result)


if __name__ == "__main__":
    unittest.main()
