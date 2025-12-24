"""
Visualization module for soil moisture analysis.

This module provides functions for creating various visualizations of soil moisture data,
including time series plots, spatial maps, and statistical visualizations.
"""

from .plots import (
    create_dashboard,
    plot_distributions,
    plot_scatter,
    plot_site_map,
    plot_time_series,
    plot_vegetation_terrain_analysis,
)

__all__ = [
    "plot_time_series",
    "plot_scatter",
    "plot_distributions",
    "plot_vegetation_terrain_analysis",
    "plot_site_map",
    "create_dashboard",
]
