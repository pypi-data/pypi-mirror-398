"""
Utilities for working with AMSR2 LPRM (Land Parameter Retrieval Model) data.

This module provides functions and classes for extracting, processing, and managing
soil moisture data from AMSR2 LPRM NetCDF files.
"""

import logging
from pathlib import Path
from typing import Dict, Optional, Tuple, Union
import contextlib

import netCDF4 as nc
import numpy as np
import numpy.ma as ma

from ..utils.geo_utils import get_location


class LPRMDataLoader:
    """A class for loading and processing LPRM NetCDF data.
    
    This class provides methods to load NetCDF files, extract soil moisture data,
    and manage the data processing pipeline.
    """
    
    def __init__(self):
        """Initialize the LPRMDataLoader."""
        self.logger = logging.getLogger(__name__)
        
    def load_netcdf_file(self, file_path: Union[str, Path]) -> Dict[str, np.ndarray]:
        """Load a NetCDF file and return its contents as a dictionary.
        
        Args:
            file_path: Path to the NetCDF file
            
        Returns:
            Dictionary containing the file's variables as numpy arrays
            
        Raises:
            FileNotFoundError: If the specified file does not exist
            IOError: If there is an error reading the NetCDF file
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"NetCDF file not found: {file_path}")
            
        try:
            with nc.Dataset(file_path, 'r') as dataset:
                # Extract all variables
                data = {}
                for var_name, var in dataset.variables.items():
                    data[var_name] = var[:]
                return data
                
        except Exception as e:
            self.logger.error(f"Error reading NetCDF file {file_path}: {str(e)}")
            raise IOError(f"Failed to read NetCDF file: {file_path}") from e
            
    def find_nearest_valid_pixel(self, data: np.ndarray, row: int, col: int, 
                              search_radius: int = 3) -> Optional[np.ndarray]:
        """Find the nearest valid pixel in a 3D array (time, lat, lon).
        
        Uses Numba acceleration when available for 10-50x speedup on large arrays.
        
        Args:
            data: 3D numpy array with shape (time, lat, lon)
            row: Target row index
            col: Target column index
            search_radius: Maximum distance to search for valid pixels
            
        Returns:
            2D array of valid data at the nearest valid pixel, or None if none found
        """
        if not isinstance(data, np.ndarray) or data.ndim != 3:
            raise ValueError("Input data must be a 3D numpy array")
        
        # Try Numba-accelerated version first (10-50x speedup)
        try:
            from ..acceleration import find_nearest_valid_pixel_numba, NUMBA_AVAILABLE
            
            if NUMBA_AVAILABLE:
                found, time_series = find_nearest_valid_pixel_numba(data, row, col, search_radius)
                return time_series if found else None
        except ImportError:
            pass
            
        # Fallback to pure Python implementation  
        # Check if the target pixel is valid
        if not np.any(np.isnan(data[:, row, col])):
            return data[:, row, col]
            
        # Search in increasing radius around the target pixel
        rows, cols = data.shape[1], data.shape[2]
        
        for radius in range(1, search_radius + 1):
            # Define search window
            min_row, max_row = max(0, row - radius), min(rows - 1, row + radius)
            min_col, max_col = max(0, col - radius), min(cols - 1, col + radius)
            
            # Check all pixels in the window
            for r in range(min_row, max_row + 1):
                for c in range(min_col, max_col + 1):
                    # Skip the center pixel (already checked)
                    if r == row and c == col:
                        continue
                        
                    # Check if this pixel is valid
                    if not np.any(np.isnan(data[:, r, c])):
                        return data[:, r, c]
                        
        return None


def extract_pixel_data(
    data: np.ndarray,
    target_lat: float,
    target_lon: float,
    lat_grid: np.ndarray,
    lon_grid: np.ndarray,
) -> np.ndarray:
    """Extract time series data for a specific latitude/longitude from a 3D array.
    
    Args:
        data: 3D numpy array with shape (time, lat, lon)
        target_lat: Target latitude in degrees
        target_lon: Target longitude in degrees
        lat_grid: 1D array of latitude values
        lon_grid: 1D array of longitude values
        
    Returns:
        1D array of data values for the specified location across all time steps
        
    Raises:
        ValueError: If the target location is outside the grid or data is invalid
    """
    # Find the grid cell that contains our location
    try:
        lat_idx, lon_idx = get_location(target_lat, target_lon, lat_grid, lon_grid)
    except ValueError as e:
        raise ValueError(f"Could not find grid cell for location ({target_lat}, {target_lon}): {str(e)}")
    
    # Extract the time series for this location
    if data.ndim != 3:
        raise ValueError(f"Expected 3D data array, got {data.ndim}D")
        
    if lat_idx < 0 or lat_idx >= data.shape[1] or lon_idx < 0 or lon_idx >= data.shape[2]:
        raise ValueError(f"Grid indices ({lat_idx}, {lon_idx}) out of bounds for data shape {data.shape}")
    
    # Return the time series for this location
    return data[:, lat_idx, lon_idx]


def get_lprm_des(
    local_date: str,
    lat: float,
    lon: float,
    lat_grid: Optional[np.ndarray] = None,
    lon_grid: Optional[np.ndarray] = None,
    lprm_dir: Optional[Path] = None,
) -> float:
    """
    Extract soil moisture data from LPRM NetCDF files for a specific date and location.

    Args:
        local_date: Local date in 'YYYYMMDD' format
        lat: Latitude of the point
        lon: Longitude of the point
        lat_grid: 1D array of latitude values from the LPRM grid
        lon_grid: 1D array of longitude values from the LPRM grid
        lprm_dir: Directory containing LPRM NetCDF files

    Returns:
        float: Soil moisture value at the specified location and date, or NaN if not found
    """
    # Import here to avoid circular imports
    from ..common.config import ConfigManager

    # Get parameters if not provided
    if lat_grid is None or lon_grid is None or lprm_dir is None:
        params = ConfigManager.get_parameters()
        lat_grid = params.get("lat_lprm")
        lon_grid = params.get("lon_lprm")
        lprm_dir = params.get("lprm_des", Path())

    # Find the grid cell that contains our location
    if lat_grid is None or lon_grid is None:
        logging.error("Latitude/Longitude grid not available")
        return np.nan

    try:
        row, col = get_location(lat, lon, lat_grid, lon_grid)
    except Exception as e:
        logging.error(f"Error finding location in grid: {e}")
        return np.nan

    # Search for a file that matches our date
    for file_path in sorted(lprm_dir.glob("*.nc")):
        file_name = file_path.name

        # Check if the file exists and contains data for our date
        if not file_path.exists() or local_date not in file_name:
            continue

        try:
            # Open the NetCDF file
            with nc.Dataset(file_path, "r") as dataset:
                # Get the soil moisture data
                soil_moisture = dataset.variables["soil_moisture"][:]

                # Check if the data is valid
                if not np.ma.is_masked(soil_moisture[row, col]):
                    return float(soil_moisture[row, col])

                # If masked, try to find nearest valid value
                logging.debug(f"Masked value at ({row}, {col}) in {file_name}")
                return _find_nearest_valid(soil_moisture, row, col)

        except (IOError, KeyError, IndexError) as e:
            logging.error(f"Error reading {file_path}: {e}")
            continue
            try:
                # Check if the data is valid
                if not np.ma.is_masked(soil_moisture[row, col]):
                    return float(soil_moisture[row, col])

                # If masked, try to find nearest valid value
                logging.debug(f"Masked value at ({row}, {col}) in {file_name}")
                return _find_nearest_valid(soil_moisture, row, col)

            except (IOError, KeyError, IndexError) as e:
                logging.error(f"Error reading {file_path}: {e}")
                continue

    logging.warning(f"No LPRM data found for date {local_date}")
    return np.nan


def _find_nearest_valid(
    data: np.ma.MaskedArray, row: int, col: int, max_distance: int = 5
) -> float:
    """
    Find the nearest valid value in a 2D masked array.

    Args:
        data: 2D masked array of data
        row: Row index of the center point
        col: Column index of the center point
        max_distance: Maximum search distance (in grid cells)

    Returns:
        The nearest valid value, or NaN if none found
    """
    if not np.ma.is_masked(data[row, col]):
        return float(data[row, col])

    # Search in expanding squares around the point
    for distance in range(1, max_distance + 1):
        # Get the bounding box
        r_start = max(0, row - distance)
        r_end = min(data.shape[0], row + distance + 1)
        c_start = max(0, col - distance)
        c_end = min(data.shape[1], col + distance + 1)

        # Check all points at this distance
        for r in range(r_start, r_end):
            for c in [c_start, c_end - 1]:
                if not np.ma.is_masked(data[r, c]):
                    return float(data[r, c])

        for c in range(c_start + 1, c_end - 1):
            for r in [r_start, r_end - 1]:
                if not np.ma.is_masked(data[r, c]):
                    return float(data[r, c])

    # If we get here, no valid value was found
    return np.nan


def read_lprm_file(file_path: Path) -> Optional[dict]:
    """
    Read an LPRM NetCDF file and return its contents as a dictionary.

    Args:
        file_path: Path to the NetCDF file

    Returns:
        Dictionary containing the file contents, or None if an error occurs
    """
    try:
        with nc.Dataset(file_path, "r") as ds:
            result = {
                "lat": ds.variables["lat"][:],
                "lon": ds.variables["lon"][:],
                "soil_moisture": ds.variables["soil_moisture"][:],
                "time": ds.variables["time"][:],
                "metadata": {attr: getattr(ds, attr) for attr in ds.ncattrs()},
            }

            # Add additional variables if they exist
            for var in ["tb", "land_water_mask", "quality_flag"]:
                if var in ds.variables:
                    result[var] = ds.variables[var][:]

            return result

    except Exception as e:
        logging.error(f"Error reading {file_path}: {e}")
        return None
