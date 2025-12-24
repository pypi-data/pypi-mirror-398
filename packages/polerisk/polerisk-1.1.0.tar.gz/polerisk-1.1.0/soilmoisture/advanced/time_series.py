"""
Advanced time series analysis for soil moisture data.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
import logging
from dataclasses import dataclass
from scipy import stats, signal
from sklearn.preprocessing import StandardScaler

try:
    from scipy.signal import butter, filtfilt
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

try:
    from statsmodels.tsa.seasonal import seasonal_decompose
    from statsmodels.tsa.stattools import adfuller, kpss
    from statsmodels.stats.diagnostic import acorr_ljungbox
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class TrendResult:
    """Results from trend analysis."""
    slope: float
    intercept: float
    r_value: float
    p_value: float
    std_err: float
    trend_direction: str
    significance: str
    trend_magnitude: str


@dataclass
class SeasonalDecomposition:
    """Results from seasonal decomposition."""
    original: pd.Series
    trend: pd.Series
    seasonal: pd.Series
    residual: pd.Series
    seasonal_strength: float
    trend_strength: float


class TimeSeriesAnalyzer:
    """
    Advanced time series analysis for soil moisture data.
    """
    
    def __init__(self):
        self.scaler = StandardScaler()
        
    def analyze_stationarity(self, series: pd.Series, 
                           significance_level: float = 0.05) -> Dict:
        """
        Test time series for stationarity using ADF and KPSS tests.
        
        Args:
            series: Time series data
            significance_level: Significance level for tests
            
        Returns:
            Dictionary with stationarity test results
        """
        if not STATSMODELS_AVAILABLE:
            logger.warning("Statsmodels not available. Using basic statistics.")
            return self._basic_stationarity_test(series)
        
        series_clean = series.dropna()
        
        results = {}
        
        # Augmented Dickey-Fuller test
        try:
            adf_result = adfuller(series_clean, autolag='AIC')
            results['adf'] = {
                'statistic': adf_result[0],
                'p_value': adf_result[1],
                'critical_values': adf_result[4],
                'is_stationary': adf_result[1] < significance_level
            }
        except Exception as e:
            logger.warning(f"ADF test failed: {e}")
            results['adf'] = {'error': str(e)}
        
        # KPSS test
        try:
            kpss_result = kpss(series_clean, regression='c')
            results['kpss'] = {
                'statistic': kpss_result[0],
                'p_value': kpss_result[1],
                'critical_values': kpss_result[3],
                'is_stationary': kpss_result[1] > significance_level
            }
        except Exception as e:
            logger.warning(f"KPSS test failed: {e}")
            results['kpss'] = {'error': str(e)}
        
        # Overall conclusion
        adf_stationary = results.get('adf', {}).get('is_stationary', False)
        kpss_stationary = results.get('kpss', {}).get('is_stationary', False)
        
        if adf_stationary and kpss_stationary:
            results['conclusion'] = 'stationary'
        elif not adf_stationary and not kpss_stationary:
            results['conclusion'] = 'non_stationary'
        else:
            results['conclusion'] = 'inconclusive'
        
        return results
    
    def _basic_stationarity_test(self, series: pd.Series) -> Dict:
        """Basic stationarity assessment without statsmodels."""
        series_clean = series.dropna()
        
        # Split series into two halves and compare means/variances
        mid_point = len(series_clean) // 2
        first_half = series_clean[:mid_point]
        second_half = series_clean[mid_point:]
        
        # T-test for mean difference
        t_stat, p_value = stats.ttest_ind(first_half, second_half)
        
        # F-test for variance difference
        f_stat = np.var(first_half) / np.var(second_half)
        
        return {
            'basic_test': {
                'mean_difference_p_value': p_value,
                'variance_ratio': f_stat,
                'likely_stationary': p_value > 0.05 and 0.5 < f_stat < 2.0
            },
            'conclusion': 'likely_stationary' if p_value > 0.05 else 'likely_non_stationary'
        }
    
    def seasonal_decompose(self, series: pd.Series, 
                          model: str = 'additive',
                          period: Optional[int] = None) -> SeasonalDecomposition:
        """
        Perform seasonal decomposition of time series.
        
        Args:
            series: Time series data
            model: 'additive' or 'multiplicative'
            period: Seasonal period (auto-detected if None)
            
        Returns:
            SeasonalDecomposition object
        """
        if not STATSMODELS_AVAILABLE:
            return self._basic_seasonal_decompose(series, period)
        
        series_clean = series.dropna()
        
        # Auto-detect period if not provided
        if period is None:
            if isinstance(series.index, pd.DatetimeIndex):
                freq = pd.infer_freq(series.index)
                if freq and 'D' in freq:
                    period = 365  # Daily data, annual cycle
                elif freq and ('M' in freq or 'MS' in freq):
                    period = 12   # Monthly data, annual cycle
                else:
                    period = min(len(series_clean) // 3, 365)  # Default
            else:
                period = min(len(series_clean) // 3, 12)
        
        try:
            decomposition = seasonal_decompose(
                series_clean, model=model, period=period, extrapolate_trend='freq'
            )
            
            # Calculate seasonal and trend strength
            seasonal_strength = self._calculate_seasonal_strength(
                decomposition.seasonal, decomposition.resid
            )
            
            trend_strength = self._calculate_trend_strength(
                decomposition.trend, decomposition.resid
            )
            
            return SeasonalDecomposition(
                original=decomposition.observed,
                trend=decomposition.trend,
                seasonal=decomposition.seasonal,
                residual=decomposition.resid,
                seasonal_strength=seasonal_strength,
                trend_strength=trend_strength
            )
            
        except Exception as e:
            logger.error(f"Seasonal decomposition failed: {e}")
            return self._basic_seasonal_decompose(series, period)
    
    def _basic_seasonal_decompose(self, series: pd.Series, 
                                 period: Optional[int] = None) -> SeasonalDecomposition:
        """Basic seasonal decomposition without statsmodels."""
        series_clean = series.dropna()
        
        if period is None:
            period = 12  # Default to annual cycle
        
        # Simple moving average for trend
        trend = series_clean.rolling(window=period, center=True).mean()
        
        # Detrended series
        detrended = series_clean - trend
        
        # Simple seasonal component (average by period)
        seasonal_pattern = []
        for i in range(period):
            period_values = detrended.iloc[i::period].dropna()
            if len(period_values) > 0:
                seasonal_pattern.append(period_values.mean())
            else:
                seasonal_pattern.append(0)
        
        # Repeat seasonal pattern
        seasonal = pd.Series(
            [seasonal_pattern[i % period] for i in range(len(series_clean))],
            index=series_clean.index
        )
        
        # Residual
        residual = series_clean - trend - seasonal
        
        return SeasonalDecomposition(
            original=series_clean,
            trend=trend,
            seasonal=seasonal,
            residual=residual,
            seasonal_strength=0.5,  # Placeholder
            trend_strength=0.5      # Placeholder
        )
    
    def _calculate_seasonal_strength(self, seasonal: pd.Series, 
                                   residual: pd.Series) -> float:
        """Calculate seasonal strength."""
        seasonal_var = seasonal.var()
        residual_var = residual.var()
        
        if seasonal_var + residual_var == 0:
            return 0.0
        
        return seasonal_var / (seasonal_var + residual_var)
    
    def _calculate_trend_strength(self, trend: pd.Series, 
                                residual: pd.Series) -> float:
        """Calculate trend strength."""
        trend_clean = trend.dropna()
        residual_clean = residual.dropna()
        
        if len(trend_clean) < 2:
            return 0.0
        
        trend_var = trend_clean.var()
        residual_var = residual_clean.var()
        
        if trend_var + residual_var == 0:
            return 0.0
        
        return trend_var / (trend_var + residual_var)
    
    def detect_changepoints(self, series: pd.Series, 
                           min_size: int = 30) -> List[Dict]:
        """
        Detect change points in time series using statistical methods.
        
        Args:
            series: Time series data
            min_size: Minimum segment size
            
        Returns:
            List of change point information
        """
        series_clean = series.dropna()
        
        if len(series_clean) < min_size * 2:
            return []
        
        changepoints = []
        
        # Simple method: sliding window t-test
        window_size = min_size
        
        for i in range(window_size, len(series_clean) - window_size):
            before = series_clean.iloc[max(0, i - window_size):i]
            after = series_clean.iloc[i:i + window_size]
            
            if len(before) > 5 and len(after) > 5:
                t_stat, p_value = stats.ttest_ind(before, after)
                
                if p_value < 0.01:  # Significant change
                    changepoint = {
                        'index': i,
                        'date': series_clean.index[i] if hasattr(series_clean.index, 'to_pydatetime') else i,
                        't_statistic': t_stat,
                        'p_value': p_value,
                        'mean_before': before.mean(),
                        'mean_after': after.mean(),
                        'change_magnitude': after.mean() - before.mean()
                    }
                    changepoints.append(changepoint)
        
        # Remove nearby changepoints (keep strongest)
        filtered_changepoints = []
        for cp in changepoints:
            # Check if too close to existing changepoints
            too_close = False
            for existing_cp in filtered_changepoints:
                if abs(cp['index'] - existing_cp['index']) < min_size:
                    # Keep the one with smaller p-value
                    if cp['p_value'] < existing_cp['p_value']:
                        filtered_changepoints.remove(existing_cp)
                    else:
                        too_close = True
                    break
            
            if not too_close:
                filtered_changepoints.append(cp)
        
        return sorted(filtered_changepoints, key=lambda x: x['index'])
    
    def apply_filter(self, series: pd.Series, 
                    filter_type: str = 'butterworth',
                    cutoff_freq: float = 0.1,
                    filter_order: int = 4) -> pd.Series:
        """
        Apply digital filter to time series.
        
        Args:
            series: Input time series
            filter_type: 'butterworth', 'moving_average', or 'savgol'
            cutoff_freq: Cutoff frequency (for Butterworth)
            filter_order: Filter order
            
        Returns:
            Filtered time series
        """
        series_clean = series.dropna()
        
        if len(series_clean) < 10:
            return series_clean
        
        if filter_type == 'butterworth' and SCIPY_AVAILABLE:
            try:
                # Butterworth low-pass filter
                nyquist = 0.5  # Normalized frequency
                normal_cutoff = cutoff_freq / nyquist
                b, a = butter(filter_order, normal_cutoff, btype='low', analog=False)
                filtered_values = filtfilt(b, a, series_clean.values)
                
                return pd.Series(filtered_values, index=series_clean.index)
                
            except Exception as e:
                logger.warning(f"Butterworth filter failed: {e}")
                filter_type = 'moving_average'
        
        if filter_type == 'moving_average':
            # Simple moving average
            window_size = max(3, int(1.0 / cutoff_freq))
            return series_clean.rolling(window=window_size, center=True).mean()
        
        elif filter_type == 'savgol' and SCIPY_AVAILABLE:
            # Savitzky-Golay filter
            try:
                window_length = max(5, int(1.0 / cutoff_freq))
                if window_length % 2 == 0:
                    window_length += 1  # Must be odd
                
                window_length = min(window_length, len(series_clean))
                polyorder = min(filter_order, window_length - 1)
                
                filtered_values = signal.savgol_filter(
                    series_clean.values, window_length, polyorder
                )
                
                return pd.Series(filtered_values, index=series_clean.index)
                
            except Exception as e:
                logger.warning(f"Savitzky-Golay filter failed: {e}")
                return series_clean
        
        return series_clean


class TrendAnalyzer:
    """
    Analyze trends in soil moisture time series.
    """
    
    def __init__(self):
        pass
    
    def analyze_trend(self, series: pd.Series, 
                     method: str = 'linear') -> TrendResult:
        """
        Analyze trend in time series.
        
        Args:
            series: Time series data
            method: 'linear', 'theil_sen', or 'polynomial'
            
        Returns:
            TrendResult object
        """
        series_clean = series.dropna()
        
        if len(series_clean) < 3:
            return TrendResult(0, 0, 0, 1, 0, 'insufficient_data', 'not_significant', 'none')
        
        # Create time index
        x = np.arange(len(series_clean))
        y = series_clean.values
        
        if method == 'linear':
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
            
        elif method == 'theil_sen':
            try:
                slope, intercept = stats.theilslopes(y, x)[:2]
                # Approximate p-value and r-value for Theil-Sen
                r_value = np.corrcoef(x, y)[0, 1]
                p_value = self._approximate_p_value(slope, len(x))
                std_err = 0  # Not available for Theil-Sen
                
            except Exception as e:
                logger.warning(f"Theil-Sen failed: {e}")
                slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        
        else:  # polynomial
            # Use degree 2 polynomial
            try:
                poly_coeffs = np.polyfit(x, y, 2)
                poly_func = np.poly1d(poly_coeffs)
                y_pred = poly_func(x)
                
                # Linear approximation for reporting
                slope = (y_pred[-1] - y_pred[0]) / (len(x) - 1)
                intercept = y_pred[0]
                r_value = np.corrcoef(y, y_pred)[0, 1]
                
                # Approximate p-value
                p_value = self._approximate_p_value(slope, len(x))
                std_err = 0  # Placeholder
                
            except Exception as e:
                logger.warning(f"Polynomial fit failed: {e}")
                slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        
        # Determine trend characteristics
        trend_direction = self._classify_trend_direction(slope, p_value)
        significance = self._classify_significance(p_value)
        trend_magnitude = self._classify_magnitude(slope, series_clean.std())
        
        return TrendResult(
            slope=slope,
            intercept=intercept,
            r_value=r_value,
            p_value=p_value,
            std_err=std_err,
            trend_direction=trend_direction,
            significance=significance,
            trend_magnitude=trend_magnitude
        )
    
    def _approximate_p_value(self, slope: float, n: int) -> float:
        """Approximate p-value for trend significance."""
        if n < 3:
            return 1.0
        
        # Very rough approximation
        t_stat = abs(slope) * np.sqrt(n - 2) / (1e-8 + abs(slope))
        return 2 * (1 - stats.t.cdf(abs(t_stat), n - 2))
    
    def _classify_trend_direction(self, slope: float, p_value: float) -> str:
        """Classify trend direction."""
        if p_value > 0.05:
            return 'no_trend'
        elif slope > 0:
            return 'increasing'
        elif slope < 0:
            return 'decreasing'
        else:
            return 'no_trend'
    
    def _classify_significance(self, p_value: float) -> str:
        """Classify statistical significance."""
        if p_value < 0.001:
            return 'highly_significant'
        elif p_value < 0.01:
            return 'very_significant'
        elif p_value < 0.05:
            return 'significant'
        elif p_value < 0.1:
            return 'marginally_significant'
        else:
            return 'not_significant'
    
    def _classify_magnitude(self, slope: float, series_std: float) -> str:
        """Classify trend magnitude."""
        if series_std == 0:
            return 'none'
        
        normalized_slope = abs(slope) / series_std
        
        if normalized_slope > 0.1:
            return 'large'
        elif normalized_slope > 0.05:
            return 'moderate'
        elif normalized_slope > 0.01:
            return 'small'
        else:
            return 'negligible'
    
    def seasonal_trend_analysis(self, series: pd.Series) -> Dict:
        """
        Analyze trends by season.
        
        Args:
            series: Time series with datetime index
            
        Returns:
            Dictionary with seasonal trend results
        """
        if not isinstance(series.index, pd.DatetimeIndex):
            logger.warning("Seasonal trend analysis requires datetime index")
            return {}
        
        seasonal_trends = {}
        
        # Define seasons
        seasons = {
            'spring': [3, 4, 5],
            'summer': [6, 7, 8],
            'fall': [9, 10, 11],
            'winter': [12, 1, 2]
        }
        
        for season_name, months in seasons.items():
            seasonal_data = series[series.index.month.isin(months)]
            
            if len(seasonal_data) > 10:
                trend_result = self.analyze_trend(seasonal_data)
                seasonal_trends[season_name] = {
                    'slope': trend_result.slope,
                    'p_value': trend_result.p_value,
                    'direction': trend_result.trend_direction,
                    'significance': trend_result.significance,
                    'n_points': len(seasonal_data)
                }
        
        return seasonal_trends
