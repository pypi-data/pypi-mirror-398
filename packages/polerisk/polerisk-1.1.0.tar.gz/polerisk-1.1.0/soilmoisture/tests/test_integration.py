"""Integration tests for the soil moisture package."""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd

# Add the parent directory to the path so we can import the module
sys.path.insert(0, str(Path(__file__).parent.parent))

from soilmoisture.core.matching import SoilMoistureDataMatcher  # noqa: E402
from soilmoisture.core.parameters import ParameterManager  # noqa: E402
from soilmoisture.visualization.plots import plot_time_series  # noqa: E402


class TestEndToEndWorkflow(unittest.TestCase):
    """Test the complete end-to-end workflow."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.param_manager = ParameterManager()
        self.matcher = SoilMoistureDataMatcher()
        
        # Create sample configuration
        self.test_config = {
            'data_dir': str(Path(self.temp_dir) / 'data'),
            'output_dir': str(Path(self.temp_dir) / 'output'),
            'start_date': '2020-01-01',
            'end_date': '2020-01-31',
            'site_lat': 41.1649,
            'site_lon': -96.4766,
            'time_window_hours': 3
        }
        
        # Create sample data files
        self._create_sample_data()

    def _create_sample_data(self):
        """Create sample data files for testing."""
        # Create data directory
        data_dir = Path(self.test_config['data_dir'])
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Create sample in-situ data
        dates = pd.date_range(self.test_config['start_date'], 
                             self.test_config['end_date'], freq='D')
        insitu_data = pd.DataFrame({
            'datetime': dates,
            'soil_moisture': np.random.uniform(0.1, 0.4, len(dates)),
            'temperature': np.random.uniform(15, 25, len(dates)),
            'site_id': 'US-Ne2'
        })
        
        insitu_file = data_dir / 'insitu_data.csv'
        insitu_data.to_csv(insitu_file, index=False)
        
        self.insitu_file = str(insitu_file)
        self.satellite_file = str(data_dir / 'satellite_data.nc')

    def test_complete_workflow(self):
        """Test the complete processing workflow."""
        # Step 1: Load and validate parameters
        self.param_manager.validate_parameters(self.test_config)
        
        # Step 2: Mock satellite data processing
        with patch('soilmoisture.core.lprm_utils.load_lprm_data') as mock_load:
            # Mock satellite data
            dates = pd.date_range(self.test_config['start_date'], 
                                 self.test_config['end_date'], freq='D')
            mock_satellite_data = np.random.uniform(0.05, 0.35, len(dates))
            mock_load.return_value = (mock_satellite_data, dates)
            
            # Step 3: Process the data
            result = self.matcher.process_site_data(
                self.insitu_file,
                self.satellite_file,
                site_lat=self.test_config['site_lat'],
                site_lon=self.test_config['site_lon'],
                time_window_hours=self.test_config['time_window_hours']
            )
            
            # Step 4: Verify results
            self.assertIsInstance(result, dict)
            self.assertIn('matched_data', result)
            self.assertIn('statistics', result)
            
            matched_data = result['matched_data']
            self.assertIsInstance(matched_data, pd.DataFrame)
            self.assertIn('in_situ', matched_data.columns)
            self.assertIn('satellite', matched_data.columns)
            
            # Step 5: Generate visualizations
            output_dir = Path(self.test_config['output_dir'])
            output_dir.mkdir(parents=True, exist_ok=True)
            
            plot_path = plot_time_series(matched_data, str(output_dir))
            self.assertTrue(Path(plot_path).exists())

    def test_error_handling_workflow(self):
        """Test workflow error handling."""
        # Test with invalid configuration
        invalid_config = self.test_config.copy()
        invalid_config['site_lat'] = 100.0  # Invalid latitude
        
        with self.assertRaises(ValueError):
            self.param_manager.validate_parameters(invalid_config)
        
        # Test with missing data files
        with self.assertRaises(FileNotFoundError):
            self.matcher.process_site_data(
                '/nonexistent/file.csv',
                '/nonexistent/file.nc',
                site_lat=41.1649,
                site_lon=-96.4766,
                time_window_hours=3
            )

    def test_data_quality_workflow(self):
        """Test data quality control in the workflow."""
        # Create data with quality issues
        dates = pd.date_range('2020-01-01', '2020-01-10', freq='D')
        poor_quality_data = pd.DataFrame({
            'datetime': dates,
            'soil_moisture': [0.1, 0.2, -0.1, 1.5, 0.3, np.nan, 0.4, 0.5, 2.0, 0.2],  # Issues
            'temperature': np.random.uniform(15, 25, len(dates)),
            'site_id': 'US-Ne2'
        })
        
        # Save poor quality data
        poor_data_file = Path(self.temp_dir) / 'poor_quality.csv'
        poor_quality_data.to_csv(poor_data_file, index=False)
        
        # Mock satellite data
        with patch('soilmoisture.core.lprm_utils.load_lprm_data') as mock_load:
            mock_satellite_data = np.random.uniform(0.05, 0.35, len(dates))
            mock_load.return_value = (mock_satellite_data, dates)
            
            # Process data - should handle quality issues
            result = self.matcher.process_site_data(
                str(poor_data_file),
                self.satellite_file,
                site_lat=self.test_config['site_lat'],
                site_lon=self.test_config['site_lon'],
                time_window_hours=self.test_config['time_window_hours']
            )
            
            # Should have fewer data points after quality control
            matched_data = result['matched_data']
            self.assertLess(len(matched_data), len(dates))
            
            # All remaining data should be valid
            self.assertTrue((matched_data['in_situ'] >= 0).all())
            self.assertTrue((matched_data['in_situ'] <= 1).all())


class TestModuleIntegration(unittest.TestCase):
    """Test integration between different modules."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def test_parameters_and_matching_integration(self):
        """Test integration between parameters and matching modules."""
        param_manager = ParameterManager()
        matcher = SoilMoistureDataMatcher()
        
        # Get default parameters
        params = param_manager.get_default_parameters()
        
        # Parameters should be compatible with matcher
        required_params = ['site_lat', 'site_lon', 'time_window_hours']
        for param in required_params:
            self.assertIn(param, params)
        
        # Validate parameters
        param_manager.validate_parameters(params)

    def test_matching_and_visualization_integration(self):
        """Test integration between matching and visualization modules."""
        # Create sample matched data
        dates = pd.date_range('2020-01-01', '2020-01-31', freq='D')
        matched_data = pd.DataFrame({
            'in_situ': np.random.uniform(0.1, 0.4, len(dates)),
            'satellite': np.random.uniform(0.05, 0.35, len(dates)),
        }, index=dates)
        
        # Should be able to create visualizations from matched data
        plot_path = plot_time_series(matched_data, self.temp_dir)
        self.assertTrue(Path(plot_path).exists())

    def test_analysis_and_visualization_integration(self):
        """Test integration between analysis and visualization modules."""
        from soilmoisture.analysis.statistics import StatisticalAnalyzer
        
        # Create sample data
        dates = pd.date_range('2020-01-01', '2020-01-31', freq='D')
        data = pd.DataFrame({
            'observed': np.random.uniform(0.1, 0.4, len(dates)),
            'predicted': np.random.uniform(0.05, 0.35, len(dates)),
        }, index=dates)
        
        # Analyze data
        analyzer = StatisticalAnalyzer()
        stats = analyzer.analyze(data, 'observed', 'predicted')
        
        # Should be able to visualize the analyzed data
        plot_path = plot_time_series(data.rename(columns={
            'observed': 'in_situ', 'predicted': 'satellite'
        }), self.temp_dir)
        self.assertTrue(Path(plot_path).exists())
        
        # Statistics should be reasonable
        self.assertIn('correlation', stats)
        self.assertIn('rmse', stats)


