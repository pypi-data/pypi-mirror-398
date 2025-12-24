"""
Statistical analysis functions for soil moisture data.

This module provides optimized statistical functions for analyzing soil moisture data,
with performance-critical functions implemented in Rust for better performance.
The module automatically falls back to pure Python implementations if the Rust extensions
are not available.

Examples
--------
>>> import numpy as np
>>> from soilmoisture.analysis import calculate_rmse, calculate_correlation
>>> 
>>> # Generate sample data
>>> x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
>>> y = np.array([1.1, 2.1, 2.9, 4.1, 5.0])
>>> 
>>> # Calculate RMSE
>>> rmse = calculate_rmse(x, y)
logger.debug(f"RMSE: {rmse:.4f}")
>>> 
>>> # Calculate correlation
>>> corr = calculate_correlation(x, y)
logger.debug(f"Correlation: {corr:.4f}")

Note
----
For optimal performance, ensure the Rust extensions are installed.
If not available, the module will automatically use Python implementations.
"""

try:
    from soilmoisture_rs import (
        calculate_rmse_rs as calculate_rmse,
        calculate_correlation_rs as calculate_correlation,
        calculate_mae_rs as calculate_mae,
        calculate_bias_rs as calculate_bias,
        calculate_ubrmse_rs as calculate_ubrmse
    )
    RUST_AVAILABLE = True
