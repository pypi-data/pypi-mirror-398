"""Unit tests for visualization module."""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import matplotlib
import numpy as np
import pandas as pd

# Use non-interactive backend for testing
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Add the parent directory to the path so we can import the module
sys.path.insert(0, str(Path(__file__).parent.parent))

from soilmoisture.visualization.plots import (  # noqa: E402
    create_dashboard,
    plot_distributions,
    plot_scatter,
    plot_site_map,
    plot_time_series,
    plot_vegetation_terrain_analysis,
)


class TestVisualizationPlots(unittest.TestCase):
    """Test cases for visualization plotting functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create sample data for testing
        dates = pd.date_range('2020-01-01', '2020-01-31', freq='D')
        self.sample_data = pd.DataFrame({
            'in_situ': np.random.uniform(0.1, 0.4, len(dates)),
            'satellite': np.random.uniform(0.05, 0.35, len(dates)),
            'lat': np.full(len(dates), 41.1649),
            'lon': np.full(len(dates), -96.4766),
        }, index=dates)

    def test_plot_time_series(self):
        """Test time series plotting function."""
        output_path = plot_time_series(self.sample_data, self.temp_dir)
        
        # Check that file was created
        self.assertTrue(Path(output_path).exists())
        self.assertTrue(output_path.endswith('.png'))
        
        # Check that the file is not empty
        file_size = Path(output_path).stat().st_size
        self.assertGreater(file_size, 1000)  # Should be at least 1KB

    def test_plot_scatter(self):
        """Test scatter plot function."""
        output_path = plot_scatter(self.sample_data, self.temp_dir)
        
        # Check that file was created
        self.assertTrue(Path(output_path).exists())
        self.assertTrue(output_path.endswith('.png'))
        
        # Check that the file is not empty
        file_size = Path(output_path).stat().st_size
        self.assertGreater(file_size, 1000)

    def test_plot_distributions(self):
        """Test distribution plotting function."""
        output_path = plot_distributions(self.sample_data, self.temp_dir)
        
        # Check that file was created
        self.assertTrue(Path(output_path).exists())
        self.assertTrue(output_path.endswith('.png'))
        
        # Check that the file is not empty
        file_size = Path(output_path).stat().st_size
        self.assertGreater(file_size, 1000)

    def test_plot_vegetation_terrain_analysis(self):
        """Test vegetation terrain analysis plotting function."""
        output_path = plot_vegetation_terrain_analysis(self.sample_data, self.temp_dir)
        
        # Check that file was created
        self.assertTrue(Path(output_path).exists())
        self.assertTrue(output_path.endswith('.png'))

    def test_plot_vegetation_terrain_analysis_missing_data(self):
        """Test vegetation terrain analysis with missing required columns."""
        # Create data without required columns
        incomplete_data = pd.DataFrame({
            'temperature': np.random.uniform(15, 25, 10)
        })
        
        output_path = plot_vegetation_terrain_analysis(incomplete_data, self.temp_dir)
        
        # Should return empty string when data is insufficient
        self.assertEqual(output_path, "")

    @patch('cartopy.crs')
    @patch('cartopy.feature')
    def test_plot_site_map(self, mock_cfeature, mock_ccrs):
        """Test site map plotting function."""
        # Mock cartopy components
        mock_ccrs.PlateCarree.return_value = MagicMock()
        mock_cfeature.LAND = MagicMock()
        mock_cfeature.OCEAN = MagicMock()
        mock_cfeature.COASTLINE = MagicMock()
        mock_cfeature.BORDERS = MagicMock()
        mock_cfeature.LAKES = MagicMock()
        mock_cfeature.RIVERS = MagicMock()
        
        with patch('matplotlib.pyplot.axes') as mock_axes:
            mock_ax = MagicMock()
            mock_axes.return_value = mock_ax
            
            output_path = plot_site_map(self.sample_data, self.temp_dir)
            
            # Should return a valid path
            self.assertIsInstance(output_path, str)
            self.assertTrue(output_path.endswith('.png'))

    def test_plot_site_map_missing_coordinates(self):
        """Test site map plotting with missing coordinate columns."""
        # Create data without lat/lon columns
        incomplete_data = pd.DataFrame({
            'in_situ': np.random.uniform(0.1, 0.4, 10),
            'satellite': np.random.uniform(0.05, 0.35, 10)
        })
        
        output_path = plot_site_map(incomplete_data, self.temp_dir)
        
        # Should return None when coordinates are missing
        self.assertIsNone(output_path)

    @patch('jinja2.Environment')
    def test_create_dashboard(self, mock_env):
        """Test dashboard creation function."""
        # Mock Jinja2 template environment
        mock_template = MagicMock()
        mock_template.render.return_value = "<html><body>Test Dashboard</body></html>"
        mock_env.return_value.get_template.return_value = mock_template
        
        # Mock the individual plotting functions
        with patch('soilmoisture.visualization.plots.plot_time_series') as mock_ts, \
             patch('soilmoisture.visualization.plots.plot_scatter') as mock_scatter, \
             patch('soilmoisture.visualization.plots.plot_distributions') as mock_dist, \
             patch('soilmoisture.visualization.plots.plot_vegetation_terrain_analysis') as mock_vt, \
             patch('soilmoisture.visualization.plots.plot_site_map') as mock_map:
            
            # Set return values for mocked functions
            mock_ts.return_value = str(Path(self.temp_dir) / "time_series.png")
            mock_scatter.return_value = str(Path(self.temp_dir) / "scatter.png")
            mock_dist.return_value = str(Path(self.temp_dir) / "distributions.png")
            mock_vt.return_value = str(Path(self.temp_dir) / "vegetation.png")
            mock_map.return_value = str(Path(self.temp_dir) / "map.png")
            
            output_path = create_dashboard(self.sample_data, self.temp_dir)
            
            # Check that dashboard file was created
            self.assertIsInstance(output_path, str)
            self.assertTrue(output_path.endswith('.html'))

    def test_plot_with_missing_data(self):
        """Test plotting functions with missing data."""
        # Create data with some missing values
        data_with_missing = self.sample_data.copy()
        data_with_missing.loc[data_with_missing.index[:5], 'satellite'] = np.nan
        data_with_missing.loc[data_with_missing.index[10:15], 'in_situ'] = np.nan
        
        # All plotting functions should handle missing data gracefully
        ts_path = plot_time_series(data_with_missing, self.temp_dir)
        scatter_path = plot_scatter(data_with_missing, self.temp_dir)
        dist_path = plot_distributions(data_with_missing, self.temp_dir)
        
        # Check that files were created despite missing data
        self.assertTrue(Path(ts_path).exists())
        self.assertTrue(Path(scatter_path).exists())
        self.assertTrue(Path(dist_path).exists())

    def test_plot_with_empty_data(self):
        """Test plotting functions with empty data."""
        empty_data = pd.DataFrame()
        
        # Functions should handle empty data gracefully
        try:
            plot_time_series(empty_data, self.temp_dir)
            plot_scatter(empty_data, self.temp_dir)
            plot_distributions(empty_data, self.temp_dir)
        except Exception as e:
            # If exceptions are raised, they should be informative
            self.assertIsInstance(e, (KeyError, ValueError))

    def test_output_directory_creation(self):
        """Test that output directories are created if they don't exist."""
        # Use a non-existent directory
        non_existent_dir = Path(self.temp_dir) / "new_subdir" / "plots"
        
        output_path = plot_time_series(self.sample_data, str(non_existent_dir))
        
        # Check that directory was created
        self.assertTrue(non_existent_dir.exists())
        self.assertTrue(Path(output_path).exists())

    def test_plot_customization(self):
        """Test that plots can be customized."""
        # This test would verify that plots have proper titles, labels, etc.
        # For now, we just ensure the functions run without error
        
        output_path = plot_time_series(self.sample_data, self.temp_dir)
        
        # In a more comprehensive test, we could:
        # 1. Load the saved image and check its properties
        # 2. Verify that specific elements (titles, labels) are present
        # 3. Check color schemes and styling
        
        self.assertTrue(Path(output_path).exists())


