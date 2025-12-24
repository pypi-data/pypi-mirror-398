"""
Command-line interface for machine learning functionality.
"""

import argparse
import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import logging

from soilmoisture.ml.models import SoilMoisturePredictor, AnomalyDetector, TimeSeriesForecaster
from soilmoisture.ml.features import FeatureEngineer, select_features
from soilmoisture.analysis.statistics import calculate_rmse, calculate_correlation, calculate_bias

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_data(filepath: str) -> pd.DataFrame:
    """Load soil moisture data from file using unified DataLoader."""
    # Import here to avoid circular imports
    from ..common import DataLoader
    
    # Determine if this looks like in-situ data or general CSV
    filepath_obj = Path(filepath)
    if filepath_obj.suffix == '.stm' or 'insitu' in filepath_obj.name.lower():
        return DataLoader.load_insitu_data(filepath)
    else:
        return DataLoader.load_csv_data(filepath, data_type='soil')


def train_predictor_command(args):
    """Train a soil moisture prediction model."""
    logger.info(f"Loading data from {args.data_file}")
    df = load_data(args.data_file)
    
    logger.info(f"Data shape: {df.shape}")
    logger.info(f"Columns: {list(df.columns)}")
    
    # Feature engineering
    logger.info("Engineering features...")
    fe = FeatureEngineer()
    features = fe.fit_transform(df)
    
    # Feature selection
    if 'in_situ' not in features.columns:
        raise ValueError("No 'in_situ' column found for training target")
    
    feature_cols = select_features(
        features, 
        target_col='in_situ',
        correlation_threshold=args.correlation_threshold,
        max_features=args.max_features
    )
    
    if len(feature_cols) == 0:
        raise ValueError("No features selected. Try lowering correlation_threshold.")
    
    logger.info(f"Selected {len(feature_cols)} features: {feature_cols}")
    
    # Prepare training data
    X = features[feature_cols].dropna()
    y = features.loc[X.index, 'in_situ']
    
    if len(X) < 10:
        raise ValueError("Not enough training samples after feature engineering")
    
    logger.info(f"Training samples: {len(X)}")
    
    # Train model
    logger.info(f"Training {args.model_type} model...")
    predictor = SoilMoisturePredictor(model_type=args.model_type)
    
    try:
        metrics = predictor.fit(X, y, validation_split=args.validation_split)
        
        logger.info("Training completed!")
        logger.info(f"Validation RMSE: {metrics['val_rmse']:.4f}")
        logger.info(f"Validation MAE: {metrics['val_mae']:.4f}")
        logger.info(f"Validation R²: {metrics['val_r2']:.4f}")
        
        if 'cv_rmse_mean' in metrics:
            logger.info(f"CV RMSE: {metrics['cv_rmse_mean']:.4f} ± {metrics['cv_rmse_std']:.4f}")
        
        # Save model
        model_path = args.output_dir / f"soil_moisture_{args.model_type}_model.joblib"
        predictor.save(str(model_path))
        logger.info(f"Model saved to {model_path}")
        
        # Feature importance
        importance = predictor.get_feature_importance()
        if importance:
            logger.info("\nTop 10 most important features:")
            sorted_importance = sorted(importance.items(), key=lambda x: x[1], reverse=True)
            for feat, imp in sorted_importance[:10]:
                logger.info(f"  {feat}: {imp:.4f}")
            
            # Save feature importance plot
            plt.figure(figsize=(10, 6))
            features_to_plot = dict(sorted_importance[:15])
            sns.barplot(x=list(features_to_plot.values()), y=list(features_to_plot.keys()))
            plt.title(f'Feature Importance - {args.model_type.title()} Model')
            plt.xlabel('Importance')
            plt.tight_layout()
            
            importance_plot = args.output_dir / f"feature_importance_{args.model_type}.png"
            plt.savefig(importance_plot, dpi=300, bbox_inches='tight')
            plt.close()
            logger.info(f"Feature importance plot saved to {importance_plot}")
        
    except Exception as e:
        logger.error(f"Training failed: {str(e)}")
        sys.exit(1)


