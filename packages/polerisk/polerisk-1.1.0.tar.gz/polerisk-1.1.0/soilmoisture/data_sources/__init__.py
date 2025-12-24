"""
Multi-satellite data source support for soil moisture analysis.

This module provides support for multiple satellite missions and data sources,
including SMAP, SMOS, ESA CCI, and enhanced AMSR2 LPRM processing.
"""

from .smap_processor import SMAPProcessor
from .smos_processor import SMOSProcessor
from .esa_cci_processor import ESACCIProcessor
from .multi_mission import MultiMissionProcessor, MissionComparator

__all__ = [
    "SMAPProcessor",
    "SMOSProcessor", 
    "ESACCIProcessor",
    "MultiMissionProcessor",
    "MissionComparator",
]
