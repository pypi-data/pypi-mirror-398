"""
Soil condition analysis and pole health assessment algorithms.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta
import logging
from dataclasses import asdict

from .pole_data import PoleInfo, SoilSample, PoleHealthMetrics, WeatherData
from ..analysis.statistics import calculate_correlation, calculate_rmse

logger = logging.getLogger(__name__)


class SoilConditionAnalyzer:
    """Analyzes soil conditions for utility pole stability assessment."""
    
    def __init__(self):
        # Optimal ranges for different soil parameters
        self.optimal_ranges = {
            'moisture_content': (0.15, 0.35),  # m³/m³
            'ph': (6.0, 8.0),
            'bulk_density': (1.2, 1.8),  # g/cm³
            'electrical_conductivity': (0.0, 2.0),  # dS/m
            'bearing_capacity': (100, 500),  # kPa
            'porosity': (0.35, 0.55)  # fraction
        }
        
        # Critical thresholds for risk assessment
        self.critical_thresholds = {
            'moisture_content_high': 0.45,  # High moisture - erosion/instability risk
            'moisture_content_low': 0.08,   # Too dry - poor compaction
            'ph_low': 5.0,                  # Acidic - corrosion risk
            'ph_high': 9.0,                 # Alkaline - chemical reactions
            'electrical_conductivity_high': 4.0,  # High salinity
            'bearing_capacity_low': 50      # kPa - insufficient support
        }
    
    def analyze_soil_sample(self, sample: SoilSample) -> Dict[str, float]:
        """
        Analyze a single soil sample and return risk scores.
        
        Returns:
            Dictionary with risk scores (0-1, higher is worse)
        """
        risks = {}
        
        # Moisture content analysis
        if sample.moisture_content is not None:
            moisture_risk = self._assess_moisture_risk(sample.moisture_content)
            risks['moisture_risk'] = moisture_risk
        
        # pH analysis
        if sample.ph is not None:
            ph_risk = self._assess_ph_risk(sample.ph)
            risks['chemical_corrosion_risk'] = ph_risk
        
        # Electrical conductivity (salinity)
        if sample.electrical_conductivity is not None:
            ec_risk = self._assess_ec_risk(sample.electrical_conductivity)
            risks['salinity_risk'] = ec_risk
        
        # Bearing capacity
        if sample.bearing_capacity is not None:
            bearing_risk = self._assess_bearing_capacity_risk(sample.bearing_capacity)
            risks['bearing_capacity_risk'] = bearing_risk
        
        # Bulk density
        if sample.bulk_density is not None:
            density_risk = self._assess_density_risk(sample.bulk_density)
            risks['compaction_risk'] = density_risk
        
        return risks
    
    def _assess_moisture_risk(self, moisture: float) -> float:
        """Assess risk from soil moisture content."""
        if moisture > self.critical_thresholds['moisture_content_high']:
            # Very high moisture - erosion, instability
            return min(1.0, (moisture - self.critical_thresholds['moisture_content_high']) / 0.2)
        elif moisture < self.critical_thresholds['moisture_content_low']:
            # Very low moisture - poor compaction, dust
            return min(1.0, (self.critical_thresholds['moisture_content_low'] - moisture) / 0.05)
        else:
            # Within acceptable range
            optimal_min, optimal_max = self.optimal_ranges['moisture_content']
            if optimal_min <= moisture <= optimal_max:
                return 0.0
            else:
                # Moderate risk outside optimal range but within acceptable limits
                return 0.3
    
    def _assess_ph_risk(self, ph: float) -> float:
        """Assess corrosion risk from soil pH."""
        if ph < self.critical_thresholds['ph_low']:
            # Acidic soil - high corrosion risk
            return min(1.0, (self.critical_thresholds['ph_low'] - ph) / 2.0)
        elif ph > self.critical_thresholds['ph_high']:
            # Alkaline soil - moderate chemical reaction risk
            return min(0.7, (ph - self.critical_thresholds['ph_high']) / 3.0)
        else:
            return 0.0
    
    def _assess_ec_risk(self, ec: float) -> float:
        """Assess risk from electrical conductivity (salinity)."""
        if ec > self.critical_thresholds['electrical_conductivity_high']:
            # High salinity - corrosion risk
            return min(1.0, (ec - self.critical_thresholds['electrical_conductivity_high']) / 4.0)
        else:
            return 0.0
    
    def _assess_bearing_capacity_risk(self, bearing_capacity: float) -> float:
        """Assess structural support risk from bearing capacity."""
        if bearing_capacity < self.critical_thresholds['bearing_capacity_low']:
            # Insufficient bearing capacity
            return min(1.0, (self.critical_thresholds['bearing_capacity_low'] - bearing_capacity) / 50)
        else:
            optimal_min, optimal_max = self.optimal_ranges['bearing_capacity']
            if bearing_capacity < optimal_min:
                return 0.4  # Moderate risk
            return 0.0
    
    def _assess_density_risk(self, bulk_density: float) -> float:
        """Assess compaction risk from bulk density."""
        optimal_min, optimal_max = self.optimal_ranges['bulk_density']
        if bulk_density < optimal_min:
            # Too loose - poor support
            return min(0.8, (optimal_min - bulk_density) / 0.5)
        elif bulk_density > optimal_max:
            # Too dense - drainage issues
            return min(0.6, (bulk_density - optimal_max) / 0.5)
        return 0.0
    
    def analyze_temporal_trends(self, samples: List[SoilSample]) -> Dict[str, float]:
        """Analyze trends in soil conditions over time."""
        if len(samples) < 2:
            return {'trend_risk': 0.0}
        
        # Sort samples by date
        sorted_samples = sorted(samples, key=lambda x: x.sample_date)
        
        # Extract time series data
        dates = [s.sample_date for s in sorted_samples]
        moisture_values = [s.moisture_content for s in sorted_samples if s.moisture_content is not None]
        
        if len(moisture_values) < 2:
            return {'trend_risk': 0.0}
        
        # Calculate trend
        x = np.arange(len(moisture_values))
        slope = np.polyfit(x, moisture_values, 1)[0]
        
        # Assess trend risk
        trend_risk = 0.0
        if abs(slope) > 0.01:  # Significant change in moisture per sample
            trend_risk = min(1.0, abs(slope) * 10)
        
        return {
            'trend_risk': trend_risk,
            'moisture_trend': slope,
            'trend_direction': 'increasing' if slope > 0 else 'decreasing'
        }


class PoleHealthAssessment:
    """Main class for assessing utility pole health based on soil and pole conditions."""
    
    def __init__(self):
        self.soil_analyzer = SoilConditionAnalyzer()
        
        # Pole-specific risk factors
        self.pole_risk_factors = {
            'wood': {
                'age_threshold_years': 25,
                'moisture_sensitivity': 1.2,
                'ph_sensitivity': 1.5,
                'base_failure_rate': 0.02
            },
            'concrete': {
                'age_threshold_years': 40,
                'moisture_sensitivity': 0.8,
                'ph_sensitivity': 1.0,
                'base_failure_rate': 0.01
            },
            'steel': {
                'age_threshold_years': 50,
                'moisture_sensitivity': 1.0,
                'ph_sensitivity': 2.0,  # High corrosion sensitivity
                'base_failure_rate': 0.015
            },
            'composite': {
                'age_threshold_years': 60,
                'moisture_sensitivity': 0.6,
                'ph_sensitivity': 0.5,
                'base_failure_rate': 0.005
            }
        }
    
    def assess_pole_health(self, pole: PoleInfo, soil_samples: List[SoilSample], 
                          weather_data: Optional[List[WeatherData]] = None) -> PoleHealthMetrics:
        """
        Perform comprehensive pole health assessment.
        
        Args:
            pole: Pole information
            soil_samples: List of soil samples for this pole
            weather_data: Optional weather data for enhanced assessment
            
        Returns:
            PoleHealthMetrics with assessment results
        """
        if not soil_samples:
            logger.warning(f"No soil samples available for pole {pole.pole_id}")
            return self._create_default_metrics(pole)
        
        # Get latest soil sample
        latest_sample = max(soil_samples, key=lambda x: x.sample_date)
        
        # Analyze soil conditions
        soil_risks = self.soil_analyzer.analyze_soil_sample(latest_sample)
        
        # Analyze temporal trends if multiple samples available
        temporal_analysis = self.soil_analyzer.analyze_temporal_trends(soil_samples)
        soil_risks.update(temporal_analysis)
        
        # Assess pole-specific risks
        pole_risks = self._assess_pole_specific_risks(pole, latest_sample)
        
        # Calculate overall scores
        overall_health_score = self._calculate_overall_health_score(soil_risks, pole_risks)
        soil_stability_score = self._calculate_soil_stability_score(soil_risks)
        structural_risk_score = self._calculate_structural_risk_score(pole_risks)
        
        # Determine maintenance priority
        maintenance_priority = self._determine_maintenance_priority(
            overall_health_score, soil_risks, pole_risks
        )
        
        # Create health metrics
        metrics = PoleHealthMetrics(
            pole_id=pole.pole_id,
            assessment_date=datetime.now(),
            overall_health_score=overall_health_score,
            soil_stability_score=soil_stability_score,
            structural_risk_score=structural_risk_score,
            moisture_risk=soil_risks.get('moisture_risk', 0.0),
            erosion_risk=self._calculate_erosion_risk(soil_risks, weather_data),
            chemical_corrosion_risk=soil_risks.get('chemical_corrosion_risk', 0.0),
            freeze_thaw_risk=self._calculate_freeze_thaw_risk(soil_risks, weather_data),
            bearing_capacity_risk=soil_risks.get('bearing_capacity_risk', 0.0),
            maintenance_priority=maintenance_priority,
            confidence_level=self._calculate_confidence_level(soil_samples, pole),
            data_completeness=self._calculate_data_completeness(latest_sample)
        )
        
        # Set action flags
        metrics.requires_immediate_attention = (
            overall_health_score < 30 or maintenance_priority == 'critical'
        )
        metrics.requires_monitoring = overall_health_score < 60
        
        return metrics
    
    def _assess_pole_specific_risks(self, pole: PoleInfo, soil_sample: SoilSample) -> Dict[str, float]:
        """Assess risks specific to pole type and characteristics."""
        pole_type = pole.pole_type.lower()
        if pole_type not in self.pole_risk_factors:
            pole_type = 'wood'  # Default
        
        factors = self.pole_risk_factors[pole_type]
        risks = {}
        
        # Age-related risk
        if pole.age_years:
            age_risk = max(0.0, (pole.age_years - factors['age_threshold_years']) / 20)
            risks['age_risk'] = min(1.0, age_risk)
        else:
            risks['age_risk'] = 0.3  # Unknown age = moderate risk
        
        # Material-specific moisture sensitivity
        if soil_sample.moisture_content is not None:
            base_moisture_risk = self.soil_analyzer._assess_moisture_risk(soil_sample.moisture_content)
            risks['material_moisture_risk'] = base_moisture_risk * factors['moisture_sensitivity']
        
        # Material-specific pH sensitivity
        if soil_sample.ph is not None:
            base_ph_risk = self.soil_analyzer._assess_ph_risk(soil_sample.ph)
            risks['material_ph_risk'] = base_ph_risk * factors['ph_sensitivity']
        
        return risks
    
    def _calculate_overall_health_score(self, soil_risks: Dict[str, float], 
                                       pole_risks: Dict[str, float]) -> float:
        """Calculate overall health score (0-100, higher is better)."""
        # Combine all risk factors
        all_risks = list(soil_risks.values()) + list(pole_risks.values())
        if not all_risks:
            return 50.0  # Neutral score if no data
        
        # Weight different risk factors
        weighted_risks = []
        
        # High-priority risks
        for risk_name in ['moisture_risk', 'bearing_capacity_risk', 'chemical_corrosion_risk']:
            if risk_name in soil_risks:
                weighted_risks.extend([soil_risks[risk_name]] * 2)  # Double weight
        
        # Medium-priority risks
        for risk_name in ['age_risk', 'material_moisture_risk', 'material_ph_risk']:
            if risk_name in pole_risks:
                weighted_risks.append(pole_risks[risk_name])
        
        # Add remaining risks with lower weight
        for risk in all_risks:
            if isinstance(risk, (int, float)):
                weighted_risks.append(risk * 0.5)
        
        # Calculate average risk and convert to health score
        if weighted_risks:
            avg_risk = np.mean(weighted_risks)
            health_score = max(0, min(100, (1 - avg_risk) * 100))
        else:
            health_score = 50.0  # Default neutral score
        
        return health_score
    
    def _calculate_soil_stability_score(self, soil_risks: Dict[str, float]) -> float:
        """Calculate soil stability score (0-100, higher is better)."""
        stability_risks = [
            soil_risks.get('moisture_risk', 0.0),
            soil_risks.get('bearing_capacity_risk', 0.0),
            soil_risks.get('compaction_risk', 0.0)
        ]
        # Filter out any non-numeric values
        stability_risks = [r for r in stability_risks if isinstance(r, (int, float))]
        if stability_risks:
            avg_risk = np.mean(stability_risks)
        else:
            avg_risk = 0.0
        return max(0, min(100, (1 - avg_risk) * 100))
    
    def _calculate_structural_risk_score(self, pole_risks: Dict[str, float]) -> float:
        """Calculate structural risk score (0-100, higher is worse)."""
        structural_risks = [
            pole_risks.get('age_risk', 0.0),
            pole_risks.get('material_moisture_risk', 0.0),
            pole_risks.get('material_ph_risk', 0.0)
        ]
        # Filter out any non-numeric values
        structural_risks = [r for r in structural_risks if isinstance(r, (int, float))]
        if structural_risks:
            avg_risk = np.mean(structural_risks)
        else:
            avg_risk = 0.0
        return max(0, min(100, avg_risk * 100))
    
    def _calculate_erosion_risk(self, soil_risks: Dict[str, float], 
                               weather_data: Optional[List[WeatherData]]) -> float:
        """Calculate erosion risk based on soil and weather conditions."""
        base_erosion_risk = soil_risks.get('moisture_risk', 0.0) * 0.5
        
        if weather_data:
            # Factor in precipitation intensity
            recent_weather = sorted(weather_data, key=lambda x: x.date)[-30:]  # Last 30 days
            heavy_rain_days = sum(1 for w in recent_weather 
                                if w.precipitation_intensity == 'heavy')
            
            if heavy_rain_days > 5:
                base_erosion_risk *= 1.5
        
        return min(1.0, base_erosion_risk)
    
    def _calculate_freeze_thaw_risk(self, soil_risks: Dict[str, float], 
                                   weather_data: Optional[List[WeatherData]]) -> float:
        """Calculate freeze-thaw risk."""
        if not weather_data:
            return 0.2  # Default moderate risk
        
        # Count freeze-thaw cycles
        total_cycles = sum(w.freeze_thaw_cycles_count or 0 for w in weather_data if w.freeze_thaw_cycles_count)
        if total_cycles > 50:  # High number of cycles
            return min(1.0, total_cycles / 100)
        
        return min(0.5, total_cycles / 100)
    
    def _determine_maintenance_priority(self, health_score: float, 
                                       soil_risks: Dict[str, float], 
                                       pole_risks: Dict[str, float]) -> str:
        """Determine maintenance priority level."""
        if health_score < 20:
            return 'critical'
        elif health_score < 40:
            return 'high'
        elif health_score < 70:
            return 'medium'
        else:
            return 'low'
    
    def _calculate_confidence_level(self, soil_samples: List[SoilSample], 
                                   pole: PoleInfo) -> float:
        """Calculate confidence level in the assessment."""
        confidence = 0.5  # Base confidence
        
        # More samples = higher confidence
        if len(soil_samples) >= 3:
            confidence += 0.2
        elif len(soil_samples) >= 2:
            confidence += 0.1
        
        # Recent samples = higher confidence
        latest_sample = max(soil_samples, key=lambda x: x.sample_date)
        days_since_sample = (datetime.now() - latest_sample.sample_date).days
        if days_since_sample < 30:
            confidence += 0.2
        elif days_since_sample < 90:
            confidence += 0.1
        
        # Complete pole info = higher confidence
        if all([pole.height_ft, pole.install_date, pole.material]):
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def _calculate_data_completeness(self, sample: SoilSample) -> float:
        """Calculate completeness of available data."""
        required_fields = ['moisture_content', 'ph', 'bulk_density', 'bearing_capacity']
        available_fields = sum(1 for field in required_fields 
                             if getattr(sample, field) is not None)
        return available_fields / len(required_fields)
    
    def _create_default_metrics(self, pole: PoleInfo) -> PoleHealthMetrics:
        """Create default metrics when no soil data is available."""
        return PoleHealthMetrics(
            pole_id=pole.pole_id,
            assessment_date=datetime.now(),
            overall_health_score=50.0,  # Neutral score
            soil_stability_score=50.0,
            structural_risk_score=50.0,
            moisture_risk=0.5,
            erosion_risk=0.5,
            chemical_corrosion_risk=0.5,
            freeze_thaw_risk=0.5,
            bearing_capacity_risk=0.5,
            maintenance_priority='medium',
            confidence_level=0.1,  # Very low confidence without soil data
            data_completeness=0.0
        )
