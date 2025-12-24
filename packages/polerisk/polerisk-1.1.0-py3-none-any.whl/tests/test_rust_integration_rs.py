"""Pytest-based integration tests for Rust-accelerated functions.
Skips gracefully if the compiled Rust extension is not available.
"""

import math
import numpy as np
import pytest

try:
    import soilmoisture_rs as rust  # This may import the directory, not the compiled module

    REQUIRED_FUNCS = [
        "calculate_mae_rs",
        "calculate_rmse_rs",
        "calculate_correlation_rs",
        "calculate_bias_rs",
        "calculate_ubrmse_rs",
    ]
    if not all(hasattr(rust, name) for name in REQUIRED_FUNCS):
        pytest.skip(
            "Rust extension not built/loaded (module exists but missing expected functions).\n"
            "Build with: cd soilmoisture_rs && maturin develop --release",
            allow_module_level=True,
        )
except Exception:
    pytest.skip(
        "Rust extension not importable. Build with: cd soilmoisture_rs && maturin develop --release",
        allow_module_level=True,
    )


def test_mae_rs_basic():
    x = np.array([1.0, 2.0, 3.0, 4.0])
    y = np.array([1.1, 1.9, 3.2, 3.8])
    mae = rust.calculate_mae_rs(x, y)
    # Mean(|diff|) = mean([0.1, 0.1, 0.2, 0.2]) = 0.15
    assert math.isclose(mae, 0.15, rel_tol=1e-12, abs_tol=1e-12)


def test_rmse_rs_basic():
    x = np.array([0.0, 1.0, 2.0])
    y = np.array([0.0, 2.0, 1.0])
    rmse = rust.calculate_rmse_rs(x, y)
    # diffs = [0, -1, 1], squares = [0,1,1], mse=2/3, rmse=sqrt(2/3)
    assert math.isclose(rmse, math.sqrt(2 / 3), rel_tol=1e-12, abs_tol=1e-12)


def test_correlation_rs_basic():
    x = np.array([1.0, 2.0, 3.0, 4.0])
    y = np.array([2.0, 3.0, 4.0, 5.0])
    corr = rust.calculate_correlation_rs(x, y)
    # Perfect linear relationship with slope 1, correlation ~= 1
    assert math.isclose(corr, 1.0, rel_tol=1e-12, abs_tol=1e-12)


def test_bias_rs_basic():
    x = np.array([1.0, 2.0, 3.0])
    y = np.array([1.5, 2.5, 3.5])
    bias = rust.calculate_bias_rs(x, y)
    # mean(y - x) = mean([0.5, 0.5, 0.5]) = 0.5
    assert math.isclose(bias, 0.5, rel_tol=1e-12, abs_tol=1e-12)


def test_ubrmse_rs_basic():
    x = np.array([1.0, 2.0, 3.0, 4.0])
    y = np.array([1.1, 2.1, 2.9, 3.9])
    ubrmse = rust.calculate_ubrmse_rs(x, y)
    # Bias ~ 0.0; ubrmse ~= rmse here
    rmse = rust.calculate_rmse_rs(x, y)
    assert math.isclose(ubrmse, rmse, rel_tol=1e-12, abs_tol=1e-12)


def test_error_on_length_mismatch():
    x = np.array([1.0, 2.0])
    y = np.array([1.0])
    with pytest.raises(ValueError):
        rust.calculate_mae_rs(x, y)
    with pytest.raises(ValueError):
        rust.calculate_rmse_rs(x, y)
    with pytest.raises(ValueError):
        rust.calculate_correlation_rs(x, y)
    with pytest.raises(ValueError):
        rust.calculate_bias_rs(x, y)
    with pytest.raises(ValueError):
        rust.calculate_ubrmse_rs(x, y)
