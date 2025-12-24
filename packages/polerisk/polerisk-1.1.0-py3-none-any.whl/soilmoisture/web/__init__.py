"""
Web interface module for soil moisture analysis.

This module provides a web-based dashboard and API for interacting with soil moisture data,
including visualization, analysis, and machine learning capabilities.
"""

from .app import create_app, run_server
from .api import api_blueprint
from .dashboard import dashboard_blueprint

__all__ = [
    "create_app",
    "run_server", 
    "api_blueprint",
    "dashboard_blueprint",
]