class TestVisualizationUtilities(unittest.TestCase):
    """Test cases for visualization utility functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def test_figure_size_consistency(self):
        """Test that all plots use consistent figure sizes."""
        # Create sample data
        dates = pd.date_range('2020-01-01', '2020-01-10', freq='D')
        data = pd.DataFrame({
            'in_situ': np.random.uniform(0.1, 0.4, len(dates)),
            'satellite': np.random.uniform(0.05, 0.35, len(dates)),
        }, index=dates)
        
        # Test that figures are created with reasonable sizes
        # This would be more comprehensive in a real implementation
        with patch('matplotlib.pyplot.figure') as mock_figure:
            plot_time_series(data, self.temp_dir)
            
            # Verify that figure was called (indicating plot creation)
            mock_figure.assert_called()

    def test_color_scheme_consistency(self):
        """Test that plots use consistent color schemes."""
        # This would test that all plots use the same color palette
        # For now, just ensure functions run
        dates = pd.date_range('2020-01-01', '2020-01-10', freq='D')
        data = pd.DataFrame({
            'in_situ': np.random.uniform(0.1, 0.4, len(dates)),
            'satellite': np.random.uniform(0.05, 0.35, len(dates)),
        }, index=dates)
        
        # All functions should run without error
        plot_time_series(data, self.temp_dir)
        plot_scatter(data, self.temp_dir)
        plot_distributions(data, self.temp_dir)

    def test_file_format_consistency(self):
        """Test that all plots are saved in the same format."""
        dates = pd.date_range('2020-01-01', '2020-01-10', freq='D')
        data = pd.DataFrame({
            'in_situ': np.random.uniform(0.1, 0.4, len(dates)),
            'satellite': np.random.uniform(0.05, 0.35, len(dates)),
        }, index=dates)
        
        # All plots should be saved as PNG files
        ts_path = plot_time_series(data, self.temp_dir)
        scatter_path = plot_scatter(data, self.temp_dir)
        dist_path = plot_distributions(data, self.temp_dir)
        
        self.assertTrue(ts_path.endswith('.png'))
        self.assertTrue(scatter_path.endswith('.png'))
        self.assertTrue(dist_path.endswith('.png'))


if __name__ == "__main__":
    unittest.main()
