"""
Analysis module for soil moisture data.

This module contains functions for statistical analysis and data processing
of soil moisture measurements, with performance-critical functions implemented in Rust.
"""

from .statistics import (
    calculate_rmse,
    calculate_correlation,
    calculate_mae,
    calculate_bias,
    calculate_ubrmse,
    RUST_AVAILABLE
)

__all__ = [
    'calculate_rmse',
    'calculate_correlation',
    'calculate_mae',
    'calculate_bias',
    'calculate_ubrmse',
    'RUST_AVAILABLE'
]
