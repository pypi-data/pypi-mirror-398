"""
Feature engineering utilities for soil moisture analysis.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """
    Advanced feature engineering for soil moisture data.
    """
    
    def __init__(self):
        self.seasonal_stats = {}
        self.is_fitted = False
    
    def fit(self, df: pd.DataFrame) -> 'FeatureEngineer':
        """
        Fit the feature engineer to learn seasonal patterns and statistics.
        
        Args:
            df: DataFrame with date and soil moisture columns
            
        Returns:
            Self for method chaining
        """
        df = df.copy()
        if 'date' not in df.columns:
            raise ValueError("DataFrame must have a 'date' column")
        
        df['date'] = pd.to_datetime(df['date'])
        df['month'] = df['date'].dt.month
        
        # Learn seasonal patterns
        for col in ['in_situ', 'satellite']:
            if col in df.columns:
                self.seasonal_stats[f'{col}_monthly_mean'] = df.groupby('month')[col].mean()
                self.seasonal_stats[f'{col}_monthly_std'] = df.groupby('month')[col].std()
        
        self.is_fitted = True
        return self
    
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform the DataFrame by adding engineered features.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with additional features
        """
        features = df.copy()
        
        # Temporal features
        features = create_temporal_features(features)
        
        # Statistical features
        features = self._create_statistical_features(features)
        
        # Seasonal features (if fitted)
        if self.is_fitted:
            features = self._create_seasonal_features(features)
        
        # Weather proxy features
        features = self._create_weather_proxy_features(features)
        
        return features
    
    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Fit and transform in one step."""
        return self.fit(df).transform(df)
    
    def _create_statistical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create statistical features like moving averages and differences."""
        features = df.copy()
        
        for col in ['satellite', 'in_situ']:
            if col in features.columns:
                # Moving averages
                for window in [3, 7, 14, 30]:
                    features[f'{col}_ma_{window}'] = features[col].rolling(
                        window=window, center=True
                    ).mean()
                
                # Moving standard deviations
                for window in [7, 14]:
                    features[f'{col}_std_{window}'] = features[col].rolling(
                        window=window, center=True
                    ).std()
                
                # Lag features
                for lag in [1, 3, 7]:
                    features[f'{col}_lag_{lag}'] = features[col].shift(lag)
                
                # Differences
                features[f'{col}_diff_1'] = features[col].diff(1)
                features[f'{col}_diff_7'] = features[col].diff(7)
                
                # Rate of change
                features[f'{col}_roc_3'] = (features[col] / features[col].shift(3) - 1) * 100
                features[f'{col}_roc_7'] = (features[col] / features[col].shift(7) - 1) * 100
        
        return features
    
    def _create_seasonal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create seasonal anomaly features."""
        if not self.is_fitted:
            return df
        
        features = df.copy()
        
        if 'date' in features.columns:
            features['date'] = pd.to_datetime(features['date'])
            features['month'] = features['date'].dt.month
            
            # Seasonal anomalies
            for col in ['in_situ', 'satellite']:
                if col in features.columns and f'{col}_monthly_mean' in self.seasonal_stats:
                    monthly_mean = features['month'].map(self.seasonal_stats[f'{col}_monthly_mean'])
                    monthly_std = features['month'].map(self.seasonal_stats[f'{col}_monthly_std'])
                    
                    features[f'{col}_seasonal_anomaly'] = (features[col] - monthly_mean) / monthly_std
                    features[f'{col}_monthly_mean'] = monthly_mean
                    features[f'{col}_monthly_std'] = monthly_std
        
        return features
    
    def _create_weather_proxy_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create proxy features for weather patterns."""
        features = df.copy()
        
        if 'satellite' in features.columns:
            # Drying/wetting patterns
            features['is_drying'] = (features['satellite'].diff() < 0).astype(int)
            features['is_wetting'] = (features['satellite'].diff() > 0).astype(int)
            
            # Consecutive dry/wet days
            features['consecutive_drying'] = features['is_drying'].groupby(
                (features['is_drying'] != features['is_drying'].shift()).cumsum()
            ).cumsum()
            
            features['consecutive_wetting'] = features['is_wetting'].groupby(
                (features['is_wetting'] != features['is_wetting'].shift()).cumsum()
            ).cumsum()
            
            # Extreme values indicators
            if len(features['satellite'].dropna()) > 10:
                q90 = features['satellite'].quantile(0.9)
                q10 = features['satellite'].quantile(0.1)
                features['is_wet_extreme'] = (features['satellite'] > q90).astype(int)
                features['is_dry_extreme'] = (features['satellite'] < q10).astype(int)
        
        return features


