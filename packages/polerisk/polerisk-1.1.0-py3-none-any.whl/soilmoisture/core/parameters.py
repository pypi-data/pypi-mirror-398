"""
Parameter handling for soil moisture analysis.

This module provides functions for managing configuration parameters and file paths
used throughout the soil moisture analysis pipeline.
"""

import logging
from pathlib import Path

from netCDF4 import Dataset


def get_parameters():
    """
    Get parameters and file paths for the soil moisture analysis.

    Returns:
        dict: Dictionary containing file paths and parameters

    Raises:
        FileNotFoundError: If required input files or directories are not found
    """
    base_path = Path(__file__).parent.parent.parent  # Get project root
    para = {}

    # Input/Output paths
    input_dir = base_path / "Input"
    output_dir = base_path / "Output"

    # Create output directory if it doesn't exist
    output_dir.mkdir(exist_ok=True)

    # Satellite data path - NetCDF files
    para["lprm_des"] = input_dir / "LPRM_NetCDF"
    para["lprm_des"].mkdir(parents=True, exist_ok=True)

    # Find all NetCDF files in the directory
    para["file_lprm_des"] = sorted(para["lprm_des"].glob("*.nc"))
    para["size_lprm_des"] = len(para["file_lprm_des"])

    # Check if we found any NetCDF files
    if para["size_lprm_des"] == 0:
        logging.warning(
            f"No NetCDF files found in {para['lprm_des']}. "
            "Please ensure your AMSR2 LPRM NetCDF files are in this directory."
        )
    else:
        logging.info(
            f"Found {para['size_lprm_des']} NetCDF files in {para['lprm_des']}"
        )

    # In-situ data path
    para["in_situ"] = (
        input_dir
        / "In-situ data"
        / "REMEDHUS_REMEDHUS_ElTomillar_sm_0.000000_0.050000_Stevens-Hydra-Probe_20150401_20150430.stm"
    )

    # NetCDF file with latitude/longitude data
    nc_file = input_dir / "LPRM-AMSR2_L3_D_SOILM3_V001_20150401013507.nc4"

    try:
        # Read latitude and longitude from the first NetCDF file if available
        if para["file_lprm_des"]:
            with Dataset(para["file_lprm_des"][0], "r") as ds:
                para["lat_lprm"] = ds.variables["lat"][:]
                para["lon_lprm"] = ds.variables["lon"][:]
        elif nc_file.exists():
            with Dataset(nc_file, "r") as ds:
                para["lat_lprm"] = ds.variables["lat"][:]
                para["lon_lprm"] = ds.variables["lon"][:]
        else:
            logging.warning("Could not find a NetCDF file to read lat/lon grid")
            para["lat_lprm"] = None
            para["lon_lprm"] = None
    except Exception as e:
        logging.error(f"Error reading NetCDF file: {e}")
        para["lat_lprm"] = None
        para["lon_lprm"] = None

    # Output directory for results
    para["out"] = output_dir

    return para
