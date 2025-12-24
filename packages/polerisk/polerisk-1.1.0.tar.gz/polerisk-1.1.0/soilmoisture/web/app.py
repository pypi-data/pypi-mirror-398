"""
Flask web application for soil moisture analysis.
"""

import os
import logging
from pathlib import Path
from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_cors import CORS

from .api import api_blueprint
from .dashboard import dashboard_blueprint

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app(config=None):
    """Create and configure the Flask application."""
    app = Flask(__name__, 
                template_folder=str(Path(__file__).parent / 'templates'),
                static_folder=str(Path(__file__).parent / 'static'))
    
    # Configuration
    app.config.update({
        'SECRET_KEY': os.environ.get('SECRET_KEY', 'dev-key-change-in-production'),
        'DEBUG': os.environ.get('FLASK_DEBUG', 'False').lower() == 'true',
        'DATA_DIR': os.environ.get('DATA_DIR', './data'),
        'OUTPUT_DIR': os.environ.get('OUTPUT_DIR', './output'),
        'UPLOAD_FOLDER': os.environ.get('UPLOAD_FOLDER', './uploads'),
        'MAX_CONTENT_LENGTH': 16 * 1024 * 1024,  # 16MB max file size
    })
    
    if config:
        app.config.update(config)
    
    # Enable CORS for API endpoints
    CORS(app, origins=['http://localhost:3000', 'http://127.0.0.1:3000'])
    
    # Ensure required directories exist
    for dir_key in ['DATA_DIR', 'OUTPUT_DIR', 'UPLOAD_FOLDER']:
        Path(app.config[dir_key]).mkdir(parents=True, exist_ok=True)
    
    # Register blueprints
    logger.debug(api_blueprint, url_prefix='/api')
    logger.debug(dashboard_blueprint)
    
    # Main routes
    @app.route('/')
    def index():
        """Main dashboard page."""
        return render_template('index.html')
    
    @app.route('/health')
    def health_check():
        """Health check endpoint."""
        return jsonify({
            'status': 'healthy',
            'version': '1.0.0',
            'features': {
                'ml_models': True,
                'visualizations': True,
                'api': True
            }
        })
    
    @app.route('/favicon.ico')
    def favicon():
        """Favicon route."""
        return send_from_directory(app.static_folder, 'favicon.ico', 
                                 mimetype='image/vnd.microsoft.icon')
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Endpoint not found'}), 404
        return render_template('error.html', error='Page not found'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Internal server error'}), 500
        return render_template('error.html', error='Internal server error'), 500
    
    @app.errorhandler(413)
    def too_large(error):
        return jsonify({'error': 'File too large'}), 413
    
    logger.info("Flask app created successfully")
    return app


def run_server(host='127.0.0.1', port=5000, debug=False):
    """Run the development server."""
    app = create_app()
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    run_server(debug=True)
