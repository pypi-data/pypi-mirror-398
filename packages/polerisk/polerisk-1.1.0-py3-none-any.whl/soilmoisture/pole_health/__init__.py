"""
Utility Pole Health Assessment Module.

This module contains functions and classes for assessing utility pole health
based on soil conditions, pole characteristics, and environmental factors.
"""

from .assessment import PoleHealthAssessment, SoilConditionAnalyzer
from .risk_scoring import PoleRiskScorer, MaintenanceScheduler
from .pole_data import PoleInfo, SoilSample

__all__ = [
    'PoleHealthAssessment',
    'SoilConditionAnalyzer', 
    'PoleRiskScorer',
    'MaintenanceScheduler',
    'PoleInfo',
    'SoilSample'
]
