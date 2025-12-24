"""
Machine Learning models for utility pole health assessment and failure prediction.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
from sklearn.ensemble import RandomForestRegressor, IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler, MinMaxScaler, LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score, classification_report, roc_auc_score
from sklearn.linear_model import LinearRegression, Ridge, Lasso, LogisticRegression
from sklearn.svm import SVR, SVC
import joblib
import logging
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

try:
    from tensorflow import keras
    from tensorflow.keras import layers
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False

logger = logging.getLogger(__name__)


class PoleFailurePredictionModel:
    """
    Machine learning model for predicting utility pole failure probability.
    
    Supports multiple algorithms including Random Forest, Neural Networks, and SVM.
    """
    
    def __init__(self, model_type: str = 'random_forest'):
        """
        Initialize the failure prediction model.
        
        Args:
            model_type: Type of model ('random_forest', 'neural_network', 'svm', 'logistic')
        """
        self.model_type = model_type
        self.model = None
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.is_fitted = False
        self.feature_names = None
        self.training_history = {}
        
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the model based on model_type."""
        if self.model_type == 'random_forest':
            self.model = RandomForestClassifier(
                n_estimators=200,
                max_depth=15,
                min_samples_split=5,
                min_samples_leaf=2,
                class_weight='balanced',
                random_state=42
            )
        elif self.model_type == 'neural_network':
            if not TENSORFLOW_AVAILABLE:
                logger.warning("TensorFlow not available, falling back to Random Forest")
                self.model_type = 'random_forest'
                self._initialize_model()
                return
            # Will be built dynamically based on input shape
            self.model = None
        elif self.model_type == 'svm':
            self.model = SVC(kernel='rbf', C=1.0, gamma='scale', probability=True, class_weight='balanced')
        elif self.model_type == 'logistic':
            self.model = LogisticRegression(class_weight='balanced', random_state=42)
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")
    
    def _build_neural_network(self, input_shape: int):
        """Build neural network model for classification."""
        if not TENSORFLOW_AVAILABLE:
            raise ImportError("TensorFlow is required for neural network models")
        
        model = keras.Sequential([
            layers.Dense(256, activation='relu', input_shape=(input_shape,)),
            layers.Dropout(0.3),
            layers.Dense(128, activation='relu'),
            layers.Dropout(0.3),
            layers.Dense(64, activation='relu'),
            layers.Dropout(0.2),
            layers.Dense(32, activation='relu'),
            layers.Dense(1, activation='sigmoid')  # Binary classification
        ])
        
        model.compile(
            optimizer='adam',
            loss='binary_crossentropy',
            metrics=['accuracy', 'precision', 'recall']
        )
        
        return model
    
    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare features for training/prediction from pole health data.
        
        Args:
            df: DataFrame with pole health assessment data
            
        Returns:
            DataFrame with engineered features
        """
        features = df.copy()
        
        # Pole characteristics
        if 'pole_type' in features.columns:
            # One-hot encode pole type
            pole_type_dummies = pd.get_dummies(features['pole_type'], prefix='pole_type')
            features = pd.concat([features, pole_type_dummies], axis=1)
        
        # Age-related features
        if 'age_years' in features.columns:
            features['age_category'] = pd.cut(features['age_years'], 
                                            bins=[0, 10, 20, 30, 50, 100], 
                                            labels=['new', 'young', 'mature', 'old', 'ancient'])
            age_dummies = pd.get_dummies(features['age_category'], prefix='age')
            features = pd.concat([features, age_dummies], axis=1)
        
        # Health score features
        if 'overall_health_score' in features.columns:
            features['health_critical'] = (features['overall_health_score'] < 30).astype(int)
            features['health_poor'] = (features['overall_health_score'] < 50).astype(int)
            features['health_fair'] = (features['overall_health_score'] < 70).astype(int)
        
        # Risk factor combinations
        risk_columns = ['moisture_risk', 'erosion_risk', 'chemical_corrosion_risk', 'bearing_capacity_risk']
        available_risk_cols = [col for col in risk_columns if col in features.columns]
        
        if available_risk_cols:
            features['total_risk_score'] = features[available_risk_cols].sum(axis=1)
            features['max_risk_factor'] = features[available_risk_cols].max(axis=1)
            features['risk_factor_count'] = (features[available_risk_cols] > 0.5).sum(axis=1)
        
        # Environmental factors
        if 'voltage_class' in features.columns:
            voltage_dummies = pd.get_dummies(features['voltage_class'], prefix='voltage')
            features = pd.concat([features, voltage_dummies], axis=1)
        
        # Maintenance history indicators
        if 'maintenance_priority' in features.columns:
            priority_dummies = pd.get_dummies(features['maintenance_priority'], prefix='priority')
            features = pd.concat([features, priority_dummies], axis=1)
        
        # Interaction features
        if 'age_years' in features.columns and 'overall_health_score' in features.columns:
            features['age_health_interaction'] = features['age_years'] * (100 - features['overall_health_score'])
        
        return features
    
    def create_failure_labels(self, df: pd.DataFrame, failure_threshold: float = 30) -> pd.Series:
        """
        Create binary failure labels based on health scores and risk factors.
        
        Args:
            df: DataFrame with pole health data
            failure_threshold: Health score threshold below which pole is considered at risk
            
        Returns:
            Binary labels (1 = high failure risk, 0 = low failure risk)
        """
        # Multiple criteria for failure risk
        failure_conditions = []
        
        if 'overall_health_score' in df.columns:
            failure_conditions.append(df['overall_health_score'] < failure_threshold)
        
        if 'requires_immediate_attention' in df.columns:
            failure_conditions.append(df['requires_immediate_attention'])
        
        if 'maintenance_priority' in df.columns:
            failure_conditions.append(df['maintenance_priority'].isin(['critical', 'high']))
        
        # Combine conditions with OR logic
        if failure_conditions:
            failure_labels = pd.Series(False, index=df.index)
            for condition in failure_conditions:
                failure_labels = failure_labels | condition
            return failure_labels.astype(int)
        else:
            # Default: use health score threshold
            return (df.get('overall_health_score', 100) < failure_threshold).astype(int)
    
    def fit(self, X: Union[pd.DataFrame, np.ndarray], y: Union[pd.Series, np.ndarray], 
            validation_split: float = 0.2) -> Dict:
        """
        Train the failure prediction model.
        
        Args:
            X: Features
            y: Target labels (failure risk: 0/1)
            validation_split: Fraction of data for validation
            
        Returns:
            Dictionary with training metrics
        """
        if isinstance(X, pd.DataFrame):
            # Select numeric columns only
            numeric_columns = X.select_dtypes(include=[np.number]).columns
            X = X[numeric_columns]
            self.feature_names = list(X.columns)
            X = X.values
        
        if isinstance(y, pd.Series):
            y = y.values
        
        # Split data for validation
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=validation_split, random_state=42, stratify=y
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_val_scaled = self.scaler.transform(X_val)
        
        # Train model
        if self.model_type == 'neural_network':
            self.model = self._build_neural_network(X_train_scaled.shape[1])
            
            history = self.model.fit(
                X_train_scaled, y_train,
                validation_data=(X_val_scaled, y_val),
                epochs=100,
                batch_size=32,
                verbose=0,
                callbacks=[
                    keras.callbacks.EarlyStopping(patience=15, restore_best_weights=True)
                ]
            )
            self.training_history = history.history
            
            # Get predictions for validation metrics
            y_pred_proba = self.model.predict(X_val_scaled, verbose=0)
            y_pred = (y_pred_proba > 0.5).astype(int).flatten()
            
        else:
            self.model.fit(X_train_scaled, y_train)
            y_pred = self.model.predict(X_val_scaled)
            y_pred_proba = self.model.predict_proba(X_val_scaled)[:, 1]
        
        # Calculate validation metrics
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
        
        metrics = {
            'val_accuracy': accuracy_score(y_val, y_pred),
            'val_precision': precision_score(y_val, y_pred, zero_division=0),
            'val_recall': recall_score(y_val, y_pred, zero_division=0),
            'val_f1': f1_score(y_val, y_pred, zero_division=0),
            'val_auc': roc_auc_score(y_val, y_pred_proba) if len(np.unique(y_val)) > 1 else 0.5,
            'n_features': X_train_scaled.shape[1],
            'n_samples': len(X_train),
            'class_distribution': np.bincount(y_train)
        }
        
        # Cross-validation for traditional ML models
        if self.model_type != 'neural_network':
            cv_scores = cross_val_score(self.model, X_train_scaled, y_train, 
                                      cv=5, scoring='f1')
            metrics['cv_f1_mean'] = cv_scores.mean()
            metrics['cv_f1_std'] = cv_scores.std()
        
        self.is_fitted = True
        logger.info(f"Failure prediction model trained. Validation F1: {metrics['val_f1']:.4f}")
        
        return metrics
    
    def predict_failure_probability(self, X: Union[pd.DataFrame, np.ndarray]) -> np.ndarray:
        """
        Predict failure probability for poles.
        
        Args:
            X: Features
            
        Returns:
            Failure probabilities (0-1)
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before making predictions")
        
        if isinstance(X, pd.DataFrame):
            # Select same numeric columns used in training
            if self.feature_names:
                available_features = [f for f in self.feature_names if f in X.columns]
                missing_features = [f for f in self.feature_names if f not in X.columns]
                if missing_features:
                    logger.warning(f"Missing features in prediction data: {missing_features}")
                X = X[available_features]
            else:
                X = X.select_dtypes(include=[np.number])
            X = X.values
        
        X_scaled = self.scaler.transform(X)
        
        if self.model_type == 'neural_network':
            probabilities = self.model.predict(X_scaled, verbose=0)
            return probabilities.flatten()
        else:
            return self.model.predict_proba(X_scaled)[:, 1]
    
    def get_feature_importance(self) -> Optional[Dict[str, float]]:
        """Get feature importance (for tree-based models)."""
        if not self.is_fitted:
            raise ValueError("Model must be fitted first")
        
        if hasattr(self.model, 'feature_importances_'):
            if self.feature_names:
                return dict(zip(self.feature_names, self.model.feature_importances_))
            else:
                return {f'feature_{i}': imp for i, imp in enumerate(self.model.feature_importances_)}
        else:
            logger.warning(f"Feature importance not available for {self.model_type}")
            return None


