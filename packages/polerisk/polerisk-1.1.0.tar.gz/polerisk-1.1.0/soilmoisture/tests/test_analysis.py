"""Unit tests for analysis module."""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd

# Add the parent directory to the path so we can import the module
sys.path.insert(0, str(Path(__file__).parent.parent))

from soilmoisture.analysis.statistics import (  # noqa: E402
    StatisticalAnalyzer,
    calculate_bias,
    calculate_correlation,
    calculate_mae,
    calculate_rmse,
    calculate_ubrmse,
)


class TestStatisticalAnalyzer(unittest.TestCase):
    """Test cases for StatisticalAnalyzer class."""

    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = StatisticalAnalyzer()
        
        # Create sample data for testing
        np.random.seed(42)  # For reproducible tests
        self.n_samples = 100
        
        # Create correlated data with known statistics
        self.true_values = np.random.uniform(0.1, 0.5, self.n_samples)
        self.predicted_values = self.true_values + np.random.normal(0, 0.05, self.n_samples)
        
        # Create DataFrame
        self.test_data = pd.DataFrame({
            'observed': self.true_values,
            'predicted': self.predicted_values
        })

    def test_calculate_correlation(self):
        """Test correlation calculation."""
        correlation = calculate_correlation(self.true_values, self.predicted_values)
        
        # Should be highly correlated since predicted = true + small noise
        self.assertGreater(correlation, 0.8)
        self.assertLessEqual(correlation, 1.0)
        self.assertGreaterEqual(correlation, -1.0)

    def test_calculate_bias(self):
        """Test bias calculation."""
        bias = calculate_bias(self.true_values, self.predicted_values)
        
        # Bias should be close to 0 since we added zero-mean noise
        self.assertAlmostEqual(bias, 0.0, places=1)

    def test_calculate_rmse(self):
        """Test RMSE calculation."""
        rmse = calculate_rmse(self.true_values, self.predicted_values)
        
        # RMSE should be positive and reasonable
        self.assertGreater(rmse, 0)
        self.assertLess(rmse, 0.2)  # Should be small since we added small noise

    def test_calculate_mae(self):
        """Test MAE calculation."""
        mae = calculate_mae(self.true_values, self.predicted_values)
        
        # MAE should be positive and smaller than RMSE
        self.assertGreater(mae, 0)
        rmse = calculate_rmse(self.true_values, self.predicted_values)
        self.assertLessEqual(mae, rmse)

    def test_calculate_ubrmse(self):
        """Test unbiased RMSE calculation."""
        ubrmse = calculate_ubrmse(self.true_values, self.predicted_values)
        
        # ubRMSE should be positive
        self.assertGreater(ubrmse, 0)
        
        # ubRMSE should be close to RMSE when bias is small
        rmse = calculate_rmse(self.true_values, self.predicted_values)
        self.assertAlmostEqual(ubrmse, rmse, places=1)

    def test_comprehensive_analysis(self):
        """Test comprehensive statistical analysis."""
        results = self.analyzer.analyze(self.test_data, 'observed', 'predicted')
        
        # Check that all expected metrics are present
        expected_metrics = ['correlation', 'bias', 'rmse', 'mae', 'ubrmse', 'count']
        for metric in expected_metrics:
            self.assertIn(metric, results)
        
        # Check data types and ranges
        self.assertIsInstance(results['correlation'], float)
        self.assertIsInstance(results['bias'], float)
        self.assertIsInstance(results['rmse'], float)
        self.assertIsInstance(results['mae'], float)
        self.assertIsInstance(results['ubrmse'], float)
        self.assertIsInstance(results['count'], int)
        
        # Check that count matches input data
        self.assertEqual(results['count'], self.n_samples)

    def test_analysis_with_missing_data(self):
        """Test analysis with missing data."""
        # Add some missing values
        data_with_missing = self.test_data.copy()
        data_with_missing.loc[:10, 'predicted'] = np.nan
        data_with_missing.loc[20:25, 'observed'] = np.nan
        
        results = self.analyzer.analyze(data_with_missing, 'observed', 'predicted')
        
        # Count should reflect only valid pairs
        expected_count = self.n_samples - 11 - 6  # Subtract missing values
        self.assertEqual(results['count'], expected_count)
        
        # All metrics should still be calculated
        self.assertIsNotNone(results['correlation'])
        self.assertIsNotNone(results['rmse'])

    def test_analysis_with_identical_data(self):
        """Test analysis when observed and predicted are identical."""
        identical_data = pd.DataFrame({
            'observed': self.true_values,
            'predicted': self.true_values
        })
        
        results = self.analyzer.analyze(identical_data, 'observed', 'predicted')
        
        # Perfect correlation
        self.assertAlmostEqual(results['correlation'], 1.0, places=5)
        
        # Zero bias and RMSE
        self.assertAlmostEqual(results['bias'], 0.0, places=10)
        self.assertAlmostEqual(results['rmse'], 0.0, places=10)
        self.assertAlmostEqual(results['mae'], 0.0, places=10)

    def test_analysis_with_constant_data(self):
        """Test analysis with constant data."""
        constant_data = pd.DataFrame({
            'observed': np.full(50, 0.3),
            'predicted': np.full(50, 0.3)
        })
        
        results = self.analyzer.analyze(constant_data, 'observed', 'predicted')
        
        # Correlation should be NaN for constant data
        self.assertTrue(np.isnan(results['correlation']))
        
        # Other metrics should be zero
        self.assertAlmostEqual(results['bias'], 0.0, places=10)
        self.assertAlmostEqual(results['rmse'], 0.0, places=10)

    def test_seasonal_analysis(self):
        """Test seasonal analysis functionality."""
        # Create data with seasonal patterns
        dates = pd.date_range('2020-01-01', '2020-12-31', freq='D')
        seasonal_pattern = np.sin(2 * np.pi * np.arange(len(dates)) / 365.25)
        
        seasonal_data = pd.DataFrame({
            'date': dates,
            'observed': 0.3 + 0.1 * seasonal_pattern + np.random.normal(0, 0.02, len(dates)),
            'predicted': 0.3 + 0.08 * seasonal_pattern + np.random.normal(0, 0.03, len(dates))
        })
        seasonal_data.set_index('date', inplace=True)
        
        # Add month column for seasonal analysis
        seasonal_data['month'] = seasonal_data.index.month
        
        seasonal_results = self.analyzer.seasonal_analysis(seasonal_data, 'observed', 'predicted', 'month')
        
        # Should have results for all 12 months
        self.assertEqual(len(seasonal_results), 12)
        
        # Each month should have statistical results
        for month_result in seasonal_results.values():
            self.assertIn('correlation', month_result)
            self.assertIn('rmse', month_result)

    def test_outlier_detection(self):
        """Test outlier detection functionality."""
        # Create data with outliers
        data_with_outliers = self.test_data.copy()
        
        # Add some outliers
        outlier_indices = [10, 25, 50, 75]
        data_with_outliers.loc[outlier_indices, 'predicted'] = 2.0  # Unrealistic soil moisture
        
        outliers = self.analyzer.detect_outliers(data_with_outliers, 'observed', 'predicted')
        
        # Should detect the outliers we added
        self.assertGreater(len(outliers), 0)
        
        # Outlier indices should include some of the ones we added
        detected_indices = outliers.index.tolist()
        self.assertTrue(any(idx in detected_indices for idx in outlier_indices))

    def test_trend_analysis(self):
        """Test trend analysis functionality."""
        # Create data with a trend
        dates = pd.date_range('2020-01-01', '2020-12-31', freq='D')
        trend = np.linspace(0, 0.1, len(dates))  # Increasing trend
        
        trend_data = pd.DataFrame({
            'date': dates,
            'observed': 0.3 + trend + np.random.normal(0, 0.02, len(dates)),
            'predicted': 0.3 + 0.8 * trend + np.random.normal(0, 0.03, len(dates))
        })
        trend_data.set_index('date', inplace=True)
        
        trend_results = self.analyzer.trend_analysis(trend_data, 'observed', 'predicted')
        
        # Should detect positive trends
        self.assertIn('observed_trend', trend_results)
        self.assertIn('predicted_trend', trend_results)
        self.assertGreater(trend_results['observed_trend'], 0)
        self.assertGreater(trend_results['predicted_trend'], 0)


