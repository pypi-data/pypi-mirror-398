import numpy as np


def get_location(lat, lon, lat_grid, lon_grid):
    """
    Find the row and column in the LPRM grid that's closest to the given lat/lon.

    Args:
        lat (float): Latitude of the point
        lon (float): Longitude of the point
        lat_grid (ndarray): 1D array of latitude values
        lon_grid (ndarray): 1D array of longitude values

    Returns:
        tuple: (row, col) indices in the LPRM grid
    """
    # Find closest latitude
    lat_distances = np.abs(lat_grid - lat)
    row = np.argmin(lat_distances)

    # Handle longitude wrap-around (e.g., -180 to 180 or 0 to 360)
    lon_diff = np.abs(lon_grid - lon)
    lon_diff = np.minimum(lon_diff, 360 - lon_diff)  # Handle wrap-around

    # Find closest longitude
    col = np.argmin(lon_diff)

    return row, col
