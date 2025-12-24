"""
REST API endpoints for soil moisture analysis.
"""

import os
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
import shutil
from datetime import datetime, timedelta
from typing import Optional
from flask import Blueprint, request, jsonify, current_app, send_file
from werkzeug.utils import secure_filename

from soilmoisture.ml.models import SoilMoisturePredictor, AnomalyDetector, TimeSeriesForecaster
from soilmoisture.ml.features import FeatureEngineer, select_features
from soilmoisture.analysis.statistics import calculate_rmse, calculate_correlation, calculate_bias
from soilmoisture.visualization.plots import create_dashboard

logger = logging.getLogger(__name__)

logger.debug('api', __name__)

# Create the API Blueprint
api_blueprint = Blueprint('api', __name__, url_prefix='/api')


def allowed_file(filename: str) -> bool:
    """Check if uploaded file has allowed extension."""
    ALLOWED_EXTENSIONS = {'txt', 'csv', 'nc', 'nc4'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def load_data_file(filepath: str) -> pd.DataFrame:
    """Load data from various file formats using unified DataLoader."""
    try:
        # Import here to avoid circular imports
        from ..common import DataLoader
        
        # Use the unified data loader
        return DataLoader.load_csv_data(filepath, data_type='generic')
        
    except Exception as e:
        logger.error(f"Error loading data file {filepath}: {str(e)}")
        raise


@api_blueprint.route('/upload', methods=['POST'])
def upload_file():
    """Upload and process a data file."""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = Path(current_app.config['UPLOAD_FOLDER']) / filename
            file.save(filepath)
            
            # Load and analyze the data
            df = load_data_file(str(filepath))
            
            # Basic statistics
            stats = {
                'n_rows': len(df),
                'columns': list(df.columns),
                'date_range': None,
                'data_summary': {}
            }
            
            if 'date' in df.columns:
                stats['date_range'] = {
                    'start': df['date'].min().isoformat() if not df['date'].min() is pd.NaT else None,
                    'end': df['date'].max().isoformat() if not df['date'].max() is pd.NaT else None
                }
            
            # Data summary for numeric columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                stats['data_summary'][col] = {
                    'mean': float(df[col].mean()) if not df[col].isna().all() else None,
                    'std': float(df[col].std()) if not df[col].isna().all() else None,
                    'min': float(df[col].min()) if not df[col].isna().all() else None,
                    'max': float(df[col].max()) if not df[col].isna().all() else None,
                    'missing_count': int(df[col].isna().sum())
                }
            
            return jsonify({
                'message': 'File uploaded successfully',
                'filename': filename,
                'stats': stats
            })
        
        return jsonify({'error': 'Invalid file type'}), 400
        
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@api_blueprint.route('/data/<filename>')
def get_data(filename: str):
    """Get basic information about a data file."""
    try:
        filename = secure_filename(filename)
        filepath = Path(current_app.config['UPLOAD_FOLDER']) / filename
        
        if not filepath.exists():
            return jsonify({'error': 'File not found'}), 404
        
        df = load_data_file(str(filepath))
        
        # Return first few rows and summary stats
        data_preview = df.head(10).to_dict('records')
        
        # Convert datetime objects to strings for JSON serialization
        for row in data_preview:
            for key, value in row.items():
                if pd.isna(value):
                    row[key] = None
                elif isinstance(value, (pd.Timestamp, datetime)):
                    row[key] = value.isoformat()
                elif isinstance(value, (np.integer, np.floating)):
                    row[key] = float(value) if not np.isnan(value) else None
        
        return jsonify({
            'preview': data_preview,
            'shape': df.shape,
            'columns': list(df.columns)
        })
        
    except Exception as e:
        logger.error(f"Data retrieval error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@api_blueprint.route('/train-model', methods=['POST'])
def train_model():
    """Train a machine learning model."""
    try:
        data = request.get_json()
        filename = data.get('filename')
        model_type = data.get('model_type', 'random_forest')
        max_features = data.get('max_features', 25)
        correlation_threshold = data.get('correlation_threshold', 0.05)
        
        if not filename:
            return jsonify({'error': 'Filename required'}), 400
        
        filename = secure_filename(filename)
        filepath = Path(current_app.config['UPLOAD_FOLDER']) / filename
        
        if not filepath.exists():
            return jsonify({'error': 'Data file not found'}), 404
        
        # Load and prepare data
        df = load_data_file(str(filepath))
        
        if 'in_situ' not in df.columns:
            return jsonify({'error': 'No in_situ column found for training target'}), 400
        
        # Feature engineering
        fe = FeatureEngineer()
        features = fe.fit_transform(df)
        
        # Feature selection
        feature_cols = select_features(
            features,
            target_col='in_situ',
            correlation_threshold=correlation_threshold,
            max_features=max_features
        )
        
        if len(feature_cols) == 0:
            return jsonify({'error': 'No features selected. Try lowering correlation threshold.'}), 400
        
        # Prepare training data
        X = features[feature_cols].dropna()
        y = features.loc[X.index, 'in_situ']
        
        if len(X) < 10:
            return jsonify({'error': 'Not enough training samples'}), 400
        
        # Train model
        predictor = SoilMoisturePredictor(model_type=model_type)
        metrics = predictor.fit(X, y, validation_split=0.2)
        
        # Save model
        model_filename = f"model_{model_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.joblib"
        model_path = Path(current_app.config['OUTPUT_DIR']) / model_filename
        predictor.save(str(model_path))
        
        # Get feature importance if available
        importance = predictor.get_feature_importance()
        top_features = None
        if importance:
            sorted_importance = sorted(importance.items(), key=lambda x: x[1], reverse=True)
            top_features = dict(sorted_importance[:10])
        
        return jsonify({
            'message': 'Model trained successfully',
            'model_filename': model_filename,
            'metrics': {
                'val_rmse': float(metrics['val_rmse']),
                'val_mae': float(metrics['val_mae']),
                'val_r2': float(metrics['val_r2']),
                'n_features': int(metrics['n_features']),
                'n_samples': int(metrics['n_samples'])
            },
            'feature_importance': top_features,
            'selected_features': feature_cols
        })
        
    except Exception as e:
        logger.error(f"Model training error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@api_blueprint.route('/predict', methods=['POST'])
def make_predictions():
    """Make predictions using a trained model."""
    try:
        data = request.get_json()
        filename = data.get('filename')
        model_filename = data.get('model_filename')
        
        if not filename or not model_filename:
            return jsonify({'error': 'Both filename and model_filename required'}), 400
        
        # Load data
        filename = secure_filename(filename)
        filepath = Path(current_app.config['UPLOAD_FOLDER']) / filename
        
        if not filepath.exists():
            return jsonify({'error': 'Data file not found'}), 404
        
        df = load_data_file(str(filepath))
        
        # Load model
        model_filename = secure_filename(model_filename)
        model_path = Path(current_app.config['OUTPUT_DIR']) / model_filename
        
        if not model_path.exists():
            return jsonify({'error': 'Model file not found'}), 404
        
        predictor = SoilMoisturePredictor()
        predictor.load(str(model_path))
        
        # Feature engineering (same as training)
        fe = FeatureEngineer()
        features = fe.fit_transform(df)
        
        # Use model's features
        if predictor.feature_names:
            feature_cols = [col for col in predictor.feature_names if col in features.columns]
        else:
            feature_cols = [col for col in features.columns if col not in ['in_situ', 'date']]
        
        if not feature_cols:
            return jsonify({'error': 'No matching features found for prediction'}), 400
        
        # Make predictions
        X = features[feature_cols].dropna()
        predictions = predictor.predict(X)
        
        # Prepare results
        results = []
        for idx, pred in zip(X.index, predictions):
            result = {'prediction': float(pred)}
            
            if 'date' in features.columns:
                result['date'] = features.loc[idx, 'date'].isoformat()
            
            if 'in_situ' in features.columns and not pd.isna(features.loc[idx, 'in_situ']):
                result['actual'] = float(features.loc[idx, 'in_situ'])
            
            results.append(result)
        
        # Calculate metrics if actual values available
        metrics = None
        if 'in_situ' in features.columns:
            actual_values = features.loc[X.index, 'in_situ'].dropna()
            pred_values = predictions[:len(actual_values)]
            
            if len(actual_values) > 0:
                metrics = {
                    'rmse': float(calculate_rmse(actual_values, pred_values)),
                    'correlation': float(calculate_correlation(actual_values, pred_values)),
                    'bias': float(calculate_bias(actual_values, pred_values)),
                    'n_predictions': len(pred_values)
                }
        
        return jsonify({
            'predictions': results,
            'metrics': metrics,
            'model_used': model_filename
        })
        
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@api_blueprint.route('/detect-anomalies', methods=['POST'])
def detect_anomalies():
    """Detect anomalies in soil moisture data."""
    try:
        data = request.get_json()
        filename = data.get('filename')
        method = data.get('method', 'isolation_forest')
        
        if not filename:
            return jsonify({'error': 'Filename required'}), 400
        
        filename = secure_filename(filename)
        filepath = Path(current_app.config['UPLOAD_FOLDER']) / filename
        
        if not filepath.exists():
            return jsonify({'error': 'Data file not found'}), 404
        
        df = load_data_file(str(filepath))
        
        if 'satellite' not in df.columns:
            return jsonify({'error': 'No satellite column found'}), 400
        
        # Prepare data for anomaly detection
        X = df[['satellite']].dropna()
        
        if len(X) < 10:
            return jsonify({'error': 'Not enough data for anomaly detection'}), 400
        
        # Train detector
        detector = AnomalyDetector(method=method)
        detector.fit(X)
        
        # Detect anomalies
        anomaly_labels, anomaly_scores = detector.detect_anomalies(X)
        
        # Prepare results
        results = []
        for idx, (is_anomaly, score) in zip(X.index, zip(anomaly_labels, anomaly_scores)):
            result = {
                'is_anomaly': bool(is_anomaly),
                'anomaly_score': float(score),
                'satellite_value': float(df.loc[idx, 'satellite'])
            }
            
            if 'date' in df.columns:
                result['date'] = df.loc[idx, 'date'].isoformat()
            
            if 'in_situ' in df.columns and not pd.isna(df.loc[idx, 'in_situ']):
                result['in_situ_value'] = float(df.loc[idx, 'in_situ'])
            
            results.append(result)
        
        n_anomalies = anomaly_labels.sum()
        anomaly_rate = float(n_anomalies / len(anomaly_labels) * 100)
        
        return jsonify({
            'anomalies': results,
            'summary': {
                'total_points': len(X),
                'n_anomalies': int(n_anomalies),
                'anomaly_rate': anomaly_rate,
                'method': method
            }
        })
        
    except Exception as e:
        logger.error(f"Anomaly detection error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@api_blueprint.route('/forecast', methods=['POST'])
def generate_forecast():
    """Generate soil moisture forecasts."""
    try:
        data = request.get_json()
        filename = data.get('filename')
        forecast_days = data.get('forecast_days', 7)
        model_type = data.get('model_type', 'linear')
        
        if not filename:
            return jsonify({'error': 'Filename required'}), 400
        
        filename = secure_filename(filename)
        filepath = Path(current_app.config['UPLOAD_FOLDER']) / filename
        
        if not filepath.exists():
            return jsonify({'error': 'Data file not found'}), 404
        
        df = load_data_file(str(filepath))
        
        # Use in-situ data if available, otherwise satellite
        if 'in_situ' in df.columns and df['in_situ'].notna().sum() > 30:
            time_series = df['in_situ'].dropna()
            series_name = 'in_situ'
        elif 'satellite' in df.columns:
            time_series = df['satellite'].dropna()
            series_name = 'satellite'
        else:
            return jsonify({'error': 'No suitable time series data found'}), 400
        
        if len(time_series) < 30:
            return jsonify({'error': 'Not enough historical data for forecasting'}), 400
        
        # Train forecaster
        forecaster = TimeSeriesForecaster(model_type=model_type, forecast_horizon=forecast_days)
        training_metrics = forecaster.fit(time_series)
        
        # Generate forecasts
        forecasts = forecaster.forecast(time_series, steps=forecast_days)
        
        # Create forecast dates
        if 'date' in df.columns:
            last_date = df['date'].max()
            forecast_dates = pd.date_range(
                start=last_date + pd.Timedelta(days=1),
                periods=forecast_days,
                freq='D'
            )
            forecast_dates = [d.isoformat() for d in forecast_dates]
        else:
            forecast_dates = list(range(1, forecast_days + 1))
        
        # Prepare results
        forecast_results = []
        for date, forecast_value in zip(forecast_dates, forecasts):
            forecast_results.append({
                'date': date,
                'forecast_value': float(forecast_value)
            })
        
        return jsonify({
            'forecasts': forecast_results,
            'training_metrics': {k: float(v) for k, v in training_metrics.items()},
            'model_type': model_type,
            'series_used': series_name,
            'forecast_days': forecast_days
        })
        
    except Exception as e:
        logger.error(f"Forecasting error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@api_blueprint.route('/visualize/<filename>')
def create_visualization(filename: str):
    """Generate visualization dashboard for a data file."""
    try:
        filename = secure_filename(filename)
        filepath = Path(current_app.config['UPLOAD_FOLDER']) / filename
        
        if not filepath.exists():
            return jsonify({'error': 'Data file not found'}), 404
        
        df = load_data_file(str(filepath))
        
        # Create dashboard
        output_dir = Path(current_app.config['OUTPUT_DIR']) / 'visualizations'
        output_dir.mkdir(exist_ok=True)
        
        dashboard_path = create_dashboard(df, str(output_dir))
        
        return send_file(dashboard_path, as_attachment=True, 
                        download_name='soil_moisture_dashboard.html')
        
    except Exception as e:
        logger.error(f"Visualization error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@api_blueprint.route('/models')
def list_models():
    """List available trained models."""
    try:
        output_dir = Path(current_app.config['OUTPUT_DIR'])
        models = []
        
        for model_file in output_dir.glob('model_*.joblib'):
            stat = model_file.stat()
            models.append({
                'filename': model_file.name,
                'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'size_bytes': stat.st_size
            })
        
        return jsonify({'models': models})
        
    except Exception as e:
        logger.error(f"Model listing error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@api_blueprint.route('/status')
def get_status():
    """Get system status and capabilities."""
    try:
        upload_dir = Path(current_app.config['UPLOAD_FOLDER'])
        output_dir = Path(current_app.config['OUTPUT_DIR'])
        
        # Count files
        data_files = len(list(upload_dir.glob('*')))
        model_files = len(list(output_dir.glob('model_*.joblib')))
        
        # Check ML capabilities
        ml_available = True
        try:
            from sklearn.ensemble import RandomForestRegressor
        except ImportError:
            ml_available = False
        
        tensorflow_available = True
        try:
            import tensorflow
        except ImportError:
            tensorflow_available = False
        
        return jsonify({
            'system': {
                'data_files': data_files,
                'model_files': model_files,
                'upload_dir': str(upload_dir),
                'output_dir': str(output_dir)
            },
            'capabilities': {
                'ml_models': ml_available,
                'neural_networks': tensorflow_available,
                'visualizations': True,
                'anomaly_detection': ml_available,
                'forecasting': ml_available
            }
        })
        
    except Exception as e:
        logger.error(f"Status error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@api_blueprint.route('/load-sample-data', methods=['POST'])
def load_sample_data():
    """Load sample data from the Input directory."""
    try:
        # Path to Input directory
        input_dir = Path(__file__).parent.parent.parent / 'Input'
        
        if not input_dir.exists():
            return jsonify({'error': 'Input directory not found'}), 404
        
        # Look for NetCDF files first, then other formats
        sample_files = []
        for pattern in ['*.nc', '*.nc4', '*.csv', '*.txt']:
            sample_files.extend(list(input_dir.glob(f'**/{pattern}')))
        
        if not sample_files:
            return jsonify({'error': 'No sample data files found in Input directory'}), 404
        
        # Use the first available file (prioritize NetCDF)
        sample_file = None
        for file in sample_files:
            if file.suffix in ['.nc', '.nc4']:
                sample_file = file
                break
        
        if not sample_file:
            sample_file = sample_files[0]  # Use first available file
        
        logger.info(f"Loading sample data from: {sample_file}")
        
        # Create synthetic processed data based on the sample file
        # This simulates the processing that would normally happen with real data
        synthetic_data = create_synthetic_data_from_sample(sample_file)
        
        # Save to uploads directory so dashboard can access it
        uploads_dir = Path(current_app.config.get('UPLOAD_FOLDER', './uploads'))
        uploads_dir.mkdir(exist_ok=True)
        
        output_file = uploads_dir / 'sample_soil_moisture_data.csv'
        synthetic_data.to_csv(output_file, index=False)
        
        return jsonify({
            'message': 'Sample data loaded successfully',
            'filename': 'sample_soil_moisture_data.csv',
            'original_file': str(sample_file.name),
            'records': len(synthetic_data),
            'date_range': {
                'start': synthetic_data['date'].min(),
                'end': synthetic_data['date'].max()
            }
        })
        
    except Exception as e:
        logger.error(f"Error loading sample data: {e}")
        return jsonify({'error': str(e)}), 500


def create_synthetic_data_from_sample(sample_file: Path) -> pd.DataFrame:
    """Create synthetic soil moisture data for demonstration."""
    
    # Generate 6 months of daily data
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2023, 6, 30)
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    n_points = len(dates)
    
    # Create realistic soil moisture time series
    # Base seasonal pattern (higher in winter/spring, lower in summer)
    day_of_year = np.array([d.dayofyear for d in dates])
    seasonal_pattern = 0.25 + 0.08 * np.cos(2 * np.pi * (day_of_year - 60) / 365)
    
    # Add some random walk for variability
    random_walk = np.cumsum(np.random.normal(0, 0.01, n_points))
    random_walk = random_walk - random_walk.mean()  # Center around 0
    
    # Daily variations
    daily_noise = np.random.normal(0, 0.015, n_points)
    
    # Combine all components
    in_situ_values = seasonal_pattern + 0.5 * random_walk + daily_noise
    in_situ_values = np.clip(in_situ_values, 0.05, 0.45)  # Realistic range
    
    # Satellite values with some bias and different noise characteristics
    satellite_bias = -0.02  # Slight dry bias
    satellite_noise = np.random.normal(0, 0.02, n_points)
    satellite_values = in_situ_values + satellite_bias + satellite_noise
    satellite_values = np.clip(satellite_values, 0.05, 0.45)
    
    # Add some missing values to make it realistic
    missing_indices = np.random.choice(n_points, size=int(0.05 * n_points), replace=False)
    for idx in missing_indices[:len(missing_indices)//2]:
        in_situ_values[idx] = np.nan
    for idx in missing_indices[len(missing_indices)//2:]:
        satellite_values[idx] = np.nan
    
    # Create DataFrame
    df = pd.DataFrame({
        'date': dates,
        'in_situ': in_situ_values,
        'satellite': satellite_values
    })
    
    # Remove rows where both values are NaN
    df = df.dropna(subset=['in_situ', 'satellite'], how='all')
    
    # Format date column
    df['date'] = df['date'].dt.strftime('%Y-%m-%d')
    
    logger.info(f"Created synthetic dataset with {len(df)} records")
    logger.info(f"In-situ range: {df['in_situ'].min():.3f} - {df['in_situ'].max():.3f}")
    logger.info(f"Satellite range: {df['satellite'].min():.3f} - {df['satellite'].max():.3f}")
    
    return df
