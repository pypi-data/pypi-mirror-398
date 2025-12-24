"""
Data loading and processing module for soil moisture analysis.

This module provides functions for loading, processing, and preparing
soil moisture data from various sources.
"""

from .io import load_results, save_results

__all__ = ["load_results", "save_results"]