class PoleHealthScorePredictor:
    """
    Regression model for predicting continuous pole health scores.
    """
    
    def __init__(self, model_type: str = 'random_forest'):
        """Initialize the health score predictor."""
        self.model_type = model_type
        self.model = None
        self.scaler = StandardScaler()
        self.is_fitted = False
        self.feature_names = None
        
        if model_type == 'random_forest':
            self.model = RandomForestRegressor(
                n_estimators=150,
                max_depth=12,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42
            )
        elif model_type == 'neural_network':
            if not TENSORFLOW_AVAILABLE:
                logger.warning("TensorFlow not available, falling back to Random Forest")
                self.model_type = 'random_forest'
                self.model = RandomForestRegressor(n_estimators=150, random_state=42)
        elif model_type == 'svm':
            self.model = SVR(kernel='rbf', C=1.0, gamma='scale')
        elif model_type == 'ridge':
            self.model = Ridge(alpha=1.0)
        else:
            raise ValueError(f"Unknown model type: {model_type}")
    
    def fit(self, X: Union[pd.DataFrame, np.ndarray], y: Union[pd.Series, np.ndarray]) -> Dict:
        """Train the health score prediction model."""
        if isinstance(X, pd.DataFrame):
            numeric_columns = X.select_dtypes(include=[np.number]).columns
            X = X[numeric_columns]
            self.feature_names = list(X.columns)
            X = X.values
        
        X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)
        
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_val_scaled = self.scaler.transform(X_val)
        
        self.model.fit(X_train_scaled, y_train)
        
        y_pred = self.model.predict(X_val_scaled)
        
        metrics = {
            'val_rmse': np.sqrt(mean_squared_error(y_val, y_pred)),
            'val_mae': mean_absolute_error(y_val, y_pred),
            'val_r2': r2_score(y_val, y_pred)
        }
        
        self.is_fitted = True
        return metrics
    
    def predict(self, X: Union[pd.DataFrame, np.ndarray]) -> np.ndarray:
        """Predict health scores."""
        if not self.is_fitted:
            raise ValueError("Model must be fitted first")
        
        if isinstance(X, pd.DataFrame):
            if self.feature_names:
                available_features = [f for f in self.feature_names if f in X.columns]
                X = X[available_features]
            else:
                X = X.select_dtypes(include=[np.number])
            X = X.values
        
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)


