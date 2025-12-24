"""
Climatology and seasonal analysis for soil moisture data.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
import logging
from dataclasses import dataclass
from scipy import stats
import warnings

logger = logging.getLogger(__name__)


@dataclass
class SeasonalStats:
    """Seasonal statistics for soil moisture data."""
    season: str
    mean: float
    std: float
    min: float
    max: float
    median: float
    q25: float
    q75: float
    n_samples: int
    cv: float  # Coefficient of variation


@dataclass
class ClimatologyResult:
    """Results from climatology analysis."""
    long_term_mean: float
    long_term_std: float
    seasonal_stats: Dict[str, SeasonalStats]
    monthly_climatology: pd.Series
    annual_cycle_amplitude: float
    annual_cycle_phase: int  # Month of maximum
    interannual_variability: float


class ClimatologyAnalyzer:
    """
    Analyze climatological patterns in soil moisture data.
    """
    
    def __init__(self):
        self.season_definitions = {
            'DJF': [12, 1, 2],    # Winter
            'MAM': [3, 4, 5],     # Spring  
            'JJA': [6, 7, 8],     # Summer
            'SON': [9, 10, 11]    # Fall
        }
    
    def compute_climatology(self, data: pd.Series, 
                          reference_period: Optional[Tuple[str, str]] = None) -> ClimatologyResult:
        """
        Compute climatological statistics.
        
        Args:
            data: Time series with datetime index
            reference_period: Tuple of (start_date, end_date) for reference period
            
        Returns:
            ClimatologyResult object
        """
        if not isinstance(data.index, pd.DatetimeIndex):
            raise ValueError("Data must have datetime index for climatology analysis")
        
        # Filter to reference period if specified
        if reference_period:
            start_date, end_date = reference_period
            data = data[start_date:end_date]
        
        data_clean = data.dropna()
        
        if len(data_clean) == 0:
            raise ValueError("No valid data for climatology computation")
        
        # Long-term statistics
        long_term_mean = float(data_clean.mean())
        long_term_std = float(data_clean.std())
        
        # Monthly climatology
        monthly_climatology = data_clean.groupby(data_clean.index.month).mean()
        
        # Annual cycle characteristics
        annual_cycle_amplitude = float(monthly_climatology.max() - monthly_climatology.min())
        annual_cycle_phase = int(monthly_climatology.idxmax())
        
        # Seasonal statistics
        seasonal_stats = {}
        for season, months in self.season_definitions.items():
            seasonal_data = data_clean[data_clean.index.month.isin(months)]
            
            if len(seasonal_data) > 0:
                seasonal_stats[season] = SeasonalStats(
                    season=season,
                    mean=float(seasonal_data.mean()),
                    std=float(seasonal_data.std()),
                    min=float(seasonal_data.min()),
                    max=float(seasonal_data.max()),
                    median=float(seasonal_data.median()),
                    q25=float(seasonal_data.quantile(0.25)),
                    q75=float(seasonal_data.quantile(0.75)),
                    n_samples=len(seasonal_data),
                    cv=float(seasonal_data.std() / seasonal_data.mean()) if seasonal_data.mean() != 0 else np.inf
                )
        
        # Interannual variability
        annual_means = data_clean.groupby(data_clean.index.year).mean()
        interannual_variability = float(annual_means.std()) if len(annual_means) > 1 else 0.0
        
        return ClimatologyResult(
            long_term_mean=long_term_mean,
            long_term_std=long_term_std,
            seasonal_stats=seasonal_stats,
            monthly_climatology=monthly_climatology,
            annual_cycle_amplitude=annual_cycle_amplitude,
            annual_cycle_phase=annual_cycle_phase,
            interannual_variability=interannual_variability
        )
    
    def compute_anomalies(self, data: pd.Series, 
                         climatology: Optional[ClimatologyResult] = None,
                         anomaly_type: str = 'absolute') -> pd.Series:
        """
        Compute climatological anomalies.
        
        Args:
            data: Time series data
            climatology: Pre-computed climatology (computed if None)
            anomaly_type: 'absolute', 'relative', or 'standardized'
            
        Returns:
            Time series of anomalies
        """
        if not isinstance(data.index, pd.DatetimeIndex):
            raise ValueError("Data must have datetime index")
        
        if climatology is None:
            climatology = self.compute_climatology(data)
        
        # Create monthly climatology series aligned with data
        monthly_clim = data.index.month.map(climatology.monthly_climatology)
        
        if anomaly_type == 'absolute':
            anomalies = data - monthly_clim
        elif anomaly_type == 'relative':
            anomalies = (data - monthly_clim) / monthly_clim * 100
        elif anomaly_type == 'standardized':
            # Use long-term standard deviation for standardization
            anomalies = (data - monthly_clim) / climatology.long_term_std
        else:
            raise ValueError("anomaly_type must be 'absolute', 'relative', or 'standardized'")
        
        return anomalies
    
    def detect_extreme_events(self, data: pd.Series,
                            threshold_type: str = 'percentile',
                            threshold_value: float = 5.0) -> pd.DataFrame:
        """
        Detect extreme dry/wet events.
        
        Args:
            data: Time series data
            threshold_type: 'percentile', 'std_dev', or 'absolute'
            threshold_value: Threshold value (percentile, std devs, or absolute)
            
        Returns:
            DataFrame with extreme events
        """
        data_clean = data.dropna()
        
        if len(data_clean) == 0:
            return pd.DataFrame()
        
        # Determine thresholds
        if threshold_type == 'percentile':
            dry_threshold = data_clean.quantile(threshold_value / 100)
            wet_threshold = data_clean.quantile(1 - threshold_value / 100)
        elif threshold_type == 'std_dev':
            mean_val = data_clean.mean()
            std_val = data_clean.std()
            dry_threshold = mean_val - threshold_value * std_val
            wet_threshold = mean_val + threshold_value * std_val
        elif threshold_type == 'absolute':
            dry_threshold = threshold_value
            wet_threshold = data_clean.max() - threshold_value  # Arbitrary for wet events
        else:
            raise ValueError("threshold_type must be 'percentile', 'std_dev', or 'absolute'")
        
        # Find extreme events
        extreme_events = []
        
        for date, value in data_clean.items():
            if value <= dry_threshold:
                extreme_events.append({
                    'date': date,
                    'value': value,
                    'type': 'dry',
                    'severity': (dry_threshold - value) / data_clean.std(),
                    'percentile': stats.percentileofscore(data_clean.values, value)
                })
            elif value >= wet_threshold:
                extreme_events.append({
                    'date': date,
                    'value': value,
                    'type': 'wet',
                    'severity': (value - wet_threshold) / data_clean.std(),
                    'percentile': stats.percentileofscore(data_clean.values, value)
                })
        
        return pd.DataFrame(extreme_events)
    
    def analyze_trends_by_season(self, data: pd.Series) -> Dict[str, Dict]:
        """
        Analyze long-term trends by season.
        
        Args:
            data: Time series with datetime index
            
        Returns:
            Dictionary with seasonal trend analysis
        """
        if not isinstance(data.index, pd.DatetimeIndex):
            raise ValueError("Data must have datetime index")
        
        seasonal_trends = {}
        
        for season, months in self.season_definitions.items():
            # Get seasonal data
            seasonal_data = data[data.index.month.isin(months)]
            
            if len(seasonal_data) < 10:  # Need minimum data for trend analysis
                continue
            
            # Group by year to get annual seasonal means
            annual_seasonal = seasonal_data.groupby(seasonal_data.index.year).mean()
            
            if len(annual_seasonal) < 3:  # Need minimum years
                continue
            
            # Linear trend analysis
            years = np.array(annual_seasonal.index)
            values = annual_seasonal.values
            
            try:
                slope, intercept, r_value, p_value, std_err = stats.linregress(years, values)
                
                # Trend per decade
                trend_per_decade = slope * 10
                
                seasonal_trends[season] = {
                    'slope': float(slope),
                    'trend_per_decade': float(trend_per_decade),
                    'r_squared': float(r_value ** 2),
                    'p_value': float(p_value),
                    'significance': 'significant' if p_value < 0.05 else 'not_significant',
                    'direction': 'increasing' if slope > 0 else 'decreasing' if slope < 0 else 'no_trend',
                    'n_years': len(annual_seasonal)
                }
                
            except Exception as e:
                logger.warning(f"Trend analysis failed for {season}: {e}")
                continue
        
        return seasonal_trends


class SeasonalAnalyzer:
    """
    Detailed seasonal pattern analysis.
    """
    
    def __init__(self):
        pass
    
    def analyze_seasonal_cycle(self, data: pd.Series) -> Dict:
        """
        Analyze the seasonal cycle characteristics.
        
        Args:
            data: Time series with datetime index
            
        Returns:
            Dictionary with seasonal cycle analysis
        """
        if not isinstance(data.index, pd.DatetimeIndex):
            raise ValueError("Data must have datetime index")
        
        data_clean = data.dropna()
        
        # Monthly statistics
        monthly_stats = data_clean.groupby(data_clean.index.month).agg([
            'mean', 'std', 'min', 'max', 'count'
        ])
        
        # Seasonal cycle characteristics
        monthly_means = monthly_stats['mean']
        
        # Find peaks and troughs
        max_month = int(monthly_means.idxmax())
        min_month = int(monthly_means.idxmin())
        amplitude = float(monthly_means.max() - monthly_means.min())
        
        # Seasonal transition dates
        transitions = self._find_seasonal_transitions(monthly_means)
        
        # Seasonality strength (based on variance explained by monthly means)
        total_var = data_clean.var()
        seasonal_var = data_clean.groupby(data_clean.index.month).transform('mean').var()
        seasonality_strength = float(seasonal_var / total_var) if total_var > 0 else 0
        
        return {
            'monthly_statistics': monthly_stats.to_dict(),
            'amplitude': amplitude,
            'maximum_month': max_month,
            'minimum_month': min_month,
            'seasonality_strength': seasonality_strength,
            'seasonal_transitions': transitions,
            'is_strongly_seasonal': seasonality_strength > 0.3
        }
    
    def _find_seasonal_transitions(self, monthly_means: pd.Series) -> Dict:
        """Find seasonal transition months."""
        # Simple approach: find months with largest changes
        monthly_changes = monthly_means.diff().abs()
        
        # Handle December-January transition
        dec_jan_change = abs(monthly_means.iloc[0] - monthly_means.iloc[-1])
        monthly_changes.iloc[0] = dec_jan_change
        
        # Sort by magnitude of change
        sorted_changes = monthly_changes.sort_values(ascending=False)
        
        return {
            'largest_increase_month': int(monthly_means.diff().idxmax()),
            'largest_decrease_month': int(monthly_means.diff().idxmin()),
            'most_variable_transition': int(sorted_changes.index[0])
        }
    
    def compare_years(self, data: pd.Series, 
                     reference_years: Optional[List[int]] = None) -> Dict:
        """
        Compare seasonal patterns across different years.
        
        Args:
            data: Time series with datetime index
            reference_years: Specific years to analyze (all years if None)
            
        Returns:
            Dictionary with year comparison results
        """
        if not isinstance(data.index, pd.DatetimeIndex):
            raise ValueError("Data must have datetime index")
        
        data_clean = data.dropna()
        
        if reference_years:
            data_clean = data_clean[data_clean.index.year.isin(reference_years)]
        
        # Group by year and month
        yearly_monthly = data_clean.groupby([data_clean.index.year, data_clean.index.month]).mean()
        
        year_comparison = {}
        available_years = yearly_monthly.index.get_level_values(0).unique()
        
        for year in available_years:
            try:
                year_data = yearly_monthly[year]
                
                year_comparison[int(year)] = {
                    'annual_mean': float(year_data.mean()),
                    'annual_std': float(year_data.std()),
                    'seasonal_amplitude': float(year_data.max() - year_data.min()),
                    'max_month': int(year_data.idxmax()),
                    'min_month': int(year_data.idxmin()),
                    'available_months': len(year_data)
                }
                
            except Exception as e:
                logger.warning(f"Year comparison failed for {year}: {e}")
                continue
        
        # Calculate inter-annual statistics
        if len(year_comparison) > 1:
            annual_means = [stats['annual_mean'] for stats in year_comparison.values()]
            annual_amplitudes = [stats['seasonal_amplitude'] for stats in year_comparison.values()]
            
            inter_annual_stats = {
                'mean_annual_mean': float(np.mean(annual_means)),
                'std_annual_mean': float(np.std(annual_means)),
                'mean_seasonal_amplitude': float(np.mean(annual_amplitudes)),
                'std_seasonal_amplitude': float(np.std(annual_amplitudes)),
                'cv_interannual': float(np.std(annual_means) / np.mean(annual_means)) if np.mean(annual_means) != 0 else np.inf
            }
        else:
            inter_annual_stats = {}
        
        return {
            'yearly_comparison': year_comparison,
            'inter_annual_statistics': inter_annual_stats,
            'n_years': len(year_comparison)
        }
    
    def phenology_analysis(self, data: pd.Series,
                          growth_threshold: Optional[float] = None) -> Dict:
        """
        Analyze soil moisture phenology (seasonal timing).
        
        Args:
            data: Time series with datetime index
            growth_threshold: Threshold for "growing season" soil moisture
            
        Returns:
            Dictionary with phenology metrics
        """
        if not isinstance(data.index, pd.DatetimeIndex):
            raise ValueError("Data must have datetime index")
        
        data_clean = data.dropna()
        
        if growth_threshold is None:
            # Use 60th percentile as growth threshold
            growth_threshold = data_clean.quantile(0.6)
        
        phenology_metrics = {}
        
        # Analyze each year
        years = data_clean.index.year.unique()
        
        yearly_phenology = {}
        
        for year in years:
            year_data = data_clean[data_clean.index.year == year]
            
            if len(year_data) < 50:  # Need sufficient data
                continue
            
            # Find growing season start and end
            above_threshold = year_data > growth_threshold
            
            # Find first sustained period above threshold
            growing_season_start = None
            growing_season_end = None
            
            # Simple approach: first and last dates above threshold
            if above_threshold.any():
                growing_season_start = above_threshold.idxmax()
                # Find last date above threshold
                above_threshold_reversed = above_threshold[::-1]
                growing_season_end = above_threshold_reversed.idxmax()
            
            yearly_phenology[int(year)] = {
                'growing_season_start': growing_season_start,
                'growing_season_end': growing_season_end,
                'growing_season_length': (growing_season_end - growing_season_start).days if growing_season_start and growing_season_end else None,
                'peak_moisture_date': year_data.idxmax(),
                'peak_moisture_value': float(year_data.max()),
                'minimum_moisture_date': year_data.idxmin(),
                'minimum_moisture_value': float(year_data.min())
            }
        
        # Calculate average phenology
        if yearly_phenology:
            growing_lengths = [p['growing_season_length'] for p in yearly_phenology.values() 
                             if p['growing_season_length'] is not None]
            
            peak_doys = []  # Day of year for peaks
            for p in yearly_phenology.values():
                if p['peak_moisture_date']:
                    peak_doys.append(p['peak_moisture_date'].dayofyear)
            
            phenology_metrics = {
                'average_growing_season_length': float(np.mean(growing_lengths)) if growing_lengths else None,
                'std_growing_season_length': float(np.std(growing_lengths)) if len(growing_lengths) > 1 else None,
                'average_peak_day_of_year': float(np.mean(peak_doys)) if peak_doys else None,
                'std_peak_day_of_year': float(np.std(peak_doys)) if len(peak_doys) > 1 else None,
                'yearly_phenology': yearly_phenology
            }
        
        return phenology_metrics
