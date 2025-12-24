import numpy as np
import logging
import pytest

# Try to import Rust extensions, skip tests if not available
try:
    from soilmoisture_rs import (
        calculate_rmse_rs,
        calculate_correlation_rs,
        calculate_mae_rs,
        calculate_bias_rs,
        calculate_ubrmse_rs,
    )

    RUST_AVAILABLE = True
except ImportError:
    RUST_AVAILABLE = False
    # Create dummy functions so the module can still be imported
    calculate_rmse_rs = None
    calculate_correlation_rs = None
    calculate_mae_rs = None
    calculate_bias_rs = None
    calculate_ubrmse_rs = None

logger = logging.getLogger(__name__)

pytestmark = pytest.mark.skipif(
    not RUST_AVAILABLE, reason="Rust extensions not available"
)


def main():
    # Generate test data
    np.random.seed(42)
    x = np.random.rand(1000) * 10  # Reference data
    noise = np.random.normal(0, 1, 1000)  # Random noise
    y = x + noise  # Data with noise

    # Test RMSE
    rmse = calculate_rmse_rs(x, y)
    logger.debug(f"RMSE: {rmse:.6f}")

    # Test Correlation
    corr = calculate_correlation_rs(x, y)
    logger.debug(f"Correlation: {corr:.6f}")

    # Test MAE
    mae = calculate_mae_rs(x, y)
    logger.debug(f"MAE: {mae:.6f}")

    # Test Bias
    bias = calculate_bias_rs(x, y)
    logger.debug(f"Bias: {bias:.6f}")

    # Test ubRMSE
    ubrmse = calculate_ubrmse_rs(x, y)
    logger.debug(f"ubRMSE: {ubrmse:.6f}")


if __name__ == "__main__":
    main()