def predict_command(args):
    """Make predictions using a trained model."""
    logger.info(f"Loading model from {args.model_file}")
    predictor = SoilMoisturePredictor()
    predictor.load(args.model_file)
    
    logger.info(f"Loading data from {args.data_file}")
    df = load_data(args.data_file)
    
    # Feature engineering (same as training)
    fe = FeatureEngineer()
    features = fe.fit_transform(df)
    
    # Use same features as training
    if predictor.feature_names:
        feature_cols = predictor.feature_names
    else:
        feature_cols = [col for col in features.columns if col not in ['in_situ', 'date']]
    
    # Make predictions
    X = features[feature_cols].dropna()
    predictions = predictor.predict(X)
    
    # Save predictions
    results = features.loc[X.index, ['date']].copy()
    results['predicted_soil_moisture'] = predictions
    
    if 'in_situ' in features.columns:
        results['actual_soil_moisture'] = features.loc[X.index, 'in_situ']
        
        # Calculate metrics
        actual = results['actual_soil_moisture'].dropna()
        pred = results.loc[actual.index, 'predicted_soil_moisture']
        
        rmse = calculate_rmse(actual, pred)
        corr = calculate_correlation(actual, pred)  
        bias = calculate_bias(actual, pred)
        
        logger.info(f"Prediction metrics:")
        logger.info(f"  RMSE: {rmse:.4f}")
        logger.info(f"  Correlation: {corr:.4f}")
        logger.info(f"  Bias: {bias:.4f}")
    
    # Save results
    output_file = args.output_dir / "predictions.csv"
    results.to_csv(output_file, index=False)
    logger.info(f"Predictions saved to {output_file}")


