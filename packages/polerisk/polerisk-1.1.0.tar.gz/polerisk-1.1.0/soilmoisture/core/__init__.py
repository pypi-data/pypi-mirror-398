"""
Core functionality for soil moisture analysis.

This module contains the core classes and functions for processing AMSR2 LPRM
soil moisture data and matching it with in-situ measurements.
"""

from .lprm_utils import _find_nearest_valid, get_lprm_des, read_lprm_file
from .matching import _log_processing_summary, match_insitu_with_lprm
from ..common.config import ConfigManager

# Provide backward compatibility
get_parameters = ConfigManager.get_parameters

__all__ = [
    "_find_nearest_valid",
    "_log_processing_summary",
    "get_lprm_des",
    "get_parameters",
    "match_insitu_with_lprm",
    "read_lprm_file",
]
