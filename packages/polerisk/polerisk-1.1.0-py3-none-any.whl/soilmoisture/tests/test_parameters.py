"""Unit tests for parameters module."""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

# Add the parent directory to the path so we can import the module
sys.path.insert(0, str(Path(__file__).parent.parent))

from soilmoisture.core.parameters import ParameterManager  # noqa: E402


class TestParameterManager(unittest.TestCase):
    """Test cases for ParameterManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.param_manager = ParameterManager()

    def test_default_parameters(self):
        """Test that default parameters are loaded correctly."""
        params = self.param_manager.get_default_parameters()
        
        # Check that all required keys are present
        required_keys = [
            'data_dir', 'output_dir', 'start_date', 'end_date',
            'site_lat', 'site_lon', 'time_window_hours'
        ]
        for key in required_keys:
            self.assertIn(key, params)
        
        # Check data types
        self.assertIsInstance(params['site_lat'], (int, float))
        self.assertIsInstance(params['site_lon'], (int, float))
        self.assertIsInstance(params['time_window_hours'], (int, float))

    def test_validate_parameters_valid(self):
        """Test parameter validation with valid parameters."""
        valid_params = {
            'data_dir': '/path/to/data',
            'output_dir': '/path/to/output',
            'start_date': '2020-01-01',
            'end_date': '2020-12-31',
            'site_lat': 41.1649,
            'site_lon': -96.4766,
            'time_window_hours': 3
        }
        
        # Should not raise any exception
        self.param_manager.validate_parameters(valid_params)

    def test_validate_parameters_invalid_lat(self):
        """Test parameter validation with invalid latitude."""
        invalid_params = {
            'data_dir': '/path/to/data',
            'output_dir': '/path/to/output',
            'start_date': '2020-01-01',
            'end_date': '2020-12-31',
            'site_lat': 100.0,  # Invalid latitude
            'site_lon': -96.4766,
            'time_window_hours': 3
        }
        
        with self.assertRaises(ValueError):
            self.param_manager.validate_parameters(invalid_params)

    def test_validate_parameters_invalid_lon(self):
        """Test parameter validation with invalid longitude."""
        invalid_params = {
            'data_dir': '/path/to/data',
            'output_dir': '/path/to/output',
            'start_date': '2020-01-01',
            'end_date': '2020-12-31',
            'site_lat': 41.1649,
            'site_lon': 200.0,  # Invalid longitude
            'time_window_hours': 3
        }
        
        with self.assertRaises(ValueError):
            self.param_manager.validate_parameters(invalid_params)

    def test_validate_parameters_missing_key(self):
        """Test parameter validation with missing required key."""
        incomplete_params = {
            'data_dir': '/path/to/data',
            'output_dir': '/path/to/output',
            # Missing start_date, end_date, etc.
        }
        
        with self.assertRaises(KeyError):
            self.param_manager.validate_parameters(incomplete_params)

    def test_load_from_file_json(self):
        """Test loading parameters from JSON file."""
        # Create a temporary JSON file
        json_file = Path(self.temp_dir) / "test_params.json"
        json_content = '''
        {
            "data_dir": "/test/data",
            "output_dir": "/test/output",
            "start_date": "2020-01-01",
            "end_date": "2020-12-31",
            "site_lat": 41.1649,
            "site_lon": -96.4766,
            "time_window_hours": 3
        }
        '''
        json_file.write_text(json_content)
        
        params = self.param_manager.load_from_file(str(json_file))
        self.assertEqual(params['data_dir'], '/test/data')
        self.assertEqual(params['site_lat'], 41.1649)

    def test_save_to_file_json(self):
        """Test saving parameters to JSON file."""
        params = {
            'data_dir': '/test/data',
            'output_dir': '/test/output',
            'start_date': '2020-01-01',
            'end_date': '2020-12-31',
            'site_lat': 41.1649,
            'site_lon': -96.4766,
            'time_window_hours': 3
        }
        
        json_file = Path(self.temp_dir) / "saved_params.json"
        self.param_manager.save_to_file(params, str(json_file))
        
        # Verify file was created and contains correct data
        self.assertTrue(json_file.exists())
        loaded_params = self.param_manager.load_from_file(str(json_file))
        self.assertEqual(loaded_params['data_dir'], '/test/data')


if __name__ == "__main__":
    unittest.main()