def detect_anomalies_command(args):
    """Detect anomalies in soil moisture data."""
    logger.info(f"Loading data from {args.data_file}")
    df = load_data(args.data_file)
    
    # Use satellite data for anomaly detection
    if 'satellite' not in df.columns:
        raise ValueError("No 'satellite' column found for anomaly detection")
    
    # Prepare features
    X = df[['satellite']].dropna()
    
    if len(X) < 10:
        raise ValueError("Not enough data for anomaly detection")
    
    # Train detector
    logger.info(f"Training {args.method} anomaly detector...")
    detector = AnomalyDetector(method=args.method)
    detector.fit(X)
    
    # Detect anomalies
    anomaly_labels, anomaly_scores = detector.detect_anomalies(X)
    
    # Prepare results
    results = df.loc[X.index].copy()
    results['is_anomaly'] = anomaly_labels
    results['anomaly_score'] = anomaly_scores
    
    n_anomalies = anomaly_labels.sum()
    anomaly_rate = n_anomalies / len(anomaly_labels) * 100
    
    logger.info(f"Detected {n_anomalies} anomalies ({anomaly_rate:.1f}% of data)")
    
    # Save results
    output_file = args.output_dir / "anomalies.csv"
    results.to_csv(output_file, index=False)
    logger.info(f"Anomaly detection results saved to {output_file}")
    
    # Create visualization
    plt.figure(figsize=(14, 8))
    
    # Time series plot
    plt.subplot(2, 1, 1)
    plt.plot(results['date'], results['satellite'], 'b-', alpha=0.7, label='Satellite Data')
    anomalies = results[results['is_anomaly']]
    if len(anomalies) > 0:
        plt.scatter(anomalies['date'], anomalies['satellite'], 
                   c='red', s=50, label='Anomalies', zorder=5)
    plt.title('Soil Moisture Time Series with Anomalies')
    plt.ylabel('Soil Moisture (m³/m³)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Score distribution
    plt.subplot(2, 1, 2)
    plt.hist(anomaly_scores, bins=30, alpha=0.7, color='skyblue', edgecolor='black')
    plt.axvline(anomaly_scores[anomaly_labels].min(), color='red', linestyle='--', 
                label='Anomaly Threshold')
    plt.title('Anomaly Score Distribution')
    plt.xlabel('Anomaly Score')
    plt.ylabel('Frequency')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plot_file = args.output_dir / f"anomaly_detection_{args.method}.png"
    plt.savefig(plot_file, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Anomaly detection plot saved to {plot_file}")


def forecast_command(args):
    """Generate soil moisture forecasts."""
    logger.info(f"Loading data from {args.data_file}")
    df = load_data(args.data_file)
    
    # Use in-situ data for forecasting if available, otherwise satellite
    if 'in_situ' in df.columns and df['in_situ'].notna().sum() > args.min_history:
        time_series = df['in_situ'].dropna()
        series_name = 'In-situ'
    elif 'satellite' in df.columns:
        time_series = df['satellite'].dropna()
        series_name = 'Satellite'
    else:
        raise ValueError("No suitable time series data found")
    
    if len(time_series) < args.min_history:
        raise ValueError(f"Not enough historical data. Need at least {args.min_history} points.")
    
    logger.info(f"Using {series_name} data with {len(time_series)} points")
    
    # Train forecaster
    logger.info(f"Training {args.model_type} forecasting model...")
    forecaster = TimeSeriesForecaster(
        model_type=args.model_type, 
        forecast_horizon=args.forecast_days
    )
    
    try:
        metrics = forecaster.fit(time_series)
        logger.info(f"Training completed. Metrics: {metrics}")
        
        # Generate forecasts
        forecasts = forecaster.forecast(time_series, steps=args.forecast_days)
        
        # Create forecast dates
        if 'date' in df.columns:
            last_date = df['date'].max()
            forecast_dates = pd.date_range(
                start=last_date + pd.Timedelta(days=1),
                periods=args.forecast_days,
                freq='D'
            )
        else:
            forecast_dates = range(1, args.forecast_days + 1)
        
        # Save forecasts
        forecast_df = pd.DataFrame({
            'date': forecast_dates,
            'forecasted_soil_moisture': forecasts
        })
        
        output_file = args.output_dir / "forecasts.csv"
        forecast_df.to_csv(output_file, index=False)
        logger.info(f"Forecasts saved to {output_file}")
        
        # Create visualization
        plt.figure(figsize=(12, 6))
        
        # Plot historical data (last 60 days)
        recent_data = time_series.tail(60)
        if 'date' in df.columns:
            recent_dates = df.loc[recent_data.index, 'date']
            plt.plot(recent_dates, recent_data.values, 'b-', label=f'{series_name} (Historical)')
            plt.plot(forecast_dates, forecasts, 'r--', marker='o', 
                    label=f'Forecast ({args.forecast_days} days)', linewidth=2)
        else:
            plt.plot(range(len(recent_data)), recent_data.values, 'b-', 
                    label=f'{series_name} (Historical)')
            plt.plot(range(len(recent_data), len(recent_data) + args.forecast_days), 
                    forecasts, 'r--', marker='o', 
                    label=f'Forecast ({args.forecast_days} days)', linewidth=2)
        
        plt.title(f'Soil Moisture Forecast - {args.model_type.upper()} Model')
        plt.ylabel('Soil Moisture (m³/m³)')
        plt.xlabel('Date')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        plot_file = args.output_dir / f"forecast_{args.model_type}.png"
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        plt.close()
        logger.info(f"Forecast plot saved to {plot_file}")
        
    except Exception as e:
        logger.error(f"Forecasting failed: {str(e)}")
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description='Soil Moisture Machine Learning CLI')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Common arguments
    def add_common_args(subparser):
        subparser.add_argument('--data-file', '-d', required=True, 
                             help='Path to input data file')
        subparser.add_argument('--output-dir', '-o', type=Path, 
                             default='./ml_output',
                             help='Output directory for results')
    
    # Train predictor
    train_parser = subparsers.add_parser('train', help='Train a prediction model')
    add_common_args(train_parser)
    train_parser.add_argument('--model-type', '-m', 
                            choices=['random_forest', 'neural_network', 'svm', 'linear'],
                            default='random_forest',
                            help='Type of model to train')
    train_parser.add_argument('--max-features', type=int, default=25,
                            help='Maximum number of features to use')
    train_parser.add_argument('--correlation-threshold', type=float, default=0.05,
                            help='Minimum correlation with target for feature selection')
    train_parser.add_argument('--validation-split', type=float, default=0.2,
                            help='Fraction of data for validation')
    
    # Predict
    predict_parser = subparsers.add_parser('predict', help='Make predictions')
    add_common_args(predict_parser)
    predict_parser.add_argument('--model-file', '-mf', required=True,
                              help='Path to trained model file')
    
    # Anomaly detection
    anomaly_parser = subparsers.add_parser('anomalies', help='Detect anomalies')
    add_common_args(anomaly_parser)
    anomaly_parser.add_argument('--method', choices=['isolation_forest', 'statistical'],
                              default='isolation_forest',
                              help='Anomaly detection method')
    
    # Forecasting
    forecast_parser = subparsers.add_parser('forecast', help='Generate forecasts')
    add_common_args(forecast_parser)
    forecast_parser.add_argument('--model-type', choices=['lstm', 'linear'],
                               default='linear',
                               help='Forecasting model type')
    forecast_parser.add_argument('--forecast-days', type=int, default=7,
                               help='Number of days to forecast')
    forecast_parser.add_argument('--min-history', type=int, default=30,
                               help='Minimum historical data points required')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    # Route to appropriate command
    try:
        if args.command == 'train':
            train_predictor_command(args)
        elif args.command == 'predict':
            predict_command(args)
        elif args.command == 'anomalies':
            detect_anomalies_command(args)
        elif args.command == 'forecast':
            forecast_command(args)
        else:
            parser.print_help()
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