except ImportError:
    import warnings
    import numpy as np
    from typing import Union, Tuple, Optional
    
    RUST_AVAILABLE = False
    
    def _ensure_arrays(x, y) -> Tuple[np.ndarray, np.ndarray]:
        """Convert inputs to numpy arrays and validate their shapes.
        
        Parameters
        ----------
        x : array_like
            First input array
        y : array_like
            Second input array
            
        Returns
        -------
        tuple
            Tuple of (x_arr, y_arr) where both are numpy.ndarray with dtype float64
            
        Raises
        ------
        ValueError
            If inputs cannot be converted to arrays, are empty, or have different shapes
        """
        if len(x) == 0 or len(y) == 0:
            raise ValueError("Input arrays cannot be empty")
            
        x_arr = np.asarray(x, dtype=np.float64)
        y_arr = np.asarray(y, dtype=np.float64)
        
        if x_arr.shape != y_arr.shape:
            raise ValueError(rf"Input arrays must have the same shape. Got {x_arr.shape} and {y_arr.shape}")
            
        return x_arr, y_arr
    
    def calculate_rmse(x: Union[np.ndarray, list], y: Union[np.ndarray, list]) -> float:
        r"""Calculate Root Mean Square Error (RMSE) between two arrays.
        
        RMSE is a measure of the differences between values predicted by a model
        and the values observed. It represents the square root of the second sample
        moment of the differences between predicted values and observed values.
        
        .. math::
            RMSE = \sqrt{\frac{1}{n}\sum_{i=1}^{n}(y_i - \hat{y}_i)^2}
        
        Parameters
        ----------
        x : array_like
            Reference/observed values (ground truth)
        y : array_like
            Predicted/estimated values
            
        Returns
        -------
        float
            The RMSE value, a non-negative floating point value (the best value is 0.0)
            
        Raises
        ------
        ValueError
            If inputs have different lengths or cannot be converted to arrays
            
        Examples
        --------
        >>> x = [1.0, 2.0, 3.0]
        >>> y = [1.1, 2.1, 2.9]
        >>> calculate_rmse(x, y)
        0.08164965809277261
        """
        x_arr, y_arr = _ensure_arrays(x, y)
        return np.sqrt(np.mean((x_arr - y_arr) ** 2))
    
    def calculate_correlation(x: Union[np.ndarray, list], y: Union[np.ndarray, list]) -> float:
        r"""Calculate the Pearson correlation coefficient between two arrays.
        
        The correlation coefficient measures the linear relationship between two datasets.
        The calculation is based on the Pearson correlation coefficient formula:
        
        .. math::
            \rho_{X,Y} = \frac{\text{cov}(X,Y)}{\sigma_X \sigma_Y}
            
        where cov is the covariance and sigma is the standard deviation.
        
        Parameters
        ----------
        x : array_like
            First array of values
        y : array_like
            Second array of values. Must have the same length as x.
            
        Returns
        -------
        float
            Pearson's correlation coefficient, a float between -1 and 1.
            Returns 1.0 for single-element arrays.
            
        Raises
        ------
        ValueError
            If inputs have different lengths, are empty, or have zero variance
        """
        x_arr, y_arr = _ensure_arrays(x, y)
        
        # Special case: single element
        if len(x_arr) == 1:
            return 1.0
            
        # Check for constant arrays
        if np.all(x_arr == x_arr[0]) or np.all(y_arr == y_arr[0]):
            # If both arrays are constant, correlation is undefined but we'll return 1 if they're the same
            if np.all(x_arr == y_arr):
                return 1.0
            return np.nan  # Undefined correlation for constant arrays
            
        try:
            return np.corrcoef(x_arr, y_arr)[0, 1]
        except (ValueError, RuntimeWarning):
            # Handle any numerical issues by returning NaN
            return np.nan
    
    def calculate_mae(x: Union[np.ndarray, list], y: Union[np.ndarray, list]) -> float:
        r"""Calculate the Mean Absolute Error (MAE) between two arrays.
        
        MAE measures the average magnitude of the errors in a set of predictions,
        without considering their direction. It's the average over the test sample
        of the absolute differences between prediction and actual observation where
        all individual differences have equal weight.
        
        .. math::
            \text{MAE} = \frac{1}{n}\sum_{i=1}^{n} |y_i - \hat{y}_i|
        
        Parameters
        ----------
        x : array_like
            Reference/observed values (ground truth)
        y : array_like
            Predicted/estimated values
            
        Returns
        -------
        float
            The MAE value, a non-negative floating point value (the best value is 0.0)
            
        Examples
        --------
        >>> x = [3, -0.5, 2, 7]
        >>> y = [2.5, 0.0, 2, 8]
        >>> calculate_mae(x, y)
        0.5
        """
        x_arr, y_arr = _ensure_arrays(x, y)
        return np.mean(np.abs(x_arr - y_arr))
    
    def calculate_bias(x: Union[np.ndarray, list], y: Union[np.ndarray, list]) -> float:
        r"""Calculate the bias between two arrays.
        
        Bias measures the average difference between the predicted values and the
        reference values. It indicates whether the model systematically over-estimates
        (positive bias) or under-estimates (negative bias) the target variable.
        
        .. math::
            \text{Bias} = \frac{1}{n}\sum_{i=1}^{n} (\hat{y}_i - y_i)
        
        Parameters
        ----------
        x : array_like
            Reference/observed values (ground truth)
        y : array_like
            Predicted/estimated values
            
        Returns
        -------
        float
            The bias value, which can be positive, negative, or zero.
            - Positive value indicates over-estimation
            - Negative value indicates under-estimation
            - Zero indicates no systematic bias
            
        Examples
        --------
        >>> x = [1, 2, 3, 4, 5]  # Observed
        >>> y = [1.1, 2.1, 3.1, 4.1, 5.1]  # Predicted (systematically higher by 0.1)
        >>> calculate_bias(x, y)  # Should be approximately 0.1
        0.10000000000000009
        """
        x_arr, y_arr = _ensure_arrays(x, y)
        return np.mean(y_arr - x_arr)
    
    def calculate_ubrmse(x: Union[np.ndarray, list], y: Union[np.ndarray, list]) -> float:
        r"""Calculate the Unbiased Root Mean Square Error (ubRMSE) between two arrays.
        
        ubRMSE is a measure of precision that removes the impact of bias from the
        RMSE calculation. It's particularly useful when you want to assess the
        random component of the error separately from the systematic component.
        
        .. math::
            \text{ubRMSE} = \sqrt{\frac{1}{n}\sum_{i=1}^{n} \left[(y_i - \bar{y}) - (x_i - \bar{x})\right]^2}
        
        where :math:`\bar{x}` and :math:`\bar{y}` are the means of x and y respectively.
        
        Parameters
        ----------
        x : array_like
            Reference/observed values (ground truth)
        y : array_like
            Predicted/estimated values
            
        Returns
        -------
        float
            The ubRMSE value, a non-negative floating point value.
            
        Notes
        -----
        - ubRMSE is always less than or equal to RMSE
        - If the model is unbiased, ubRMSE will be equal to RMSE
        - A large difference between RMSE and ubRMSE indicates significant bias
        
        Examples
        --------
        >>> x = [1, 2, 3, 4, 5]  # Observed
        >>> y = [1.1, 2.1, 3.1, 4.1, 5.1]  # Predicted (systematic offset)
        >>> calculate_ubrmse(x, y)  # Should be very small (just random error)
        0.0
        """
        x_arr, y_arr = _ensure_arrays(x, y)
        bias = calculate_bias(x_arr, y_arr)
        return np.sqrt(np.mean((y_arr - x_arr - bias) ** 2))
    
    # Warn that using Python implementation instead of Rust
    warnings.warn(
        "Rust extensions not available. Falling back to Python implementations. "
        "For better performance, install the Rust extensions with: "
        "cd soilmoisture_rs && maturin develop --release",
        RuntimeWarning
    )

