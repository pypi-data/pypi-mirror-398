"""
Enhanced pole data models with structural inspection and operational features.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from enum import Enum
import numpy as np


class PoleCondition(Enum):
    """Standardized pole condition ratings."""
    EXCELLENT = "excellent"
    GOOD = "good" 
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"


class InspectionType(Enum):
    """Types of pole inspections."""
    VISUAL = "visual"
    DETAILED = "detailed"
    RESISTOGRAPH = "resistograph"
    SONIC = "sonic"
    EXCAVATION = "excavation"
    CLIMBING = "climbing"


@dataclass
class StructuralInspection:
    """Physical structural inspection data."""
    
    inspection_id: str
    pole_id: str
    inspection_date: datetime
    inspector_id: str
    inspection_type: InspectionType
    
    # Visual inspection results
    overall_condition: PoleCondition
    visible_damage: bool = False
    damage_description: Optional[str] = None
    
    # Material-specific assessments
    wood_decay_depth: Optional[float] = None  # inches
    wood_circumferential_loss: Optional[float] = None  # percentage
    concrete_cracking: Optional[bool] = None
    concrete_spalling: Optional[bool] = None
    steel_corrosion_level: Optional[int] = None  # 1-5 scale
    coating_condition: Optional[str] = None
    
    # Structural measurements
    ground_line_circumference: Optional[float] = None  # inches
    lean_angle: Optional[float] = None  # degrees
    twist_angle: Optional[float] = None  # degrees
    
    # Load-bearing assessment
    estimated_remaining_strength: Optional[float] = None  # percentage
    load_test_result: Optional[str] = None
    
    # Photos and documentation
    photo_paths: List[str] = None
    notes: Optional[str] = None
    
    # Quality and recommendations
    confidence_level: float = 1.0
    recommended_action: Optional[str] = None
    next_inspection_date: Optional[datetime] = None


@dataclass
class LoadAnalysis:
    """Engineering load analysis for utility pole."""
    
    pole_id: str
    analysis_date: datetime
    engineer_id: str
    
    # Environmental loads
    wind_load_lbs: Optional[float] = None
    ice_load_lbs: Optional[float] = None
    seismic_factor: Optional[float] = None
    
    # Electrical loads
    conductor_weight_lbs: Optional[float] = None
    conductor_tension_lbs: Optional[float] = None
    equipment_weight_lbs: Optional[float] = None
    
    # Foundation analysis
    foundation_type: Optional[str] = None
    embedment_depth_ft: Optional[float] = None
    backfill_type: Optional[str] = None
    foundation_capacity_lbs: Optional[float] = None
    
    # Safety factors
    design_load_lbs: Optional[float] = None
    actual_load_lbs: Optional[float] = None
    safety_factor: Optional[float] = None
    
    # Results
    load_rating_adequate: bool = True
    maximum_allowable_load: Optional[float] = None
    recommended_upgrades: Optional[str] = None


@dataclass
class IoTSensorData:
    """IoT sensor measurements from pole monitoring devices."""
    
    sensor_id: str
    pole_id: str
    timestamp: datetime
    
    # Tilt and movement
    tilt_x: Optional[float] = None  # degrees
    tilt_y: Optional[float] = None  # degrees
    acceleration_x: Optional[float] = None  # g-force
    acceleration_y: Optional[float] = None  # g-force
    acceleration_z: Optional[float] = None  # g-force
    
    # Environmental
    temperature_c: Optional[float] = None
    humidity_percent: Optional[float] = None
    wind_speed_mph: Optional[float] = None
    vibration_frequency_hz: Optional[float] = None
    
    # Power and connectivity
    battery_voltage: Optional[float] = None
    signal_strength_dbm: Optional[int] = None
    
    # Data quality
    sensor_status: str = "online"
    data_quality: str = "good"


@dataclass
class WorkOrder:
    """Maintenance work order."""
    
    work_order_id: str
    pole_id: str
    created_date: datetime
    
    # Work details
    work_type: str  # inspection, maintenance, replacement, emergency
    priority: str  # critical, high, medium, low
    description: str
    estimated_hours: Optional[float] = None
    estimated_cost: Optional[float] = None
    
    # Scheduling
    scheduled_date: Optional[datetime] = None
    assigned_crew: Optional[str] = None
    required_skills: List[str] = None
    required_materials: List[Dict[str, Any]] = None
    
    # Status tracking
    status: str = "open"  # open, assigned, in_progress, completed, cancelled
    completion_date: Optional[datetime] = None
    actual_hours: Optional[float] = None
    actual_cost: Optional[float] = None
    
    # Results
    work_performed: Optional[str] = None
    issues_found: Optional[str] = None
    photos_taken: List[str] = None
    follow_up_required: bool = False


@dataclass
class RiskAssessment:
    """Comprehensive risk assessment combining all factors."""
    
    pole_id: str
    assessment_date: datetime
    
    # Individual risk components (0-1 scale)
    structural_risk: float
    soil_risk: float
    environmental_risk: float
    load_risk: float
    age_risk: float
    
    # Composite risk scores
    failure_probability_1yr: float
    failure_probability_5yr: float
    consequence_score: float  # impact if pole fails
    
    # Risk categories
    public_safety_risk: str  # low, medium, high, critical
    service_reliability_risk: str
    financial_risk: str
    environmental_impact_risk: str
    
    # Mitigation strategies
    recommended_actions: List[str]
    risk_reduction_potential: float  # after mitigation
    cost_to_mitigate: Optional[float] = None
    
    # Confidence and validation
    assessment_confidence: float = 0.8
    data_sources: List[str] = None
    validation_notes: Optional[str] = None


@dataclass
class NetworkImpactAnalysis:
    """Analysis of pole failure impact on electrical network."""
    
    pole_id: str
    analysis_date: datetime
    
    # Connected infrastructure
    downstream_poles: List[str]
    connected_transformers: List[str] 
    affected_feeders: List[str]
    backup_routes_available: bool
    
    # Customer impact
    customers_affected: int
    critical_customers: int  # hospitals, emergency services
    average_outage_duration_hours: float
    estimated_outage_cost: float
    
    # System reliability
    system_reliability_impact: float  # SAIDI/SAIFI impact
    cascade_failure_probability: float
    load_transfer_capacity: float  # percentage
    
    # Mitigation options
    temporary_solutions: List[str]
    permanent_solutions: List[str]
    estimated_restoration_time: float


# Enhanced main pole info class
@dataclass 
class EnhancedPoleInfo:
    """Comprehensive pole information with all operational data."""
    
    # Basic identification (from original PoleInfo)
    pole_id: str
    latitude: float
    longitude: float
    pole_type: str
    material: str
    height_ft: float
    install_date: datetime
    voltage_class: str
    structure_type: str
    
    # Enhanced pole specifications
    pole_class: Optional[str] = None  # ANSI pole class
    manufacturer: Optional[str] = None
    model_number: Optional[str] = None
    serial_number: Optional[str] = None
    
    # Installation details
    embedment_depth_ft: Optional[float] = None
    backfill_material: Optional[str] = None
    foundation_type: Optional[str] = None
    installation_contractor: Optional[str] = None
    
    # Operational context  
    circuit_id: Optional[str] = None
    substation: Optional[str] = None
    feeder: Optional[str] = None
    phase_configuration: Optional[str] = None
    
    # Load information
    installed_equipment: List[str] = None
    conductor_types: List[str] = None
    estimated_total_load_lbs: Optional[float] = None
    
    # Accessibility and environment
    access_difficulty: Optional[str] = None  # easy, moderate, difficult
    terrain_type: Optional[str] = None
    vegetation_density: Optional[str] = None
    traffic_exposure: Optional[str] = None  # low, medium, high
    
    # Asset management
    asset_tag: Optional[str] = None
    accounting_unit: Optional[str] = None
    depreciation_method: Optional[str] = None
    book_value: Optional[float] = None
    replacement_cost: Optional[float] = None
    
    # Historical data
    major_repairs: List[Dict[str, Any]] = None
    previous_replacements: List[Dict[str, Any]] = None
    insurance_claims: List[Dict[str, Any]] = None
    
    # Regulatory and compliance
    inspection_frequency_months: int = 60  # default 5 years
    last_regulatory_inspection: Optional[datetime] = None
    compliance_issues: List[str] = None
    
    # Smart features
    iot_sensors_installed: bool = False
    sensor_ids: List[str] = None
    monitoring_frequency: Optional[str] = None
    
    def __post_init__(self):
        """Calculate derived fields."""
        if self.install_date:
            self.age_years = (datetime.now() - self.install_date).days / 365.25
