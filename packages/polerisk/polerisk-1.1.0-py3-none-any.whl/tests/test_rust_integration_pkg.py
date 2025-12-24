"""
Test script to verify the integration of Rust-optimized statistical functions
in the soilmoisture package.
"""

import numpy as np
import logging

from soilmoisture.analysis import (
    calculate_rmse,
    calculate_correlation,
    calculate_mae,
    calculate_bias,
    calculate_ubrmse,
    RUST_AVAILABLE,
)

logger = logging.getLogger(__name__)


def test_statistical_functions():
    # Generate test data
    np.random.seed(42)
    x = np.random.rand(1000) * 10  # Reference data
    noise = np.random.normal(0, 1, 1000)  # Random noise
    y = x + noise  # Data with noise

    # Print whether Rust is being used
    logger.debug(f"Using Rust optimizations: {RUST_AVAILABLE}")

    # Test RMSE
    rmse = calculate_rmse(x, y)
    logger.debug(f"RMSE: {rmse:.6f}")

    # Test Correlation
    corr = calculate_correlation(x, y)
    logger.debug(f"Correlation: {corr:.6f}")

    # Test MAE
    mae = calculate_mae(x, y)
    logger.debug(f"MAE: {mae:.6f}")

    # Test Bias
    bias = calculate_bias(x, y)
    logger.debug(f"Bias: {bias:.6f}")

    # Test ubRMSE
    ubrmse = calculate_ubrmse(x, y)
    logger.debug(f"ubRMSE: {ubrmse:.6f}")


if __name__ == "__main__":
    test_statistical_functions()