class AnomalyDetector:
    """
    Detect anomalies in soil moisture measurements.
    """
    
    def __init__(self, method: str = 'isolation_forest'):
        """
        Initialize the anomaly detector.
        
        Args:
            method: Detection method ('isolation_forest', 'statistical', 'seasonal')
        """
        self.method = method
        self.model = None
        self.scaler = StandardScaler()
        self.threshold = None
        self.is_fitted = False
        
        if method == 'isolation_forest':
            self.model = IsolationForest(contamination=0.1, random_state=42)
    
    def fit(self, X: Union[pd.DataFrame, np.ndarray]):
        """
        Fit the anomaly detector.
        
        Args:
            X: Features for anomaly detection
        """
        if isinstance(X, pd.DataFrame):
            X = X.values
        
        X_scaled = self.scaler.fit_transform(X)
        
        if self.method == 'isolation_forest':
            self.model.fit(X_scaled)
        elif self.method == 'statistical':
            # Use statistical thresholds (e.g., z-score)
            self.threshold = {
                'mean': np.mean(X_scaled, axis=0),
                'std': np.std(X_scaled, axis=0)
            }
        
        self.is_fitted = True
    
    def detect_anomalies(self, X: Union[pd.DataFrame, np.ndarray]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Detect anomalies in the data.
        
        Args:
            X: Data to check for anomalies
            
        Returns:
            Tuple of (anomaly_labels, anomaly_scores)
        """
        if not self.is_fitted:
            raise ValueError("Detector must be fitted first")
        
        if isinstance(X, pd.DataFrame):
            X = X.values
        
        X_scaled = self.scaler.transform(X)
        
        if self.method == 'isolation_forest':
            anomaly_labels = self.model.predict(X_scaled)  # -1 for anomaly, 1 for normal
            anomaly_scores = self.model.decision_function(X_scaled)
            
            # Convert to boolean (True for anomaly)
            anomaly_labels = (anomaly_labels == -1)
            
        elif self.method == 'statistical':
            # Z-score based detection
            z_scores = np.abs((X_scaled - self.threshold['mean']) / self.threshold['std'])
            anomaly_scores = np.max(z_scores, axis=1)  # Max z-score across features
            anomaly_labels = anomaly_scores > 3  # 3-sigma rule
        
        return anomaly_labels, anomaly_scores


class TimeSeriesForecaster:
    """
    Time series forecasting for soil moisture data.
    """
    
    def __init__(self, model_type: str = 'lstm', forecast_horizon: int = 7):
        """
        Initialize the forecaster.
        
        Args:
            model_type: Type of forecasting model ('lstm', 'arima', 'linear')
            forecast_horizon: Number of days to forecast ahead
        """
        self.model_type = model_type
        self.forecast_horizon = forecast_horizon
        self.model = None
        self.scaler = MinMaxScaler()
        self.is_fitted = False
        self.sequence_length = 30  # Use 30 days of history
    
    def create_sequences(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Create sequences for time series modeling."""
        X, y = [], []
        
        for i in range(len(data) - self.sequence_length):
            X.append(data[i:(i + self.sequence_length)])
            y.append(data[i + self.sequence_length])
        
        return np.array(X), np.array(y)
    
    def fit(self, time_series: Union[pd.Series, np.ndarray]) -> Dict:
        """
        Fit the forecasting model.
        
        Args:
            time_series: Time series data
            
        Returns:
            Training metrics
        """
        if isinstance(time_series, pd.Series):
            time_series = time_series.values
        
        # Scale the data
        scaled_data = self.scaler.fit_transform(time_series.reshape(-1, 1)).flatten()
        
        if self.model_type == 'lstm':
            if not TENSORFLOW_AVAILABLE:
                logger.warning("TensorFlow not available, falling back to linear model")
                self.model_type = 'linear'
                return self.fit(time_series)
            
            # Create sequences
            X, y = self.create_sequences(scaled_data)
            
            if len(X) < 10:
                raise ValueError("Not enough data for LSTM training")
            
            # Split data
            split_idx = int(len(X) * 0.8)
            X_train, X_val = X[:split_idx], X[split_idx:]
            y_train, y_val = y[:split_idx], y[split_idx:]
            
            # Build LSTM model
            self.model = keras.Sequential([
                layers.LSTM(50, return_sequences=True, input_shape=(self.sequence_length, 1)),
                layers.Dropout(0.2),
                layers.LSTM(50),
                layers.Dropout(0.2),
                layers.Dense(25),
                layers.Dense(1)
            ])
            
            self.model.compile(optimizer='adam', loss='mse', metrics=['mae'])
            
            # Reshape for LSTM
            X_train = X_train.reshape((X_train.shape[0], X_train.shape[1], 1))
            X_val = X_val.reshape((X_val.shape[0], X_val.shape[1], 1))
            
            # Train
            history = self.model.fit(
                X_train, y_train,
                validation_data=(X_val, y_val),
                epochs=50,
                batch_size=32,
                verbose=0,
                callbacks=[keras.callbacks.EarlyStopping(patience=5)]
            )
            
            # Calculate metrics
            y_pred = self.model.predict(X_val, verbose=0)
            val_rmse = np.sqrt(mean_squared_error(y_val, y_pred))
            
            metrics = {
                'val_rmse': val_rmse,
                'val_mae': mean_absolute_error(y_val, y_pred),
                'n_samples': len(X_train)
            }
            
        elif self.model_type == 'linear':
            # Simple linear trend model
            X = np.arange(len(scaled_data)).reshape(-1, 1)
            y = scaled_data
            
            self.model = LinearRegression()
            self.model.fit(X, y)
            
            y_pred = self.model.predict(X)
            metrics = {
                'rmse': np.sqrt(mean_squared_error(y, y_pred)),
                'mae': mean_absolute_error(y, y_pred),
                'r2': r2_score(y, y_pred)
            }
        
        self.is_fitted = True
        return metrics
    
    def forecast(self, time_series: Union[pd.Series, np.ndarray], 
                steps: Optional[int] = None) -> np.ndarray:
        """
        Generate forecasts.
        
        Args:
            time_series: Historical time series data
            steps: Number of steps to forecast (default: forecast_horizon)
            
        Returns:
            Forecasted values
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted first")
        
        if steps is None:
            steps = self.forecast_horizon
        
        if isinstance(time_series, pd.Series):
            time_series = time_series.values
        
        scaled_data = self.scaler.transform(time_series.reshape(-1, 1)).flatten()
        
        if self.model_type == 'lstm':
            # Use last sequence_length points as input
            last_sequence = scaled_data[-self.sequence_length:].reshape(1, self.sequence_length, 1)
            
            forecasts = []
            current_seq = last_sequence.copy()
            
            for _ in range(steps):
                next_pred = self.model.predict(current_seq, verbose=0)[0, 0]
                forecasts.append(next_pred)
                
                # Update sequence for next prediction
                current_seq = np.roll(current_seq, -1, axis=1)
                current_seq[0, -1, 0] = next_pred
            
            forecasts = np.array(forecasts)
            
        elif self.model_type == 'linear':
            # Linear extrapolation
            X_future = np.arange(len(scaled_data), len(scaled_data) + steps).reshape(-1, 1)
            forecasts = self.model.predict(X_future)
        
        # Inverse transform
        forecasts_rescaled = self.scaler.inverse_transform(forecasts.reshape(-1, 1)).flatten()
        
        return forecasts_rescaled
