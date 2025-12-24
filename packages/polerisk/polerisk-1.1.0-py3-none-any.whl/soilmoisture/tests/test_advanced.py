"""
Tests for advanced analytics functionality.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import logging

from soilmoisture.advanced.time_series import TimeSeriesAnalyzer, TrendAnalyzer
from soilmoisture.advanced.climatology import ClimatologyAnalyzer, SeasonalAnalyzer

logger = logging.getLogger(__name__)


@pytest.fixture
def sample_time_series():
    """Create sample time series data for testing."""
    # Create 3 years of daily data
    dates = pd.date_range('2020-01-01', '2022-12-31', freq='D')
    n_days = len(dates)
    
    # Create realistic seasonal pattern with trend and noise
    day_of_year = np.arange(1, n_days + 1) % 365
    seasonal = 0.2 + 0.1 * np.cos(2 * np.pi * day_of_year / 365)
    trend = 0.00005 * np.arange(n_days)  # Small increasing trend
    noise = np.random.normal(0, 0.02, n_days)
    
    values = seasonal + trend + noise
    values = np.clip(values, 0.05, 0.5)  # Realistic soil moisture range
    
    return pd.Series(values, index=dates)


@pytest.fixture
def sample_non_stationary_series():
    """Create non-stationary time series for testing."""
    dates = pd.date_range('2020-01-01', '2021-12-31', freq='D')
    n_days = len(dates)
    
    # Strong trend with changing variance
    trend = 0.0005 * np.arange(n_days)
    changing_variance = 0.01 + 0.02 * np.arange(n_days) / n_days
    noise = np.random.normal(0, changing_variance, n_days)
    
    values = 0.2 + trend + noise
    return pd.Series(values, index=dates)


class TestTimeSeriesAnalyzer:
    """Test the TimeSeriesAnalyzer class."""
    
    def test_initialization(self):
        """Test analyzer initialization."""
        analyzer = TimeSeriesAnalyzer()
        assert analyzer.scaler is not None
    
    def test_stationarity_analysis(self, sample_time_series):
        """Test stationarity analysis."""
        analyzer = TimeSeriesAnalyzer()
        results = analyzer.analyze_stationarity(sample_time_series)
        
        assert 'conclusion' in results
        assert results['conclusion'] in ['stationary', 'non_stationary', 'inconclusive']
    
    def test_stationarity_non_stationary(self, sample_non_stationary_series):
        """Test stationarity analysis on non-stationary series."""
        analyzer = TimeSeriesAnalyzer()
        results = analyzer.analyze_stationarity(sample_non_stationary_series)
        
        # Should detect non-stationarity
        assert results['conclusion'] in ['non_stationary', 'inconclusive']
    
    def test_seasonal_decompose(self, sample_time_series):
        """Test seasonal decomposition."""
        analyzer = TimeSeriesAnalyzer()
        decomp = analyzer.seasonal_decompose(sample_time_series, period=365)
        
        assert decomp.original is not None
        assert decomp.trend is not None
        assert decomp.seasonal is not None
        assert decomp.residual is not None
        assert 0 <= decomp.seasonal_strength <= 1
        assert 0 <= decomp.trend_strength <= 1
    
    def test_changepoint_detection(self, sample_time_series):
        """Test changepoint detection."""
        analyzer = TimeSeriesAnalyzer()
        changepoints = analyzer.detect_changepoints(sample_time_series, min_size=30)
        
        assert isinstance(changepoints, list)
        
        for cp in changepoints:
            assert 'index' in cp
            assert 'p_value' in cp
            assert 'mean_before' in cp
            assert 'mean_after' in cp
    
    def test_filter_application(self, sample_time_series):
        """Test digital filter application."""
        analyzer = TimeSeriesAnalyzer()
        
        # Test moving average filter
        filtered = analyzer.apply_filter(sample_time_series, filter_type='moving_average')
        assert len(filtered) <= len(sample_time_series)
        
        # Test Butterworth filter (if scipy available)
        try:
            filtered_butter = analyzer.apply_filter(
                sample_time_series, 
                filter_type='butterworth', 
                cutoff_freq=0.1
            )
            assert len(filtered_butter) == len(sample_time_series.dropna())
        except ImportError:
            # scipy not available, skip
            pass
    
    def test_empty_series(self):
        """Test handling of empty series."""
        analyzer = TimeSeriesAnalyzer()
        empty_series = pd.Series([], dtype=float)
        
        # Should handle empty series gracefully
        result = analyzer.analyze_stationarity(empty_series)
        assert 'conclusion' in result


class TestTrendAnalyzer:
    """Test the TrendAnalyzer class."""
    
    def test_initialization(self):
        """Test trend analyzer initialization."""
        analyzer = TrendAnalyzer()
        assert analyzer is not None
    
    def test_linear_trend_analysis(self, sample_time_series):
        """Test linear trend analysis."""
        analyzer = TrendAnalyzer()
        result = analyzer.analyze_trend(sample_time_series, method='linear')
        
        assert hasattr(result, 'slope')
        assert hasattr(result, 'p_value')
        assert hasattr(result, 'trend_direction')
        assert hasattr(result, 'significance')
        assert result.trend_direction in ['increasing', 'decreasing', 'no_trend']
    
    def test_theil_sen_trend(self, sample_time_series):
        """Test Theil-Sen trend analysis."""
        analyzer = TrendAnalyzer()
        result = analyzer.analyze_trend(sample_time_series, method='theil_sen')
        
        assert hasattr(result, 'slope')
        assert hasattr(result, 'trend_direction')
    
    def test_seasonal_trend_analysis(self, sample_time_series):
        """Test seasonal trend analysis."""
        analyzer = TrendAnalyzer()
        seasonal_trends = analyzer.seasonal_trend_analysis(sample_time_series)
        
        expected_seasons = ['spring', 'summer', 'fall', 'winter']
        for season in expected_seasons:
            if season in seasonal_trends:
                assert 'slope' in seasonal_trends[season]
                assert 'direction' in seasonal_trends[season]
                assert 'significance' in seasonal_trends[season]
    
    def test_insufficient_data(self):
        """Test trend analysis with insufficient data."""
        analyzer = TrendAnalyzer()
        
        # Very short series
        short_series = pd.Series([1.0, 2.0])
        result = analyzer.analyze_trend(short_series)
        
        assert result.trend_direction == 'insufficient_data'
    
    def test_trend_classification(self):
        """Test trend classification functions."""
        analyzer = TrendAnalyzer()
        
        # Test with known increasing trend
        dates = pd.date_range('2020-01-01', periods=100, freq='D')
        increasing_series = pd.Series(np.arange(100) * 0.01, index=dates)
        
        result = analyzer.analyze_trend(increasing_series)
        assert result.trend_direction == 'increasing'
        assert result.slope > 0


class TestClimatologyAnalyzer:
    """Test the ClimatologyAnalyzer class."""
    
    def test_initialization(self):
        """Test climatology analyzer initialization."""
        analyzer = ClimatologyAnalyzer()
        assert len(analyzer.season_definitions) == 4
        assert 'DJF' in analyzer.season_definitions
    
    def test_compute_climatology(self, sample_time_series):
        """Test climatology computation."""
        analyzer = ClimatologyAnalyzer()
        climatology = analyzer.compute_climatology(sample_time_series)
        
        assert climatology.long_term_mean > 0
        assert climatology.long_term_std > 0
        assert len(climatology.seasonal_stats) <= 4
        assert len(climatology.monthly_climatology) == 12
        assert climatology.annual_cycle_amplitude >= 0
        assert 1 <= climatology.annual_cycle_phase <= 12
    
    def test_compute_anomalies(self, sample_time_series):
        """Test anomaly computation."""
        analyzer = ClimatologyAnalyzer()
        
        # Test different anomaly types
        abs_anomalies = analyzer.compute_anomalies(sample_time_series, anomaly_type='absolute')
        rel_anomalies = analyzer.compute_anomalies(sample_time_series, anomaly_type='relative')
        std_anomalies = analyzer.compute_anomalies(sample_time_series, anomaly_type='standardized')
        
        assert len(abs_anomalies) == len(sample_time_series)
        assert len(rel_anomalies) == len(sample_time_series)
        assert len(std_anomalies) == len(sample_time_series)
        
        # Absolute anomalies should have near-zero mean
        assert abs(abs_anomalies.mean()) < 0.01
    
    def test_detect_extreme_events(self, sample_time_series):
        """Test extreme event detection."""
        analyzer = ClimatologyAnalyzer()
        
        # Test percentile-based detection
        extremes = analyzer.detect_extreme_events(
            sample_time_series, 
            threshold_type='percentile', 
            threshold_value=5.0
        )
        
        assert isinstance(extremes, pd.DataFrame)
        if len(extremes) > 0:
            assert 'date' in extremes.columns
            assert 'type' in extremes.columns
            assert 'severity' in extremes.columns
            assert set(extremes['type'].unique()).issubset({'dry', 'wet'})
    
    def test_seasonal_trends(self, sample_time_series):
        """Test seasonal trend analysis."""
        analyzer = ClimatologyAnalyzer()
        seasonal_trends = analyzer.analyze_trends_by_season(sample_time_series)
        
        for season, trend_info in seasonal_trends.items():
            assert 'slope' in trend_info
            assert 'p_value' in trend_info
            assert 'significance' in trend_info
            assert 'direction' in trend_info
            assert trend_info['significance'] in ['significant', 'not_significant']
    
    def test_non_datetime_index(self):
        """Test error handling for non-datetime index."""
        analyzer = ClimatologyAnalyzer()
        
        # Series without datetime index
        non_datetime_series = pd.Series([1, 2, 3, 4, 5])
        
        with pytest.raises(ValueError, match="datetime index"):
            analyzer.compute_climatology(non_datetime_series)


class TestSeasonalAnalyzer:
    """Test the SeasonalAnalyzer class."""
    
    def test_initialization(self):
        """Test seasonal analyzer initialization."""
        analyzer = SeasonalAnalyzer()
        assert analyzer is not None
    
    def test_seasonal_cycle_analysis(self, sample_time_series):
        """Test seasonal cycle analysis."""
        analyzer = SeasonalAnalyzer()
        cycle_analysis = analyzer.analyze_seasonal_cycle(sample_time_series)
        
        assert 'monthly_statistics' in cycle_analysis
        assert 'amplitude' in cycle_analysis
        assert 'maximum_month' in cycle_analysis
        assert 'minimum_month' in cycle_analysis
        assert 'seasonality_strength' in cycle_analysis
        
        assert 1 <= cycle_analysis['maximum_month'] <= 12
        assert 1 <= cycle_analysis['minimum_month'] <= 12
        assert 0 <= cycle_analysis['seasonality_strength'] <= 1
    
    def test_year_comparison(self, sample_time_series):
        """Test year comparison functionality."""
        analyzer = SeasonalAnalyzer()
        comparison = analyzer.compare_years(sample_time_series)
        
        assert 'yearly_comparison' in comparison
        assert 'inter_annual_statistics' in comparison
        assert 'n_years' in comparison
        
        # Should have multiple years
        assert comparison['n_years'] > 1
        
        for year, year_stats in comparison['yearly_comparison'].items():
            assert 'annual_mean' in year_stats
            assert 'seasonal_amplitude' in year_stats
            assert 'max_month' in year_stats
    
    def test_phenology_analysis(self, sample_time_series):
        """Test phenology analysis."""
        analyzer = SeasonalAnalyzer()
        phenology = analyzer.phenology_analysis(sample_time_series)
        
        if 'yearly_phenology' in phenology:
            for year, year_pheno in phenology['yearly_phenology'].items():
                if year_pheno['growing_season_length'] is not None:
                    assert isinstance(year_pheno['growing_season_length'], (int, float))
                    assert year_pheno['growing_season_length'] >= 0
    
    def test_custom_growth_threshold(self, sample_time_series):
        """Test phenology analysis with custom threshold."""
        analyzer = SeasonalAnalyzer()
        
        custom_threshold = sample_time_series.quantile(0.7)
        phenology = analyzer.phenology_analysis(
            sample_time_series, 
            growth_threshold=custom_threshold
        )
        
        # Should work with custom threshold
        assert isinstance(phenology, dict)
    
    def test_insufficient_data(self):
        """Test handling of insufficient data."""
        analyzer = SeasonalAnalyzer()
        
        # Very short time series
        short_dates = pd.date_range('2020-01-01', periods=10, freq='D')
        short_series = pd.Series(np.random.rand(10), index=short_dates)
        
        # Should handle gracefully without crashing
        cycle_analysis = analyzer.analyze_seasonal_cycle(short_series)
        assert isinstance(cycle_analysis, dict)


class TestIntegration:
    """Integration tests for advanced analytics."""
    
    def test_complete_analysis_workflow(self, sample_time_series):
        """Test complete analysis workflow."""
        # Time series analysis
        ts_analyzer = TimeSeriesAnalyzer()
        stationarity = ts_analyzer.analyze_stationarity(sample_time_series)
        decomposition = ts_analyzer.seasonal_decompose(sample_time_series)
        changepoints = ts_analyzer.detect_changepoints(sample_time_series)
        
        # Trend analysis
        trend_analyzer = TrendAnalyzer()
        trend_result = trend_analyzer.analyze_trend(sample_time_series)
        seasonal_trends = trend_analyzer.seasonal_trend_analysis(sample_time_series)
        
        # Climatology analysis
        clim_analyzer = ClimatologyAnalyzer()
        climatology = clim_analyzer.compute_climatology(sample_time_series)
        anomalies = clim_analyzer.compute_anomalies(sample_time_series)
        extremes = clim_analyzer.detect_extreme_events(sample_time_series)
        
        # Seasonal analysis
        seasonal_analyzer = SeasonalAnalyzer()
        seasonal_cycle = seasonal_analyzer.analyze_seasonal_cycle(sample_time_series)
        year_comparison = seasonal_analyzer.compare_years(sample_time_series)
        
        # Verify all analyses completed
        assert stationarity['conclusion'] is not None
        assert decomposition.seasonal_strength >= 0
        assert isinstance(changepoints, list)
        assert trend_result.trend_direction is not None
        assert climatology.long_term_mean > 0
        assert len(anomalies) == len(sample_time_series)
        assert seasonal_cycle['amplitude'] >= 0
        
        logger.info(f"Complete analysis successful!")
        logger.debug(f"Trend direction: {trend_result.trend_direction}")
        logger.debug(f"Seasonality strength: {seasonal_cycle['seasonality_strength']:.3f}")
        logger.debug(f"Extreme events detected: {len(extremes)}")


if __name__ == "__main__":
    pytest.main([__file__])
