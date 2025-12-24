"""
Dashboard views for the web interface.
"""

import logging
from pathlib import Path

from flask import Blueprint, render_template, current_app, jsonify, request
import pandas as pd
import json

logger = logging.getLogger(__name__)

logger.debug('dashboard', __name__)

# Create the Dashboard Blueprint
dashboard_blueprint = Blueprint('dashboard', __name__)


def load_sample_data():
    """Load or create sample data for dashboard demo."""
    try:
        # Try to load existing data first
        upload_dir = Path(current_app.config['UPLOAD_FOLDER'])
        
        for data_file in upload_dir.glob('*.csv'):
            df = pd.read_csv(data_file)
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'], errors='coerce')
            return df
        
        # Create sample data if no files exist
        import numpy as np
        np.random.seed(42)
        
        dates = pd.date_range('2023-01-01', '2023-12-31', freq='D')
        n_days = len(dates)
        
        # Seasonal pattern
        day_of_year = np.arange(1, n_days + 1)
        seasonal = 0.15 + 0.1 * np.cos(2 * np.pi * day_of_year / 365)
        
        # Add noise
        noise = np.random.normal(0, 0.02, n_days)
        
        sample_data = pd.DataFrame({
            'date': dates,
            'in_situ': seasonal + noise,
            'satellite': seasonal + noise * 1.5 + 0.03,
        })
        
        return sample_data
        
    except Exception as e:
        logger.error(f"Error loading sample data: {e}")
        return pd.DataFrame()


@dashboard_blueprint.route('/dashboard')
def dashboard():
    """Main dashboard view."""
    return render_template('dashboard.html')


@dashboard_blueprint.route('/upload')
def upload_page():
    """File upload page."""
    return render_template('upload.html')


@dashboard_blueprint.route('/models')
def models_page():
    """Model management page."""
    return render_template('models.html')


@dashboard_blueprint.route('/analytics')
def analytics_page():
    """Advanced analytics page."""
    return render_template('analytics.html')


@dashboard_blueprint.route('/api-docs')
def api_docs():
    """API documentation page."""
    return render_template('api_docs.html')


@dashboard_blueprint.route('/dashboard-data')
def get_dashboard_data():
    """Get data for dashboard visualizations."""
    try:
        # Load sample or uploaded data
        df = load_sample_data()
        
        if df.empty:
            return jsonify({'error': 'No data available'}), 404
        
        # Prepare data for frontend
        data_dict = {
            'dates': df['date'].dt.strftime('%Y-%m-%d').tolist() if 'date' in df.columns else [],
            'in_situ': [None if pd.isna(x) else x for x in df['in_situ'].tolist()] if 'in_situ' in df.columns else [],
            'satellite': [None if pd.isna(x) else x for x in df['satellite'].tolist()] if 'satellite' in df.columns else [],
        }
        
        # Calculate basic statistics
        stats = {}
        if 'in_situ' in df.columns:
            stats['in_situ'] = {
                'mean': float(df['in_situ'].mean()),
                'std': float(df['in_situ'].std()),
                'min': float(df['in_situ'].min()),
                'max': float(df['in_situ'].max()),
                'count': int(df['in_situ'].count())
            }
        
        if 'satellite' in df.columns:
            stats['satellite'] = {
                'mean': float(df['satellite'].mean()),
                'std': float(df['satellite'].std()),
                'min': float(df['satellite'].min()),
                'max': float(df['satellite'].max()),
                'count': int(df['satellite'].count())
            }
        
        # Calculate correlation if both columns exist
        correlation = None
        if 'in_situ' in df.columns and 'satellite' in df.columns:
            valid_data = df.dropna(subset=['in_situ', 'satellite'])
            if len(valid_data) > 1:
                correlation = float(valid_data['in_situ'].corr(valid_data['satellite']))
        
        return jsonify({
            'data': data_dict,
            'stats': stats,
            'correlation': correlation,
            'n_samples': len(df)
        })
        
    except Exception as e:
        logger.error(f"Dashboard data error: {e}")
        return jsonify({'error': str(e)}), 500


# Note: Plotting is now handled by Chart.js on the frontend.
# The dashboard-data endpoint provides raw data for client-side chart generation.


@dashboard_blueprint.route('/export-data')
def export_data():
    """Export data in various formats."""
    try:
        format_type = request.args.get('format', 'csv')
        
        df = load_sample_data()
        
        if df.empty:
            return jsonify({'error': 'No data available'}), 404
        
        if format_type == 'csv':
            # Return CSV data
            csv_data = df.to_csv(index=False)
            return jsonify({
                'data': csv_data,
                'filename': 'soil_moisture_data.csv',
                'content_type': 'text/csv'
            })
        
        elif format_type == 'json':
            # Convert dates to strings for JSON serialization
            df_json = df.copy()
            if 'date' in df_json.columns:
                df_json['date'] = df_json['date'].dt.strftime('%Y-%m-%d')
            
            json_data = df_json.to_json(orient='records', indent=2)
            return jsonify({
                'data': json_data,
                'filename': 'soil_moisture_data.json',
                'content_type': 'application/json'
            })
        
        else:
            return jsonify({'error': 'Unsupported format'}), 400
            
    except Exception as e:
        logger.error(f"Data export error: {e}")
        return jsonify({'error': str(e)}), 500
