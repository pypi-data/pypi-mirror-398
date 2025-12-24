"""
Data models for utility pole and soil information.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime
import numpy as np


@dataclass
class PoleInfo:
    """Information about a utility pole."""
    
    pole_id: str
    latitude: float
    longitude: float
    pole_type: str  # wood, concrete, steel, composite
    material: str   # specific material (e.g., Douglas Fir, Southern Pine)
    height_ft: float
    install_date: datetime
    voltage_class: str  # distribution, transmission
    structure_type: str  # tangent, dead-end, corner, etc.
    
    # Optional fields
    diameter_top_inches: Optional[float] = None
    diameter_base_inches: Optional[float] = None
    treatment_type: Optional[str] = None  # CCA, pentachlorophenol, etc.
    last_inspection_date: Optional[datetime] = None
    condition_rating: Optional[str] = None  # excellent, good, fair, poor
    depth_ft: Optional[float] = None
    
    # Calculated fields
    age_years: Optional[float] = None
    
    def __post_init__(self):
        """Calculate derived fields."""
        if self.install_date:
            self.age_years = (datetime.now() - self.install_date).days / 365.25


@dataclass
class SoilSample:
    """Soil measurement data at a pole location."""
    
    pole_id: str
    sample_date: datetime
    depth_inches: float
    
    # Physical properties
    moisture_content: float  # volumetric water content (m³/m³)
    bulk_density: Optional[float] = None  # g/cm³
    porosity: Optional[float] = None  # fraction
    permeability: Optional[float] = None  # cm/hr
    
    # Chemical properties  
    ph: Optional[float] = None
    electrical_conductivity: Optional[float] = None  # dS/m
    organic_matter: Optional[float] = None  # percentage
    
    # Mechanical properties
    bearing_capacity: Optional[float] = None  # kPa
    angle_internal_friction: Optional[float] = None  # degrees
    cohesion: Optional[float] = None  # kPa
    
    # Classification
    soil_type: Optional[str] = None  # clay, silt, sand, gravel
    uscs_classification: Optional[str] = None  # Unified Soil Classification System
    
    # Environmental conditions
    temperature_c: Optional[float] = None
    freeze_thaw_cycles: Optional[int] = None
    seasonal_variation: Optional[str] = None
    
    # Quality flags
    data_quality: str = "good"  # good, questionable, poor
    measurement_method: Optional[str] = None
    
    
@dataclass
class PoleHealthMetrics:
    """Calculated health metrics for a utility pole."""
    
    pole_id: str
    assessment_date: datetime
    
    # Overall scores (0-100)
    overall_health_score: float
    soil_stability_score: float
    structural_risk_score: float
    
    # Individual risk factors (0-1, higher is worse)
    moisture_risk: float
    erosion_risk: float
    chemical_corrosion_risk: float
    freeze_thaw_risk: float
    bearing_capacity_risk: float
    
    # Predicted metrics
    predicted_failure_probability: Optional[float] = None  # next 5 years
    recommended_inspection_interval: Optional[int] = None  # months
    
    # Action flags
    requires_immediate_attention: bool = False
    requires_monitoring: bool = False
    maintenance_priority: str = "low"  # low, medium, high, critical
    
    # Supporting data
    confidence_level: float = 0.8  # confidence in assessment
    data_completeness: float = 1.0  # fraction of required data available
    
    
@dataclass
class WeatherData:
    """Weather data for pole location analysis."""
    
    location: tuple  # (lat, lon)
    date: datetime
    
    # Precipitation
    daily_precipitation_mm: Optional[float] = None
    monthly_precipitation_mm: Optional[float] = None
    precipitation_intensity: Optional[str] = None  # light, moderate, heavy
    
    # Temperature
    avg_temperature_c: Optional[float] = None
    min_temperature_c: Optional[float] = None
    max_temperature_c: Optional[float] = None
    freeze_thaw_cycles_count: Optional[int] = None
    
    # Wind
    wind_speed_mph: Optional[float] = None
    wind_direction: Optional[str] = None
    storm_events: Optional[List[str]] = None
    
    # Seasonal patterns
    season: Optional[str] = None
    drought_index: Optional[float] = None
    flooding_risk: Optional[str] = None  # low, medium, high


class PoleDatabase:
    """Database interface for pole and soil data."""
    
    def __init__(self):
        self.poles: Dict[str, PoleInfo] = {}
        self.soil_samples: Dict[str, List[SoilSample]] = {}
        self.health_metrics: Dict[str, List[PoleHealthMetrics]] = {}
        self.weather_data: Dict[str, List[WeatherData]] = {}
    
    def add_pole(self, pole: PoleInfo):
        """Add a pole to the database."""
        self.poles[pole.pole_id] = pole
        if pole.pole_id not in self.soil_samples:
            self.soil_samples[pole.pole_id] = []
    
    def add_soil_sample(self, sample: SoilSample):
        """Add a soil sample to the database."""
        if sample.pole_id not in self.soil_samples:
            self.soil_samples[sample.pole_id] = []
        self.soil_samples[sample.pole_id].append(sample)
    
    def get_pole_history(self, pole_id: str) -> Dict[str, Any]:
        """Get complete history for a pole."""
        return {
            'pole_info': self.poles.get(pole_id),
            'soil_samples': self.soil_samples.get(pole_id, []),
            'health_metrics': self.health_metrics.get(pole_id, []),
            'weather_data': self.weather_data.get(pole_id, [])
        }
    
    def get_poles_by_risk_level(self, risk_level: str) -> List[str]:
        """Get poles by maintenance priority level."""
        high_risk_poles = []
        for pole_id, metrics_list in self.health_metrics.items():
            if metrics_list:
                latest_metrics = max(metrics_list, key=lambda x: x.assessment_date)
                if latest_metrics.maintenance_priority == risk_level:
                    high_risk_poles.append(pole_id)
        return high_risk_poles
