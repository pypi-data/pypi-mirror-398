"""
Tests for machine learning functionality.
"""

import pytest
import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error
import logging

from soilmoisture.ml.models import (
    SoilMoisturePredictor, 
    AnomalyDetector,
    TimeSeriesForecaster
)
from soilmoisture.ml.features import (
    FeatureEngineer,
    create_temporal_features,
    create_weather_features,
    select_features
)

logger = logging.getLogger(__name__)


@pytest.fixture
def sample_data():
    """Create sample soil moisture data for testing."""
    np.random.seed(42)
    dates = pd.date_range('2015-01-01', '2015-12-31', freq='D')
    n_days = len(dates)
    
    # Create synthetic data with seasonal pattern
    day_of_year = np.arange(1, n_days + 1)
    seasonal = 0.1 * np.sin(2 * np.pi * day_of_year / 365) + 0.2
    noise = np.random.normal(0, 0.02, n_days)
    
    data = {
        'date': dates,
        'in_situ': seasonal + noise,
        'satellite': seasonal + noise * 1.5 + 0.05,  # Satellite has bias and more noise
        'temperature': 15 + 10 * np.sin(2 * np.pi * day_of_year / 365) + np.random.normal(0, 2, n_days),
        'precipitation': np.random.exponential(2, n_days)  # Exponential distribution for precip
    }
    
    return pd.DataFrame(data)


class TestSoilMoisturePredictor:
    """Test the SoilMoisturePredictor class."""
    
    def test_initialization(self):
        """Test predictor initialization."""
        predictor = SoilMoisturePredictor(model_type='random_forest')
        assert predictor.model_type == 'random_forest'
        assert not predictor.is_fitted
    
    def test_feature_preparation(self, sample_data):
        """Test feature preparation."""
        predictor = SoilMoisturePredictor()
        features = predictor.prepare_features(sample_data)
        
        # Check that temporal features are created
        assert 'day_of_year' in features.columns
        assert 'month' in features.columns
        assert 'season' in features.columns
        
        # Check that satellite features are created
        assert 'satellite_ma3' in features.columns
        assert 'satellite_lag1' in features.columns
    
    def test_random_forest_training(self, sample_data):
        """Test Random Forest model training."""
        predictor = SoilMoisturePredictor(model_type='random_forest')
        features = predictor.prepare_features(sample_data)
        
        # Select features (exclude target and date)
        feature_cols = [col for col in features.columns 
                       if col not in ['in_situ', 'date'] and not features[col].isna().all()]
        
        X = features[feature_cols].dropna()
        y = features.loc[X.index, 'in_situ']
        
        # Train model
        metrics = predictor.fit(X, y)
        
        assert predictor.is_fitted
        assert 'val_rmse' in metrics
        assert 'val_r2' in metrics
        assert metrics['val_rmse'] > 0
    
    def test_prediction(self, sample_data):
        """Test making predictions."""
        predictor = SoilMoisturePredictor(model_type='random_forest')
        features = predictor.prepare_features(sample_data)
        
        feature_cols = [col for col in features.columns 
                       if col not in ['in_situ', 'date'] and not features[col].isna().all()]
        
        X = features[feature_cols].dropna()
        y = features.loc[X.index, 'in_situ']
        
        # Train and predict
        predictor.fit(X, y)
        predictions = predictor.predict(X[:10])  # Predict first 10 samples
        
        assert len(predictions) == 10
        assert all(np.isfinite(predictions))
    
    def test_feature_importance(self, sample_data):
        """Test feature importance extraction."""
        predictor = SoilMoisturePredictor(model_type='random_forest')
        features = predictor.prepare_features(sample_data)
        
        feature_cols = [col for col in features.columns 
                       if col not in ['in_situ', 'date'] and not features[col].isna().all()]
        
        X = features[feature_cols].dropna()
        y = features.loc[X.index, 'in_situ']
        
        predictor.fit(X, y)
        importance = predictor.get_feature_importance()
        
        assert importance is not None
        assert isinstance(importance, dict)
        assert len(importance) == len(feature_cols)


class TestAnomalyDetector:
    """Test the AnomalyDetector class."""
    
    def test_initialization(self):
        """Test detector initialization."""
        detector = AnomalyDetector(method='isolation_forest')
        assert detector.method == 'isolation_forest'
        assert not detector.is_fitted
    
    def test_isolation_forest_detection(self, sample_data):
        """Test Isolation Forest anomaly detection."""
        detector = AnomalyDetector(method='isolation_forest')
        
        # Use satellite data as features
        X = sample_data[['satellite']].dropna()
        detector.fit(X)
        
        assert detector.is_fitted
        
        # Detect anomalies
        anomaly_labels, anomaly_scores = detector.detect_anomalies(X)
        
        assert len(anomaly_labels) == len(X)
        assert len(anomaly_scores) == len(X)
        assert anomaly_labels.dtype == bool
        
        # Should detect some anomalies but not too many
        anomaly_rate = anomaly_labels.sum() / len(anomaly_labels)
        assert 0.0 <= anomaly_rate <= 0.3  # Should be reasonable
    
    def test_statistical_detection(self, sample_data):
        """Test statistical anomaly detection."""
        detector = AnomalyDetector(method='statistical')
        
        X = sample_data[['satellite']].dropna()
        detector.fit(X)
        
        anomaly_labels, anomaly_scores = detector.detect_anomalies(X)
        
        assert len(anomaly_labels) == len(X)
        assert all(score >= 0 for score in anomaly_scores)  # Z-scores should be positive