def create_temporal_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create temporal features from date column.
    
    Args:
        df: DataFrame with 'date' column
        
    Returns:
        DataFrame with additional temporal features
    """
    features = df.copy()
    
    if 'date' not in features.columns:
        return features
    
    features['date'] = pd.to_datetime(features['date'])
    
    # Basic temporal features
    features['year'] = features['date'].dt.year
    features['month'] = features['date'].dt.month
    features['day'] = features['date'].dt.day
    features['day_of_year'] = features['date'].dt.dayofyear
    features['week_of_year'] = features['date'].dt.isocalendar().week
    features['day_of_week'] = features['date'].dt.dayofweek
    
    # Seasonal features
    features['season'] = features['month'].map({
        12: 0, 1: 0, 2: 0,  # Winter
        3: 1, 4: 1, 5: 1,   # Spring  
        6: 2, 7: 2, 8: 2,   # Summer
        9: 3, 10: 3, 11: 3  # Fall
    })
    
    # Cyclical encoding for better ML performance
    features['month_sin'] = np.sin(2 * np.pi * features['month'] / 12)
    features['month_cos'] = np.cos(2 * np.pi * features['month'] / 12)
    features['day_of_year_sin'] = np.sin(2 * np.pi * features['day_of_year'] / 365.25)
    features['day_of_year_cos'] = np.cos(2 * np.pi * features['day_of_year'] / 365.25)
    
    # Days since start of data
    features['days_since_start'] = (features['date'] - features['date'].min()).dt.days
    
    return features


def create_weather_features(df: pd.DataFrame, 
                          temperature_col: Optional[str] = None,
                          precipitation_col: Optional[str] = None,
                          humidity_col: Optional[str] = None) -> pd.DataFrame:
    """
    Create weather-related features if weather data is available.
    
    Args:
        df: Input DataFrame
        temperature_col: Name of temperature column
        precipitation_col: Name of precipitation column
        humidity_col: Name of humidity column
        
    Returns:
        DataFrame with weather-derived features
    """
    features = df.copy()
    
    # Temperature features
    if temperature_col and temperature_col in features.columns:
        temp = features[temperature_col]
        
        # Temperature-based features
        features['temp_ma_3'] = temp.rolling(3).mean()
        features['temp_ma_7'] = temp.rolling(7).mean()
        features['temp_range_7'] = temp.rolling(7).max() - temp.rolling(7).min()
        
        # Growing degree days (assuming base temp of 10°C)
        features['gdd'] = np.maximum(temp - 10, 0).cumsum()
        
        # Freezing days
        features['is_freezing'] = (temp < 0).astype(int)
    
    # Precipitation features
    if precipitation_col and precipitation_col in features.columns:
        precip = features[precipitation_col]
        
        # Cumulative precipitation
        features['precip_cumsum_7'] = precip.rolling(7).sum()
        features['precip_cumsum_14'] = precip.rolling(14).sum()
        features['precip_cumsum_30'] = precip.rolling(30).sum()
        
        # Days since last rain
        rain_days = (precip > 1.0)  # Assuming >1mm is significant rain
        features['days_since_rain'] = rain_days[::-1].groupby(rain_days[::-1].cumsum()).cumcount()[::-1]
        
        # Wet/dry spells
        features['is_rainy_day'] = (precip > 1.0).astype(int)
    
    # Humidity features
    if humidity_col and humidity_col in features.columns:
        humidity = features[humidity_col]
        
        # Humidity statistics
        features['humidity_ma_3'] = humidity.rolling(3).mean()
        features['humidity_ma_7'] = humidity.rolling(7).mean()
        features['humidity_min_7'] = humidity.rolling(7).min()
        features['humidity_max_7'] = humidity.rolling(7).max()
    
    # Combined weather indices
    if temperature_col and precipitation_col:
        temp = features[temperature_col]
        precip = features[precipitation_col]
        
        # Simple drought index (high temp, low precip)
        temp_norm = (temp - temp.mean()) / temp.std()
        precip_norm = (precip - precip.mean()) / precip.std()
        features['drought_index'] = temp_norm - precip_norm
    
    return features


def create_satellite_quality_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create features related to satellite data quality and reliability.
    
    Args:
        df: DataFrame with satellite data
        
    Returns:
        DataFrame with quality-related features
    """
    features = df.copy()
    
    if 'satellite' not in features.columns:
        return features
    
    sat = features['satellite']
    
    # Data availability
    features['satellite_available'] = (~sat.isna()).astype(int)
    features['satellite_gap_length'] = sat.isna().groupby(sat.notna().cumsum()).cumsum()
    
    # Stability indicators
    features['satellite_stability_3'] = sat.rolling(3).std()
    features['satellite_stability_7'] = sat.rolling(7).std()
    
    # Change magnitude
    features['satellite_change_abs'] = sat.diff().abs()
    features['satellite_change_abs_ma3'] = features['satellite_change_abs'].rolling(3).mean()
    
    # Outlier indicators
    if len(sat.dropna()) > 30:
        q99 = sat.quantile(0.99)
        q01 = sat.quantile(0.01)
        features['satellite_outlier_high'] = (sat > q99).astype(int)
        features['satellite_outlier_low'] = (sat < q01).astype(int)
    
    return features