# Add type hints for the public API
if RUST_AVAILABLE:
    from typing import Union
    import numpy as np
    
    # Import Rust functions with aliases to avoid name conflicts
    from soilmoisture_rs import (
        calculate_rmse_rs,
        calculate_correlation_rs,
        calculate_mae_rs,
        calculate_bias_rs,
        calculate_ubrmse_rs
    )
    
    def calculate_rmse(x: Union[np.ndarray, list], y: Union[np.ndarray, list]) -> float:
        """
        Calculate Root Mean Square Error (RMSE) between two arrays.
        
        Optimized Rust implementation.
        """
        x_arr = np.asarray(x, dtype=np.float64)
        y_arr = np.asarray(y, dtype=np.float64)
        return calculate_rmse_rs(x_arr, y_arr)
    
    def calculate_correlation(x: Union[np.ndarray, list], y: Union[np.ndarray, list]) -> float:
        """
        Calculate correlation coefficient between two arrays.
        
        Optimized Rust implementation.
        """
        x_arr = np.asarray(x, dtype=np.float64)
        y_arr = np.asarray(y, dtype=np.float64)
        return calculate_correlation_rs(x_arr, y_arr)
    
    def calculate_mae(x: Union[np.ndarray, list], y: Union[np.ndarray, list]) -> float:
        """
        Calculate Mean Absolute Error (MAE) between two arrays.
        
        Optimized Rust implementation.
        """
        x_arr = np.asarray(x, dtype=np.float64)
        y_arr = np.asarray(y, dtype=np.float64)
        return calculate_mae_rs(x_arr, y_arr)
    
    def calculate_bias(x: Union[np.ndarray, list], y: Union[np.ndarray, list]) -> float:
        """
        Calculate bias between two arrays.
        
        Optimized Rust implementation.
        """
        x_arr = np.asarray(x, dtype=np.float64)
        y_arr = np.asarray(y, dtype=np.float64)
        return calculate_bias_rs(x_arr, y_arr)
    
    def calculate_ubrmse(x: Union[np.ndarray, list], y: Union[np.ndarray, list]) -> float:
        """
        Calculate Unbiased Root Mean Square Error (ubRMSE) between two arrays.
        
        Optimized Rust implementation.
        """
        x_arr = np.asarray(x, dtype=np.float64)
        y_arr = np.asarray(y, dtype=np.float64)
        return calculate_ubrmse_rs(x_arr, y_arr)

# Update __all__ for cleaner imports
__all__ = [
    'calculate_rmse',
    'calculate_correlation',
    'calculate_mae',
    'calculate_bias',
    'calculate_ubrmse',
    'RUST_AVAILABLE'
]
