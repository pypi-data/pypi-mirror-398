"""
Database backend for utility pole health assessment system.
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import JSON
from datetime import datetime
import os
import logging
import pandas as pd

logger = logging.getLogger(__name__)

Base = declarative_base()


class Pole(Base):
    """Utility pole database table."""
    __tablename__ = 'poles'
    
    id = Column(Integer, primary_key=True)
    pole_id = Column(String(50), unique=True, nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    
    # Basic specifications
    pole_type = Column(String(20), nullable=False)  # wood, concrete, steel, composite
    material = Column(String(100))
    height_ft = Column(Float, nullable=False)
    install_date = Column(DateTime, nullable=False)
    voltage_class = Column(String(20))  # distribution, transmission
    structure_type = Column(String(30))  # tangent, dead-end, corner
    
    # Physical characteristics
    diameter_top_inches = Column(Float)
    diameter_base_inches = Column(Float)
    treatment_type = Column(String(50))
    depth_ft = Column(Float)
    
    # Asset management
    manufacturer = Column(String(100))
    model_number = Column(String(50))
    serial_number = Column(String(50))
    asset_tag = Column(String(50))
    book_value = Column(Float)
    replacement_cost = Column(Float)
    
    # Operational context
    circuit_id = Column(String(50))
    substation = Column(String(100))
    feeder = Column(String(50))
    phase_configuration = Column(String(10))
    
    # Access and environment
    access_difficulty = Column(String(20))  # easy, moderate, difficult
    terrain_type = Column(String(30))
    traffic_exposure = Column(String(20))  # low, medium, high
    
    # Status
    condition_rating = Column(String(20))  # excellent, good, fair, poor, critical
    last_inspection_date = Column(DateTime)
    inspection_frequency_months = Column(Integer, default=60)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    soil_samples = relationship("SoilSample", back_populates="pole")
    inspections = relationship("StructuralInspection", back_populates="pole")
    health_assessments = relationship("HealthAssessment", back_populates="pole")
    work_orders = relationship("WorkOrder", back_populates="pole")


class SoilSample(Base):
    """Soil sample database table."""
    __tablename__ = 'soil_samples'
    
    id = Column(Integer, primary_key=True)
    pole_id = Column(String(50), ForeignKey('poles.pole_id'), nullable=False, index=True)
    sample_date = Column(DateTime, nullable=False)
    depth_inches = Column(Float, nullable=False)
    
    # Physical properties
    moisture_content = Column(Float, nullable=False)  # m³/m³
    bulk_density = Column(Float)  # g/cm³
    porosity = Column(Float)  # fraction
    permeability = Column(Float)  # cm/hr
    
    # Chemical properties
    ph = Column(Float)
    electrical_conductivity = Column(Float)  # dS/m
    organic_matter = Column(Float)  # percentage
    
    # Mechanical properties
    bearing_capacity = Column(Float)  # kPa
    angle_internal_friction = Column(Float)  # degrees
    cohesion = Column(Float)  # kPa
    
    # Classification
    soil_type = Column(String(30))
    uscs_classification = Column(String(10))
    
    # Environmental
    temperature_c = Column(Float)
    freeze_thaw_cycles = Column(Integer)
    seasonal_variation = Column(String(20))
    
    # Quality
    data_quality = Column(String(20), default='good')
    measurement_method = Column(String(50))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    pole = relationship("Pole", back_populates="soil_samples")


class StructuralInspection(Base):
    """Structural inspection database table."""
    __tablename__ = 'structural_inspections'
    
    id = Column(Integer, primary_key=True)
    inspection_id = Column(String(50), unique=True, nullable=False)
    pole_id = Column(String(50), ForeignKey('poles.pole_id'), nullable=False, index=True)
    inspection_date = Column(DateTime, nullable=False)
    inspector_id = Column(String(50), nullable=False)
    inspection_type = Column(String(30), nullable=False)  # visual, detailed, resistograph, etc.
    
    # Overall assessment
    overall_condition = Column(String(20))  # excellent, good, fair, poor, critical
    visible_damage = Column(Boolean, default=False)
    damage_description = Column(Text)
    
    # Material-specific assessments
    wood_decay_depth = Column(Float)  # inches
    wood_circumferential_loss = Column(Float)  # percentage
    concrete_cracking = Column(Boolean)
    concrete_spalling = Column(Boolean)
    steel_corrosion_level = Column(Integer)  # 1-5 scale
    coating_condition = Column(String(20))
    
    # Structural measurements
    ground_line_circumference = Column(Float)  # inches
    lean_angle = Column(Float)  # degrees
    twist_angle = Column(Float)  # degrees
    
    # Load-bearing assessment
    estimated_remaining_strength = Column(Float)  # percentage
    load_test_result = Column(String(50))
    
    # Documentation
    photo_paths = Column(JSON)  # List of photo file paths
    notes = Column(Text)
    
    # Quality and recommendations
    confidence_level = Column(Float, default=1.0)
    recommended_action = Column(Text)
    next_inspection_date = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    pole = relationship("Pole", back_populates="inspections")


class HealthAssessment(Base):
    """Pole health assessment database table."""
    __tablename__ = 'health_assessments'
    
    id = Column(Integer, primary_key=True)
    pole_id = Column(String(50), ForeignKey('poles.pole_id'), nullable=False, index=True)
    assessment_date = Column(DateTime, nullable=False)
    
    # Overall scores (0-100)
    overall_health_score = Column(Float, nullable=False)
    soil_stability_score = Column(Float, nullable=False)
    structural_risk_score = Column(Float, nullable=False)
    
    # Individual risk factors (0-1)
    moisture_risk = Column(Float, default=0.0)
    erosion_risk = Column(Float, default=0.0)
    chemical_corrosion_risk = Column(Float, default=0.0)
    freeze_thaw_risk = Column(Float, default=0.0)
    bearing_capacity_risk = Column(Float, default=0.0)
    
    # Weather-enhanced risks
    current_weather_risk = Column(Float, default=0.0)
    forecast_weather_risk = Column(Float, default=0.0)
    combined_weather_risk = Column(Float, default=0.0)
    
    # Predicted metrics
    predicted_failure_probability = Column(Float)  # next 5 years
    recommended_inspection_interval = Column(Integer)  # months
    
    # Action flags
    requires_immediate_attention = Column(Boolean, default=False)
    requires_monitoring = Column(Boolean, default=False)
    maintenance_priority = Column(String(20), default='low')
    
    # Supporting data
    confidence_level = Column(Float, default=0.8)
    data_completeness = Column(Float, default=1.0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    pole = relationship("Pole", back_populates="health_assessments")


class WorkOrder(Base):
    """Work order database table."""
    __tablename__ = 'work_orders'
    
    id = Column(Integer, primary_key=True)
    work_order_id = Column(String(50), unique=True, nullable=False)
    pole_id = Column(String(50), ForeignKey('poles.pole_id'), nullable=False, index=True)
    
    # Work details
    work_type = Column(String(30), nullable=False)  # inspection, maintenance, replacement, emergency
    priority = Column(String(20), nullable=False)  # critical, high, medium, low
    description = Column(Text, nullable=False)
    estimated_hours = Column(Float)
    estimated_cost = Column(Float)
    
    # Scheduling
    created_date = Column(DateTime, default=datetime.utcnow)
    scheduled_date = Column(DateTime)
    assigned_crew = Column(String(100))
    required_skills = Column(JSON)  # List of required skills
    required_materials = Column(JSON)  # List of materials
    
    # Status tracking
    status = Column(String(20), default='open')  # open, assigned, in_progress, completed, cancelled
    completion_date = Column(DateTime)
    actual_hours = Column(Float)
    actual_cost = Column(Float)
    
    # Results
    work_performed = Column(Text)
    issues_found = Column(Text)
    photos_taken = Column(JSON)  # List of photo paths
    follow_up_required = Column(Boolean, default=False)
    
    # Timestamps
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    pole = relationship("Pole", back_populates="work_orders")


class WeatherData(Base):
    """Weather data database table."""
    __tablename__ = 'weather_data'
    
    id = Column(Integer, primary_key=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    
    # Current conditions
    temperature_c = Column(Float)
    humidity_percent = Column(Float)
    wind_speed_mph = Column(Float)
    wind_direction_deg = Column(Float)
    pressure_mb = Column(Float)
    
    # Precipitation
    precipitation_mm = Column(Float)
    rain_1h_mm = Column(Float)
    snow_1h_mm = Column(Float)
    
    # Conditions
    visibility_km = Column(Float)
    cloud_cover_percent = Column(Float)
    weather_description = Column(String(100))
    
    # Derived
    feels_like_c = Column(Float)
    dew_point_c = Column(Float)
    uv_index = Column(Float)
    
    # Data source
    data_source = Column(String(50), default='openweathermap')
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)


class DatabaseManager:
    """Database connection and session management."""
    
    def __init__(self, database_url: str = None):
        """Initialize database connection."""
        
        # Default to SQLite for development
        if database_url is None:
            database_url = os.getenv('DATABASE_URL', 'sqlite:///pole_assessment.db')
        
        self.database_url = database_url
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        logger.info(f"Database initialized: {database_url}")
    
    def create_tables(self):
        """Create all database tables."""
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created")
    
    def get_session(self):
        """Get database session."""
        return self.SessionLocal()
    
    def close(self):
        """Close database connection."""
        self.engine.dispose()


class PoleDataAccess:
    """Data access layer for pole operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def create_pole(self, pole_data: dict) -> Pole:
        """Create a new pole record."""
        session = self.db_manager.get_session()
        try:
            pole = Pole(**pole_data)
            session.add(pole)
            session.commit()
            session.refresh(pole)
            return pole
        finally:
            session.close()
    
    def get_pole(self, pole_id: str) -> Pole:
        """Get pole by ID."""
        session = self.db_manager.get_session()
        try:
            return session.query(Pole).filter(Pole.pole_id == pole_id).first()
        finally:
            session.close()
    
    def get_all_poles(self) -> list:
        """Get all poles."""
        session = self.db_manager.get_session()
        try:
            return session.query(Pole).all()
        finally:
            session.close()
    
    def update_pole(self, pole_id: str, updates: dict) -> Pole:
        """Update pole record."""
        session = self.db_manager.get_session()
        try:
            pole = session.query(Pole).filter(Pole.pole_id == pole_id).first()
            if pole:
                for key, value in updates.items():
                    setattr(pole, key, value)
                pole.updated_at = datetime.utcnow()
                session.commit()
                session.refresh(pole)
            return pole
        finally:
            session.close()
    
    def add_soil_sample(self, sample_data: dict) -> SoilSample:
        """Add soil sample."""
        session = self.db_manager.get_session()
        try:
            sample = SoilSample(**sample_data)
            session.add(sample)
            session.commit()
            session.refresh(sample)
            return sample
        finally:
            session.close()
    
    def get_soil_samples(self, pole_id: str = None) -> list:
        """Get soil samples, optionally filtered by pole."""
        session = self.db_manager.get_session()
        try:
            query = session.query(SoilSample)
            if pole_id:
                query = query.filter(SoilSample.pole_id == pole_id)
            return query.order_by(SoilSample.sample_date.desc()).all()
        finally:
            session.close()
    
    def add_inspection(self, inspection_data: dict) -> StructuralInspection:
        """Add structural inspection."""
        session = self.db_manager.get_session()
        try:
            inspection = StructuralInspection(**inspection_data)
            session.add(inspection)
            session.commit()
            session.refresh(inspection)
            return inspection
        finally:
            session.close()
    
    def get_inspections(self, pole_id: str = None) -> list:
        """Get inspections, optionally filtered by pole."""
        session = self.db_manager.get_session()
        try:
            query = session.query(StructuralInspection)
            if pole_id:
                query = query.filter(StructuralInspection.pole_id == pole_id)
            return query.order_by(StructuralInspection.inspection_date.desc()).all()
        finally:
            session.close()
    
    def add_health_assessment(self, assessment_data: dict) -> HealthAssessment:
        """Add health assessment."""
        session = self.db_manager.get_session()
        try:
            assessment = HealthAssessment(**assessment_data)
            session.add(assessment)
            session.commit()
            session.refresh(assessment)
            return assessment
        finally:
            session.close()
    
    def get_latest_health_assessment(self, pole_id: str) -> HealthAssessment:
        """Get latest health assessment for pole."""
        session = self.db_manager.get_session()
        try:
            return (session.query(HealthAssessment)
                   .filter(HealthAssessment.pole_id == pole_id)
                   .order_by(HealthAssessment.assessment_date.desc())
                   .first())
        finally:
            session.close()
    
    def create_work_order(self, work_order_data: dict) -> WorkOrder:
        """Create work order."""
        session = self.db_manager.get_session()
        try:
            work_order = WorkOrder(**work_order_data)
            session.add(work_order)
            session.commit()
            session.refresh(work_order)
            return work_order
        finally:
            session.close()
    
    def get_work_orders(self, pole_id: str = None, status: str = None) -> list:
        """Get work orders with optional filters."""
        session = self.db_manager.get_session()
        try:
            query = session.query(WorkOrder)
            if pole_id:
                query = query.filter(WorkOrder.pole_id == pole_id)
            if status:
                query = query.filter(WorkOrder.status == status)
            return query.order_by(WorkOrder.created_date.desc()).all()
        finally:
            session.close()
    
    def add_weather_data(self, weather_data: dict) -> WeatherData:
        """Add weather data."""
        session = self.db_manager.get_session()
        try:
            weather = WeatherData(**weather_data)
            session.add(weather)
            session.commit()
            session.refresh(weather)
            return weather
        finally:
            session.close()
    
    def get_weather_data(self, latitude: float, longitude: float, 
                        hours: int = 24) -> list:
        """Get recent weather data for location."""
        session = self.db_manager.get_session()
        try:
            cutoff_time = datetime.utcnow() - pd.Timedelta(hours=hours)
            return (session.query(WeatherData)
                   .filter(WeatherData.latitude.between(latitude-0.01, latitude+0.01))
                   .filter(WeatherData.longitude.between(longitude-0.01, longitude+0.01))
                   .filter(WeatherData.timestamp >= cutoff_time)
                   .order_by(WeatherData.timestamp.desc())
                   .all())
        finally:
            session.close()
