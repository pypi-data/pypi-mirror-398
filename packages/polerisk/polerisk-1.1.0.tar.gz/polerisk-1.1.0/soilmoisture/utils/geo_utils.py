"""
Geospatial utility functions.

This module provides functions for geospatial operations used in the soil moisture
analysis, including coordinate transformations and grid operations.
"""

import numpy as np


def get_location(lat, lon, lat_grid, lon_grid):
    """
    Find the row and column in the LPRM grid that's closest to the given lat/lon.
    
    Uses Numba acceleration when available for 3-10x speedup on large grids.

    Args:
        lat (float): Latitude of the point
        lon (float): Longitude of the point
        lat_grid (ndarray): 1D array of latitude values
        lon_grid (ndarray): 1D array of longitude values

    Returns:
        tuple: (row, col) indices in the LPRM grid
    """
    # Try Numba-accelerated version first (3-10x speedup)
    try:
        from ..acceleration import find_nearest_grid_point_numba, NUMBA_AVAILABLE
        
        if NUMBA_AVAILABLE:
            lat_idx, lon_idx, distance = find_nearest_grid_point_numba(
                lat, lon, lat_grid, lon_grid
            )
            return lat_idx, lon_idx
    except ImportError:
        pass
        
    # Fallback to pure Python implementation
    # Find closest latitude
    lat_distances = np.abs(lat_grid - lat)
    row = np.argmin(lat_distances)

    # Handle longitude wrap-around (e.g., -180 to 180 or 0 to 360)
    lon_diff = np.abs(lon_grid - lon)
    lon_diff = np.minimum(lon_diff, 360 - lon_diff)  # Handle wrap-around

    # Find closest longitude
    col = np.argmin(lon_diff)

    return row, col