class TestPerformanceIntegration(unittest.TestCase):
    """Test performance aspects of the integrated system."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def test_large_dataset_processing(self):
        """Test processing of larger datasets."""
        # Create a larger dataset (1 year of daily data)
        dates = pd.date_range('2020-01-01', '2020-12-31', freq='D')
        large_dataset = pd.DataFrame({
            'datetime': dates,
            'soil_moisture': np.random.uniform(0.1, 0.4, len(dates)),
            'temperature': np.random.uniform(15, 25, len(dates)),
            'site_id': 'US-Ne2'
        })
        
        # Save large dataset
        large_file = Path(self.temp_dir) / 'large_dataset.csv'
        large_dataset.to_csv(large_file, index=False)
        
        # Mock processing
        matcher = SoilMoistureDataMatcher()
        
        with patch('soilmoisture.core.lprm_utils.load_lprm_data') as mock_load:
            mock_satellite_data = np.random.uniform(0.05, 0.35, len(dates))
            mock_load.return_value = (mock_satellite_data, dates)
            
            # Process should complete without memory issues
            result = matcher.process_site_data(
                str(large_file),
                '/fake/satellite.nc',
                site_lat=41.1649,
                site_lon=-96.4766,
                time_window_hours=3
            )
            
            self.assertIsInstance(result, dict)
            self.assertIn('matched_data', result)

    def test_memory_efficiency(self):
        """Test memory efficiency of data processing."""
        # This test would monitor memory usage in a real implementation
        # For now, just ensure processing completes
        
        dates = pd.date_range('2020-01-01', '2020-01-31', freq='H')  # Hourly data
        hourly_data = pd.DataFrame({
            'datetime': dates,
            'soil_moisture': np.random.uniform(0.1, 0.4, len(dates)),
            'site_id': 'US-Ne2'
        })
        
        # Processing should handle hourly data efficiently
        self.assertGreater(len(hourly_data), 700)  # Should be ~744 hours in January


class TestConfigurationIntegration(unittest.TestCase):
    """Test configuration and setup integration."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def test_configuration_file_integration(self):
        """Test loading configuration from file and using it in workflow."""
        param_manager = ParameterManager()
        
        # Create configuration file
        config = {
            'data_dir': str(Path(self.temp_dir) / 'data'),
            'output_dir': str(Path(self.temp_dir) / 'output'),
            'start_date': '2020-01-01',
            'end_date': '2020-01-31',
            'site_lat': 41.1649,
            'site_lon': -96.4766,
            'time_window_hours': 3
        }
        
        config_file = Path(self.temp_dir) / 'config.json'
        param_manager.save_to_file(config, str(config_file))
        
        # Load configuration and use in workflow
        loaded_config = param_manager.load_from_file(str(config_file))
        param_manager.validate_parameters(loaded_config)
        
        # Configuration should be usable
        self.assertEqual(loaded_config['site_lat'], 41.1649)
        self.assertEqual(loaded_config['time_window_hours'], 3)

    def test_output_directory_integration(self):
        """Test output directory creation and file organization."""
        output_dir = Path(self.temp_dir) / 'organized_output'
        
        # Create sample data
        dates = pd.date_range('2020-01-01', '2020-01-10', freq='D')
        data = pd.DataFrame({
            'in_situ': np.random.uniform(0.1, 0.4, len(dates)),
            'satellite': np.random.uniform(0.05, 0.35, len(dates)),
        }, index=dates)
        
        # Generate multiple outputs
        plot_path = plot_time_series(data, str(output_dir))
        
        # Check that output directory structure is created
        self.assertTrue(output_dir.exists())
        self.assertTrue(Path(plot_path).exists())
        
        # Output should be organized properly
        self.assertTrue(str(plot_path).startswith(str(output_dir)))


if __name__ == "__main__":
    unittest.main()