def select_features(df: pd.DataFrame, 
                   target_col: str = 'in_situ',
                   correlation_threshold: float = 0.05,
                   max_features: int = 50) -> List[str]:
    """
    Select the most relevant features for prediction.
    
    Args:
        df: DataFrame with features and target
        target_col: Name of target column
        correlation_threshold: Minimum correlation with target
        max_features: Maximum number of features to select
        
    Returns:
        List of selected feature names
    """
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found")
    
    # Calculate correlations with target
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    correlations = df[numeric_cols].corrwith(df[target_col]).abs().sort_values(ascending=False)
    
    # Filter by correlation threshold
    significant_features = correlations[correlations >= correlation_threshold].index.tolist()
    
    # Remove target from features
    if target_col in significant_features:
        significant_features.remove(target_col)
    
    # Limit number of features
    selected_features = significant_features[:max_features]
    
    logger.info(f"Selected {len(selected_features)} features out of {len(numeric_cols)} total")
    
    return selected_features


def create_interaction_features(df: pd.DataFrame, 
                              feature_pairs: List[Tuple[str, str]]) -> pd.DataFrame:
    """
    Create interaction features between specified feature pairs.
    
    Args:
        df: Input DataFrame
        feature_pairs: List of tuples specifying feature pairs to interact
        
    Returns:
        DataFrame with interaction features
    """
    features = df.copy()
    
    for feat1, feat2 in feature_pairs:
        if feat1 in features.columns and feat2 in features.columns:
            # Multiplicative interaction
            features[f'{feat1}_x_{feat2}'] = features[feat1] * features[feat2]
            
            # Ratio (avoid division by zero)
            safe_feat2 = features[feat2].replace(0, np.nan)
            features[f'{feat1}_div_{feat2}'] = features[feat1] / safe_feat2
            
            # Difference
            features[f'{feat1}_minus_{feat2}'] = features[feat1] - features[feat2]
    
    return features
