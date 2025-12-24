"""Test configuration and fixtures for the soil moisture package tests."""

import tempfile
import pytest
import numpy as np
import pandas as pd
from pathlib import Path


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup is handled automatically by tempfile


@pytest.fixture
def sample_insitu_data():
    """Create sample in-situ soil moisture data for testing."""
    dates = pd.date_range('2020-01-01', '2020-01-31', freq='D')
    np.random.seed(42)  # For reproducible tests
    
    data = pd.DataFrame({
        'datetime': dates,
        'soil_moisture': np.random.uniform(0.1, 0.4, len(dates)),
        'temperature': np.random.uniform(15, 25, len(dates)),
        'humidity': np.random.uniform(40, 80, len(dates)),
        'site_id': 'US-Ne2',
        'lat': 41.1649,
        'lon': -96.4766
    })
    
    return data


@pytest.fixture
def sample_satellite_data():
    """Create sample satellite soil moisture data for testing."""
    dates = pd.date_range('2020-01-01', '2020-01-31', freq='D')
    np.random.seed(43)  # Different seed for satellite data
    
    # Create satellite data with some correlation to in-situ but with bias
    satellite_values = np.random.uniform(0.05, 0.35, len(dates))
    
    return pd.Series(satellite_values, index=dates)


@pytest.fixture
def sample_matched_data():
    """Create sample matched in-situ and satellite data for testing."""
    dates = pd.date_range('2020-01-01', '2020-01-31', freq='D')
    np.random.seed(42)
    
    # Create correlated data
    base_values = np.random.uniform(0.1, 0.4, len(dates))
    noise = np.random.normal(0, 0.02, len(dates))
    
    data = pd.DataFrame({
        'in_situ': base_values,
        'satellite': base_values + noise + 0.01,  # Small bias
        'lat': 41.1649,
        'lon': -96.4766
    }, index=dates)
    
    return data


@pytest.fixture
def sample_config():
    """Create sample configuration parameters for testing."""
    return {
        'data_dir': '/path/to/data',
        'output_dir': '/path/to/output',
        'start_date': '2020-01-01',
        'end_date': '2020-01-31',
        'site_lat': 41.1649,
        'site_lon': -96.4766,
        'time_window_hours': 3,
        'quality_control': {
            'min_soil_moisture': 0.0,
            'max_soil_moisture': 1.0,
            'outlier_threshold': 3.0
        }
    }


@pytest.fixture
def sample_netcdf_data():
    """Create sample NetCDF-like data structure for testing."""
    # Create grid coordinates
    lat_grid = np.linspace(-89.5, 89.5, 180)  # 1 degree resolution
    lon_grid = np.linspace(-179.5, 179.5, 360)  # 1 degree resolution
    time_steps = 31  # January 2020
    
    # Create 3D soil moisture data
    np.random.seed(44)
    soil_moisture = np.random.uniform(0.05, 0.45, (time_steps, len(lat_grid), len(lon_grid)))
    
    # Add some missing data
    soil_moisture[soil_moisture < 0.1] = np.nan
    
    data = {
        'soil_moisture': soil_moisture,
        'latitude': lat_grid,
        'longitude': lon_grid,
        'time': pd.date_range('2020-01-01', '2020-01-31', freq='D')
    }
    
    return data


@pytest.fixture
def sample_files(temp_dir, sample_insitu_data):
    """Create sample data files for testing."""
    data_dir = Path(temp_dir) / 'data'
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Create in-situ data file
    insitu_file = data_dir / 'insitu_data.csv'
    sample_insitu_data.to_csv(insitu_file, index=False)
    
    # Create satellite data file (mock)
    satellite_file = data_dir / 'satellite_data.nc'
    satellite_file.touch()  # Create empty file for testing
    
    return {
        'insitu_file': str(insitu_file),
        'satellite_file': str(satellite_file),
        'data_dir': str(data_dir)
    }


@pytest.fixture
def quality_control_data():
    """Create data with quality control issues for testing."""
    dates = pd.date_range('2020-01-01', '2020-01-20', freq='D')
    
    # Create data with various quality issues
    soil_moisture_values = [
        0.1, 0.2, 0.3, 0.4, 0.5,  # Normal values
        -0.1, 1.5, 2.0,           # Out of range values
        np.nan, np.nan,           # Missing values
        0.15, 0.25, 0.35,         # Normal values
        10.0, -5.0,               # Extreme outliers
        0.2, 0.3, 0.4, 0.5, 0.6   # Normal values
    ]
    
    data = pd.DataFrame({
        'datetime': dates,
        'soil_moisture': soil_moisture_values,
        'temperature': np.random.uniform(15, 25, len(dates)),
        'site_id': 'TEST'
    })
    
    return data


@pytest.fixture
def seasonal_data():
    """Create data with seasonal patterns for testing."""
    dates = pd.date_range('2020-01-01', '2020-12-31', freq='D')
    
    # Create seasonal pattern
    day_of_year = dates.dayofyear
    seasonal_pattern = 0.3 + 0.1 * np.sin(2 * np.pi * day_of_year / 365.25)
    
    # Add noise
    np.random.seed(45)
    noise = np.random.normal(0, 0.02, len(dates))
    
    data = pd.DataFrame({
        'date': dates,
        'soil_moisture': seasonal_pattern + noise,
        'month': dates.month,
        'season': dates.quarter
    })
    data.set_index('date', inplace=True)
    
    return data


@pytest.fixture
def performance_data():
    """Create large dataset for performance testing."""
    # Create 5 years of hourly data
    dates = pd.date_range('2018-01-01', '2022-12-31', freq='H')
    np.random.seed(46)
    
    # This creates a large dataset (~44,000 records)
    data = pd.DataFrame({
        'datetime': dates,
        'soil_moisture': np.random.uniform(0.1, 0.4, len(dates)),
        'temperature': np.random.uniform(-10, 35, len(dates)),
        'site_id': 'PERF_TEST'
    })
    
    return data


# Test configuration constants
TEST_COORDINATES = {
    'US_NE2': {'lat': 41.1649, 'lon': -96.4766, 'name': 'Mead, Nebraska'},
    'INVALID': {'lat': 100.0, 'lon': 200.0, 'name': 'Invalid coordinates'},
    'OCEAN': {'lat': 0.0, 'lon': 0.0, 'name': 'Ocean point'}
}

TEST_DATE_RANGES = {
    'SHORT': {'start': '2020-01-01', 'end': '2020-01-31'},
    'MEDIUM': {'start': '2020-01-01', 'end': '2020-06-30'},
    'LONG': {'start': '2018-01-01', 'end': '2022-12-31'},
    'INVALID': {'start': '2020-12-31', 'end': '2020-01-01'}  # End before start
}

# Test data quality thresholds
QUALITY_THRESHOLDS = {
    'soil_moisture': {'min': 0.0, 'max': 1.0},
    'temperature': {'min': -50.0, 'max': 60.0},
    'correlation': {'min_acceptable': 0.3},
    'rmse': {'max_acceptable': 0.2}
}


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )


def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on their location and name."""
    for item in items:
        # Mark integration tests
        if "test_integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        
        # Mark performance tests
        if "performance" in item.name.lower() or "large" in item.name.lower():
            item.add_marker(pytest.mark.performance)
            item.add_marker(pytest.mark.slow)
        
        # Mark unit tests (everything else)
        if not any(marker.name in ['integration', 'performance'] 
                  for marker in item.iter_markers()):
            item.add_marker(pytest.mark.unit)
