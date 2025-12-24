"""
Common utilities and shared functionality for the soilmoisture package.

This module contains unified implementations of configuration management,
data loading, application factories, and common interfaces to eliminate
duplication across the codebase.
"""

from .config import ConfigManager
from .data_loader import DataLoader, DataValidationError

__all__ = [
    'ConfigManager',
    'DataLoader',
    'DataValidationError',
]
