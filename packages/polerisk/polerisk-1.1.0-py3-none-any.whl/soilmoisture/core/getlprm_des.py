import os
import numpy as np
import netCDF4 as nc
from .getlocation import get_location

import logging
logger = logging.getLogger(__name__)



def get_lprm_des(local_date, lat, lon):
    # Import here to avoid circular imports
    from ..common.config import ConfigManager

    # Get configuration parameters
    para = ConfigManager.get_parameters()

    # Find the grid cell that contains our location
    row, col = get_location(lat, lon, para["lat_lprm"], para["lon_lprm"])

    # Search for a file that matches our date
    for file_path in para["file_lprm_des"]:
        file_name = os.path.basename(file_path)

        # Check if this file contains data for our date
        if local_date in file_name:
            try:
                # Load the NetCDF file
                with nc.Dataset(file_path, "r") as ds:
                    # Get the soil moisture data
                    sm_data = ds.variables["soil_moisture"][:]
                    return float(sm_data[row, col])

            except (IOError, KeyError, IndexError) as e:
                logger.error(f"Error reading {file_path}: {str(e)}")
                return np.nan

    return np.nan
