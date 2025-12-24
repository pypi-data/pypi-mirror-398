"""
Structural inspection assessment module for physical pole condition evaluation.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
from dataclasses import asdict

from .enhanced_models import StructuralInspection, InspectionType, PoleCondition, LoadAnalysis
from .pole_data import PoleInfo, PoleHealthMetrics

logger = logging.getLogger(__name__)


class StructuralConditionAnalyzer:
    """Analyzes physical structural condition of utility poles."""
    
    def __init__(self):
        # Condition thresholds for different materials
        self.wood_thresholds = {
            'decay_depth_critical': 2.0,  # inches
            'decay_depth_poor': 1.5,
            'decay_depth_fair': 1.0,
            'circumferential_loss_critical': 50,  # percentage
            'circumferential_loss_poor': 30,
            'circumferential_loss_fair': 15
        }
        
        self.concrete_thresholds = {
            'crack_width_critical': 0.02,  # inches
            'spalling_area_critical': 25,  # percentage of surface
            'carbonation_depth_critical': 2.0  # inches
        }
        
        self.steel_thresholds = {
            'corrosion_level_critical': 4,  # 1-5 scale
            'corrosion_level_poor': 3,
            'section_loss_critical': 10,  # percentage
            'coating_life_remaining': 5  # years
        }
        
        # Structural limits
        self.structural_limits = {
            'lean_angle_critical': 5.0,  # degrees
            'lean_angle_poor': 3.0,
            'twist_angle_critical': 3.0,  # degrees
            'strength_loss_critical': 40,  # percentage
            'strength_loss_poor': 25
        }
    
    def assess_wood_condition(self, inspection: StructuralInspection) -> Dict[str, float]:
        """Assess wood pole structural condition."""
        risks = {}
        
        # Decay assessment
        if inspection.wood_decay_depth is not None:
            decay_risk = 0.0
            if inspection.wood_decay_depth >= self.wood_thresholds['decay_depth_critical']:
                decay_risk = 1.0
            elif inspection.wood_decay_depth >= self.wood_thresholds['decay_depth_poor']:
                decay_risk = 0.8
            elif inspection.wood_decay_depth >= self.wood_thresholds['decay_depth_fair']:
                decay_risk = 0.5
            else:
                decay_risk = inspection.wood_decay_depth / self.wood_thresholds['decay_depth_fair'] * 0.3
            
            risks['wood_decay_risk'] = min(1.0, decay_risk)
        
        # Circumferential loss assessment
        if inspection.wood_circumferential_loss is not None:
            circ_risk = 0.0
            loss = inspection.wood_circumferential_loss
            
            if loss >= self.wood_thresholds['circumferential_loss_critical']:
                circ_risk = 1.0
            elif loss >= self.wood_thresholds['circumferential_loss_poor']:
                circ_risk = 0.8
            elif loss >= self.wood_thresholds['circumferential_loss_fair']:
                circ_risk = 0.5
            else:
                circ_risk = loss / self.wood_thresholds['circumferential_loss_fair'] * 0.3
            
            risks['circumferential_loss_risk'] = min(1.0, circ_risk)
        
        return risks
    
    def assess_concrete_condition(self, inspection: StructuralInspection) -> Dict[str, float]:
        """Assess concrete pole structural condition."""
        risks = {}
        
        # Cracking assessment
        if inspection.concrete_cracking is not None:
            risks['concrete_cracking_risk'] = 0.6 if inspection.concrete_cracking else 0.0
        
        # Spalling assessment
        if inspection.concrete_spalling is not None:
            risks['concrete_spalling_risk'] = 0.7 if inspection.concrete_spalling else 0.0
        
        return risks
    
    def assess_steel_condition(self, inspection: StructuralInspection) -> Dict[str, float]:
        """Assess steel pole structural condition."""
        risks = {}
        
        # Corrosion level assessment
        if inspection.steel_corrosion_level is not None:
            corr_level = inspection.steel_corrosion_level
            
            if corr_level >= self.steel_thresholds['corrosion_level_critical']:
                corr_risk = 1.0
            elif corr_level >= self.steel_thresholds['corrosion_level_poor']:
                corr_risk = 0.7
            else:
                corr_risk = corr_level / self.steel_thresholds['corrosion_level_poor'] * 0.5
            
            risks['steel_corrosion_risk'] = min(1.0, corr_risk)
        
        # Coating condition assessment
        if inspection.coating_condition is not None:
            coating_risk = 0.0
            condition = inspection.coating_condition.lower()
            
            if condition in ['failed', 'poor']:
                coating_risk = 0.8
            elif condition in ['fair', 'weathered']:
                coating_risk = 0.4
            elif condition in ['good']:
                coating_risk = 0.1
            
            risks['coating_degradation_risk'] = coating_risk
        
        return risks
    
    def assess_structural_geometry(self, inspection: StructuralInspection) -> Dict[str, float]:
        """Assess pole geometry and alignment."""
        risks = {}
        
        # Lean angle assessment
        if inspection.lean_angle is not None:
            lean = abs(inspection.lean_angle)
            
            if lean >= self.structural_limits['lean_angle_critical']:
                lean_risk = 1.0
            elif lean >= self.structural_limits['lean_angle_poor']:
                lean_risk = 0.8
            else:
                lean_risk = lean / self.structural_limits['lean_angle_poor'] * 0.6
            
            risks['lean_risk'] = min(1.0, lean_risk)
        
        # Twist angle assessment
        if inspection.twist_angle is not None:
            twist = abs(inspection.twist_angle)
            
            if twist >= self.structural_limits['twist_angle_critical']:
                twist_risk = 1.0
            else:
                twist_risk = twist / self.structural_limits['twist_angle_critical'] * 0.8
            
            risks['twist_risk'] = min(1.0, twist_risk)
        
        return risks
    
    def assess_remaining_strength(self, inspection: StructuralInspection) -> Dict[str, float]:
        """Assess remaining structural strength."""
        risks = {}
        
        if inspection.estimated_remaining_strength is not None:
            strength_remaining = inspection.estimated_remaining_strength
            strength_loss = 100 - strength_remaining
            
            if strength_loss >= self.structural_limits['strength_loss_critical']:
                strength_risk = 1.0
            elif strength_loss >= self.structural_limits['strength_loss_poor']:
                strength_risk = 0.8
            else:
                strength_risk = strength_loss / self.structural_limits['strength_loss_poor'] * 0.6
            
            risks['strength_degradation_risk'] = min(1.0, strength_risk)
        
        return risks
    
    def calculate_overall_condition_score(self, inspection: StructuralInspection, 
                                        pole_type: str) -> float:
        """Calculate overall structural condition score (0-100, higher is better)."""
        all_risks = []
        
        # Material-specific assessments
        if pole_type.lower() == 'wood':
            wood_risks = self.assess_wood_condition(inspection)
            all_risks.extend(wood_risks.values())
        elif pole_type.lower() == 'concrete':
            concrete_risks = self.assess_concrete_condition(inspection)
            all_risks.extend(concrete_risks.values())
        elif pole_type.lower() == 'steel':
            steel_risks = self.assess_steel_condition(inspection)
            all_risks.extend(steel_risks.values())
        
        # Geometry and strength assessments (apply to all types)
        geometry_risks = self.assess_structural_geometry(inspection)
        strength_risks = self.assess_remaining_strength(inspection)
        
        all_risks.extend(geometry_risks.values())
        all_risks.extend(strength_risks.values())
        
        # Overall condition from inspector assessment
        if inspection.overall_condition:
            condition_map = {
                PoleCondition.EXCELLENT: 0.0,
                PoleCondition.GOOD: 0.2,
                PoleCondition.FAIR: 0.5,
                PoleCondition.POOR: 0.8,
                PoleCondition.CRITICAL: 1.0
            }
            inspector_risk = condition_map.get(inspection.overall_condition, 0.5)
            all_risks.append(inspector_risk)
        
        if not all_risks:
            return 50.0  # Neutral score if no data
        
        # Calculate weighted average risk
        avg_risk = np.mean(all_risks)
        condition_score = max(0, min(100, (1 - avg_risk) * 100))
        
        return condition_score
    
    def determine_inspection_frequency(self, condition_score: float, 
                                     pole_age: float, pole_type: str) -> int:
        """Determine recommended inspection frequency in months."""
        
        # Base frequencies by pole type (months)
        base_frequencies = {
            'wood': 60,      # 5 years
            'concrete': 72,  # 6 years  
            'steel': 60,     # 5 years
            'composite': 84  # 7 years
        }
        
        base_freq = base_frequencies.get(pole_type.lower(), 60)
        
        # Adjust based on condition
        if condition_score < 30:
            frequency = 6   # Every 6 months for critical condition
        elif condition_score < 50:
            frequency = 12  # Annual for poor condition
        elif condition_score < 70:
            frequency = 24  # Every 2 years for fair condition
        else:
            frequency = base_freq  # Standard frequency for good condition
        
        # Adjust for age (older poles need more frequent inspection)
        if pole_age > 30:
            frequency = int(frequency * 0.75)  # 25% more frequent
        elif pole_age > 20:
            frequency = int(frequency * 0.9)   # 10% more frequent
        
        return max(6, frequency)  # Minimum 6 months
    
    def generate_recommendations(self, inspection: StructuralInspection, 
                               condition_score: float, pole_type: str) -> List[str]:
        """Generate specific maintenance recommendations."""
        recommendations = []
        
        # Critical conditions requiring immediate action
        if condition_score < 30:
            recommendations.append("URGENT: Pole replacement recommended within 30 days")
            recommendations.append("Install temporary support if needed")
            recommendations.append("Restrict climbing until replacement")
        
        # Material-specific recommendations
        if pole_type.lower() == 'wood':
            if (inspection.wood_decay_depth is not None and 
                inspection.wood_decay_depth > self.wood_thresholds['decay_depth_fair']):
                recommendations.append("Consider wood preservation treatment")
                recommendations.append("Monitor decay progression quarterly")
            
            if (inspection.wood_circumferential_loss is not None and
                inspection.wood_circumferential_loss > self.wood_thresholds['circumferential_loss_fair']):
                recommendations.append("Evaluate for steel band reinforcement")
        
        elif pole_type.lower() == 'steel':
            if (inspection.steel_corrosion_level is not None and
                inspection.steel_corrosion_level >= self.steel_thresholds['corrosion_level_poor']):
                recommendations.append("Apply corrosion protection treatment")
                recommendations.append("Inspect coating system integrity")
            
            if inspection.coating_condition and 'poor' in inspection.coating_condition.lower():
                recommendations.append("Schedule coating renewal")
        
        elif pole_type.lower() == 'concrete':
            if inspection.concrete_cracking:
                recommendations.append("Seal cracks to prevent water infiltration")
                recommendations.append("Monitor crack progression")
            
            if inspection.concrete_spalling:
                recommendations.append("Repair spalled areas")
                recommendations.append("Evaluate reinforcement corrosion")
        
        # Geometry issues
        if (inspection.lean_angle is not None and 
            abs(inspection.lean_angle) > self.structural_limits['lean_angle_poor']):
            recommendations.append("Evaluate foundation stability")
            recommendations.append("Consider guy wire installation")
        
        # General recommendations based on condition
        if 30 <= condition_score < 50:
            recommendations.append("Increase inspection frequency to annual")
            recommendations.append("Document condition changes with photos")
        elif 50 <= condition_score < 70:
            recommendations.append("Schedule detailed inspection within 6 months")
            recommendations.append("Monitor for condition changes")
        
        if not recommendations:
            recommendations.append("Continue routine maintenance schedule")
            recommendations.append("Next standard inspection as scheduled")
        
        return recommendations


class EnhancedPoleHealthAssessment:
    """Enhanced pole health assessment including structural inspection data."""
    
    def __init__(self):
        from .assessment import PoleHealthAssessment  # Import existing assessor
        self.soil_assessor = PoleHealthAssessment()
        self.structural_analyzer = StructuralConditionAnalyzer()
    
    def assess_pole_with_structural_data(self, pole: PoleInfo, 
                                       soil_samples: List,
                                       structural_inspections: List[StructuralInspection] = None,
                                       load_analysis: LoadAnalysis = None) -> PoleHealthMetrics:
        """
        Comprehensive pole assessment including structural inspection data.
        
        Args:
            pole: Pole information
            soil_samples: Soil condition samples
            structural_inspections: Physical inspection data
            load_analysis: Engineering load analysis
            
        Returns:
            Enhanced PoleHealthMetrics with structural assessment
        """
        # Get base soil assessment
        base_metrics = self.soil_assessor.assess_pole_health(pole, soil_samples)
        
        # Add structural assessment if available
        if structural_inspections:
            latest_inspection = max(structural_inspections, 
                                  key=lambda x: x.inspection_date)
            
            # Calculate structural condition score
            structural_score = self.structural_analyzer.calculate_overall_condition_score(
                latest_inspection, pole.pole_type
            )
            
            # Update structural risk score (invert score to get risk)
            base_metrics.structural_risk_score = max(0, 100 - structural_score)
            
            # Generate structural recommendations
            structural_recommendations = self.structural_analyzer.generate_recommendations(
                latest_inspection, structural_score, pole.pole_type
            )
            
            # Determine inspection frequency
            inspection_frequency = self.structural_analyzer.determine_inspection_frequency(
                structural_score, pole.age_years or 0, pole.pole_type
            )
            base_metrics.recommended_inspection_interval = inspection_frequency
            
            # Adjust overall health score to include structural condition
            structural_weight = 0.4  # 40% weight for structural condition
            soil_weight = 0.6       # 60% weight for soil condition
            
            base_metrics.overall_health_score = (
                structural_score * structural_weight +
                base_metrics.overall_health_score * soil_weight
            )
            
            # Update maintenance priority based on structural condition
            if structural_score < 30:
                base_metrics.maintenance_priority = 'critical'
                base_metrics.requires_immediate_attention = True
            elif structural_score < 50 and base_metrics.maintenance_priority in ['low', 'medium']:
                base_metrics.maintenance_priority = 'high'
        
        # Add load analysis assessment if available
        if load_analysis:
            if load_analysis.safety_factor is not None:
                if load_analysis.safety_factor < 1.5:
                    base_metrics.maintenance_priority = 'critical'
                    base_metrics.requires_immediate_attention = True
                elif load_analysis.safety_factor < 2.0:
                    if base_metrics.maintenance_priority in ['low', 'medium']:
                        base_metrics.maintenance_priority = 'high'
        
        return base_metrics