class TestStatisticalFunctions(unittest.TestCase):
    """Test cases for individual statistical functions."""

    def setUp(self):
        """Set up test fixtures."""
        # Create known test cases
        self.perfect_match = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
        self.perfect_predicted = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
        
        self.biased_predicted = np.array([0.15, 0.25, 0.35, 0.45, 0.55])  # +0.05 bias
        
        self.noisy_predicted = np.array([0.12, 0.18, 0.32, 0.38, 0.52])  # Some noise

    def test_correlation_perfect_match(self):
        """Test correlation with perfect match."""
        corr = calculate_correlation(self.perfect_match, self.perfect_predicted)
        self.assertAlmostEqual(corr, 1.0, places=10)

    def test_correlation_no_correlation(self):
        """Test correlation with no correlation."""
        random_data = np.array([0.5, 0.1, 0.4, 0.2, 0.3])
        corr = calculate_correlation(self.perfect_match, random_data)
        self.assertLess(abs(corr), 0.5)  # Should be low correlation

    def test_bias_calculation(self):
        """Test bias calculation."""
        bias = calculate_bias(self.perfect_match, self.biased_predicted)
        self.assertAlmostEqual(bias, 0.05, places=10)

    def test_rmse_calculation(self):
        """Test RMSE calculation."""
        rmse_perfect = calculate_rmse(self.perfect_match, self.perfect_predicted)
        self.assertAlmostEqual(rmse_perfect, 0.0, places=10)
        
        rmse_biased = calculate_rmse(self.perfect_match, self.biased_predicted)
        self.assertAlmostEqual(rmse_biased, 0.05, places=10)

    def test_mae_calculation(self):
        """Test MAE calculation."""
        mae_perfect = calculate_mae(self.perfect_match, self.perfect_predicted)
        self.assertAlmostEqual(mae_perfect, 0.0, places=10)
        
        mae_biased = calculate_mae(self.perfect_match, self.biased_predicted)
        self.assertAlmostEqual(mae_biased, 0.05, places=10)

    def test_ubrmse_calculation(self):
        """Test unbiased RMSE calculation."""
        # For purely biased data (no random error), ubRMSE should be 0
        ubrmse_biased = calculate_ubrmse(self.perfect_match, self.biased_predicted)
        self.assertAlmostEqual(ubrmse_biased, 0.0, places=10)
        
        # For data with random error, ubRMSE should be > 0
        ubrmse_noisy = calculate_ubrmse(self.perfect_match, self.noisy_predicted)
        self.assertGreater(ubrmse_noisy, 0)

    def test_error_handling(self):
        """Test error handling for invalid inputs."""
        # Test with different length arrays
        short_array = np.array([0.1, 0.2])
        
        with self.assertRaises(ValueError):
            calculate_correlation(self.perfect_match, short_array)
        
        # Test with all NaN values
        nan_array = np.full(5, np.nan)
        
        result = calculate_correlation(self.perfect_match, nan_array)
        self.assertTrue(np.isnan(result))

    def test_edge_cases(self):
        """Test edge cases for statistical functions."""
        # Single value arrays
        single_obs = np.array([0.3])
        single_pred = np.array([0.3])
        
        bias = calculate_bias(single_obs, single_pred)
        self.assertEqual(bias, 0.0)
        
        rmse = calculate_rmse(single_obs, single_pred)
        self.assertEqual(rmse, 0.0)
        
        # Correlation with single value should be NaN
        corr = calculate_correlation(single_obs, single_pred)
        self.assertTrue(np.isnan(corr))


if __name__ == "__main__":
    unittest.main()