class TestTimeSeriesForecaster:
    """Test the TimeSeriesForecaster class."""
    
    def test_initialization(self):
        """Test forecaster initialization."""
        forecaster = TimeSeriesForecaster(model_type='linear', forecast_horizon=7)
        assert forecaster.model_type == 'linear'
        assert forecaster.forecast_horizon == 7
        assert not forecaster.is_fitted
    
    def test_linear_forecasting(self, sample_data):
        """Test linear model forecasting."""
        forecaster = TimeSeriesForecaster(model_type='linear', forecast_horizon=5)
        
        # Use in-situ data
        time_series = sample_data['in_situ'].dropna()
        
        # Train
        metrics = forecaster.fit(time_series)
        assert forecaster.is_fitted
        assert 'rmse' in metrics
        
        # Forecast
        forecasts = forecaster.forecast(time_series, steps=5)
        assert len(forecasts) == 5
        assert all(np.isfinite(forecasts))
    
    def test_sequence_creation(self, sample_data):
        """Test sequence creation for LSTM."""
        forecaster = TimeSeriesForecaster(model_type='lstm')
        
        data = np.random.randn(100)
        X, y = forecaster.create_sequences(data)
        
        expected_length = len(data) - forecaster.sequence_length
        assert len(X) == expected_length
        assert len(y) == expected_length
        assert X.shape[1] == forecaster.sequence_length


class TestFeatureEngineer:
    """Test the FeatureEngineer class."""
    
    def test_initialization(self):
        """Test feature engineer initialization."""
        fe = FeatureEngineer()
        assert not fe.is_fitted
        assert fe.seasonal_stats == {}
    
    def test_fit_transform(self, sample_data):
        """Test fit and transform."""
        fe = FeatureEngineer()
        features = fe.fit_transform(sample_data)
        
        assert fe.is_fitted
        assert len(features) <= len(sample_data)  # Some rows might be dropped due to rolling ops
        
        # Check that new features are created
        original_cols = set(sample_data.columns)
        new_cols = set(features.columns) - original_cols
        assert len(new_cols) > 0  # Should have new features
    
    def test_seasonal_features(self, sample_data):
        """Test seasonal feature creation."""
        fe = FeatureEngineer()
        fe.fit(sample_data)
        
        # Check that seasonal stats are computed
        assert 'in_situ_monthly_mean' in fe.seasonal_stats
        assert 'satellite_monthly_mean' in fe.seasonal_stats
        
        features = fe.transform(sample_data)
        assert 'in_situ_seasonal_anomaly' in features.columns
        assert 'satellite_seasonal_anomaly' in features.columns


class TestFeatureFunctions:
    """Test standalone feature creation functions."""
    
    def test_temporal_features(self, sample_data):
        """Test temporal feature creation."""
        features = create_temporal_features(sample_data)
        
        temporal_cols = ['year', 'month', 'day_of_year', 'season', 
                        'month_sin', 'month_cos', 'day_of_year_sin', 'day_of_year_cos']
        
        for col in temporal_cols:
            assert col in features.columns
        
        # Check cyclical encoding
        assert -1 <= features['month_sin'].min() <= 1
        assert -1 <= features['month_cos'].max() <= 1
    
    def test_weather_features(self, sample_data):
        """Test weather feature creation."""
        features = create_weather_features(
            sample_data, 
            temperature_col='temperature',
            precipitation_col='precipitation'
        )
        
        # Should have temperature features
        assert 'temp_ma_3' in features.columns
        assert 'gdd' in features.columns
        
        # Should have precipitation features
        assert 'precip_cumsum_7' in features.columns
        assert 'is_rainy_day' in features.columns
        
        # Should have combined features
        assert 'drought_index' in features.columns
    
    def test_feature_selection(self, sample_data):
        """Test feature selection."""
        # Add some random features
        sample_data['random1'] = np.random.randn(len(sample_data))
        sample_data['random2'] = np.random.randn(len(sample_data))
        
        # Add temporal features
        features = create_temporal_features(sample_data)
        
        selected = select_features(
            features, 
            target_col='in_situ', 
            correlation_threshold=0.01,
            max_features=10
        )
        
        assert isinstance(selected, list)
        assert len(selected) <= 10
        assert 'in_situ' not in selected  # Target should not be in features


class TestIntegration:
    """Integration tests combining multiple components."""
    
    def test_end_to_end_pipeline(self, sample_data):
        """Test complete ML pipeline."""
        # Feature engineering
        fe = FeatureEngineer()
        features = fe.fit_transform(sample_data)
        
        # Feature selection
        feature_cols = select_features(
            features, 
            target_col='in_situ',
            correlation_threshold=0.01,
            max_features=15
        )
        
        # Prepare data
        X = features[feature_cols].dropna()
        y = features.loc[X.index, 'in_situ']
        
        # Train model
        predictor = SoilMoisturePredictor(model_type='random_forest')
        metrics = predictor.fit(X, y)
        
        # Make predictions
        predictions = predictor.predict(X)
        
        # Check results
        assert predictor.is_fitted
        assert len(predictions) == len(y)
        
        # Calculate test RMSE
        rmse = np.sqrt(mean_squared_error(y, predictions))
        assert rmse > 0
        assert rmse < 1.0  # Should be reasonable for synthetic data
        
        logger.debug(f"End-to-end test RMSE: {rmse:.4f}")
        logger.debug(f"Validation RMSE: {metrics['val_rmse']:.4f}")
        logger.debug(f"R² score: {metrics['val_r2']:.4f}")


if __name__ == "__main__":
    pytest.main([__file__])
