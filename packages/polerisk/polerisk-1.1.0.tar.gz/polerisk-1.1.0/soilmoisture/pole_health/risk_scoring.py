"""
Risk scoring and maintenance scheduling for utility poles.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
from dataclasses import asdict

from .pole_data import PoleInfo, PoleHealthMetrics, PoleDatabase

logger = logging.getLogger(__name__)


class PoleRiskScorer:
    """Advanced risk scoring system for utility poles."""
    
    def __init__(self):
        self.risk_weights = {
            'safety': 0.4,      # Public safety impact
            'reliability': 0.3,  # Service reliability impact  
            'financial': 0.2,    # Replacement/repair cost
            'environmental': 0.1 # Environmental factors
        }
        
        # Risk multipliers by pole characteristics
        self.location_multipliers = {
            'urban': 1.5,       # Higher consequences of failure
            'suburban': 1.2,
            'rural': 1.0,
            'remote': 0.8
        }
        
        self.circuit_importance = {
            'transmission': 2.0,    # High voltage transmission
            'distribution_main': 1.5, # Main distribution feeders
            'distribution_branch': 1.0, # Branch circuits
            'service': 0.7         # Individual service drops
        }
    
    def calculate_comprehensive_risk_score(self, pole: PoleInfo, 
                                         health_metrics: PoleHealthMetrics,
                                         service_area_data: Optional[Dict] = None) -> Dict[str, float]:
        """
        Calculate comprehensive risk score considering multiple factors.
        
        Args:
            pole: Pole information
            health_metrics: Current health assessment
            service_area_data: Optional data about service area (customers, critical facilities)
            
        Returns:
            Dictionary with detailed risk scores
        """
        scores = {}
        
        # Base technical risk from health assessment
        technical_risk = (100 - health_metrics.overall_health_score) / 100
        
        # Safety risk assessment
        safety_risk = self._calculate_safety_risk(pole, health_metrics, service_area_data)
        scores['safety_risk'] = safety_risk
        
        # Reliability risk assessment
        reliability_risk = self._calculate_reliability_risk(pole, health_metrics, service_area_data)
        scores['reliability_risk'] = reliability_risk
        
        # Financial risk assessment
        financial_risk = self._calculate_financial_risk(pole, health_metrics)
        scores['financial_risk'] = financial_risk
        
        # Environmental risk assessment
        environmental_risk = self._calculate_environmental_risk(pole, health_metrics)
        scores['environmental_risk'] = environmental_risk
        
        # Calculate weighted composite risk score
        composite_risk = (
            safety_risk * self.risk_weights['safety'] +
            reliability_risk * self.risk_weights['reliability'] +
            financial_risk * self.risk_weights['financial'] +  
            environmental_risk * self.risk_weights['environmental']
        )
        
        scores['composite_risk'] = composite_risk
        scores['technical_risk'] = technical_risk
        
        return scores
    
    def _calculate_safety_risk(self, pole: PoleInfo, health_metrics: PoleHealthMetrics,
                              service_area_data: Optional[Dict] = None) -> float:
        """Calculate safety risk score."""
        base_safety_risk = (100 - health_metrics.overall_health_score) / 100
        
        # Adjust for pole height (taller poles = higher risk)
        if pole.height_ft:
            height_factor = min(2.0, pole.height_ft / 40)  # Normalize to 40ft standard
            base_safety_risk *= height_factor
        
        # Adjust for voltage class
        voltage_factor = self.circuit_importance.get(pole.voltage_class, 1.0)
        base_safety_risk *= voltage_factor
        
        # Adjust for population density if available
        if service_area_data and 'population_density' in service_area_data:
            density = service_area_data['population_density']
            if density > 1000:  # Urban
                base_safety_risk *= 1.5
            elif density > 200:  # Suburban
                base_safety_risk *= 1.2
        
        return min(1.0, base_safety_risk)
    
    def _calculate_reliability_risk(self, pole: PoleInfo, health_metrics: PoleHealthMetrics,
                                   service_area_data: Optional[Dict] = None) -> float:
        """Calculate service reliability risk."""
        base_reliability_risk = (100 - health_metrics.overall_health_score) / 100
        
        # Adjust for number of customers affected
        if service_area_data:
            customers = service_area_data.get('customers_served', 100)
            if customers > 1000:
                base_reliability_risk *= 1.8
            elif customers > 500:
                base_reliability_risk *= 1.4
            elif customers > 100:
                base_reliability_risk *= 1.1
        
        # Critical facilities factor
        if service_area_data and service_area_data.get('critical_facilities', 0) > 0:
            base_reliability_risk *= 2.0
        
        return min(1.0, base_reliability_risk)
    
    def _calculate_financial_risk(self, pole: PoleInfo, health_metrics: PoleHealthMetrics) -> float:
        """Calculate financial risk (cost of failure vs. proactive replacement)."""
        # Base cost factors by pole type and size
        base_costs = {
            'wood': 3000,      # Typical wood pole replacement cost
            'concrete': 8000,   # Concrete pole cost
            'steel': 12000,     # Steel pole cost
            'composite': 15000  # Composite pole cost
        }
        
        base_cost = base_costs.get(pole.pole_type.lower(), 5000)
        
        # Adjust for pole height
        if pole.height_ft:
            height_factor = pole.height_ft / 40  # Normalize to 40ft
            base_cost *= height_factor
        
        # Emergency replacement costs are typically 2-3x normal
        emergency_multiplier = 2.5
        
        # Calculate probability of emergency replacement
        failure_probability = (100 - health_metrics.overall_health_score) / 100
        
        # Expected cost of emergency replacement
        emergency_cost = base_cost * emergency_multiplier * failure_probability
        
        # Financial risk is ratio of emergency cost to proactive replacement cost
        financial_risk = emergency_cost / base_cost
        
        return min(1.0, financial_risk)
    
    def _calculate_environmental_risk(self, pole: PoleInfo, health_metrics: PoleHealthMetrics) -> float:
        """Calculate environmental risk from pole failure."""
        base_environmental_risk = health_metrics.erosion_risk * 0.5
        
        # Wood poles with chemical treatment have higher environmental risk
        if pole.pole_type.lower() == 'wood' and pole.treatment_type:
            if 'CCA' in pole.treatment_type or 'pentachlorophenol' in pole.treatment_type:
                base_environmental_risk *= 1.5
        
        return min(1.0, base_environmental_risk)


class MaintenanceScheduler:
    """Intelligent maintenance scheduling based on risk assessment."""
    
    def __init__(self):
        self.inspection_intervals = {
            'critical': 30,     # days
            'high': 90,         # days
            'medium': 180,      # days
            'low': 365          # days
        }
        
        self.maintenance_windows = {
            'emergency': 7,      # days - must be addressed immediately
            'urgent': 30,        # days - address within a month
            'planned': 90,       # days - plan for next quarter
            'routine': 365       # days - annual maintenance cycle
        }
    
    def create_maintenance_schedule(self, poles_data: List[Tuple[PoleInfo, PoleHealthMetrics]], 
                                   current_date: Optional[datetime] = None) -> pd.DataFrame:
        """
        Create optimized maintenance schedule for a fleet of poles.
        
        Args:
            poles_data: List of (PoleInfo, PoleHealthMetrics) tuples
            current_date: Current date for scheduling (defaults to now)
            
        Returns:
            DataFrame with maintenance schedule
        """
        if current_date is None:
            current_date = datetime.now()
        
        schedule_data = []
        
        for pole, metrics in poles_data:
            # Determine maintenance window
            maintenance_window = self._determine_maintenance_window(metrics)
            
            # Calculate recommended action date
            if maintenance_window == 'emergency':
                action_date = current_date + timedelta(days=7)
            elif maintenance_window == 'urgent':
                action_date = current_date + timedelta(days=30)
            elif maintenance_window == 'planned':
                action_date = current_date + timedelta(days=90)
            else:
                action_date = current_date + timedelta(days=365)
            
            # Determine recommended actions
            recommended_actions = self._determine_recommended_actions(pole, metrics)
            
            # Estimate costs
            estimated_cost = self._estimate_maintenance_cost(pole, recommended_actions)
            
            schedule_data.append({
                'pole_id': pole.pole_id,
                'latitude': pole.latitude,
                'longitude': pole.longitude,
                'pole_type': pole.pole_type,
                'age_years': pole.age_years or 0,
                'health_score': metrics.overall_health_score,
                'maintenance_priority': metrics.maintenance_priority,
                'maintenance_window': maintenance_window,
                'recommended_action_date': action_date,
                'days_until_action': (action_date - current_date).days,
                'recommended_actions': '; '.join(recommended_actions),
                'estimated_cost': estimated_cost,
                'confidence_level': metrics.confidence_level,
                'requires_immediate_attention': metrics.requires_immediate_attention,
                'soil_stability_score': metrics.soil_stability_score,
                'structural_risk_score': metrics.structural_risk_score
            })
        
        df = pd.DataFrame(schedule_data)
        
        # Sort by priority and urgency
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        df['priority_rank'] = df['maintenance_priority'].map(priority_order)
        df = df.sort_values(['priority_rank', 'days_until_action', 'health_score'])
        
        return df.drop('priority_rank', axis=1)
    
    def _determine_maintenance_window(self, metrics: PoleHealthMetrics) -> str:
        """Determine appropriate maintenance window based on health metrics."""
        if metrics.requires_immediate_attention or metrics.overall_health_score < 20:
            return 'emergency'
        elif metrics.maintenance_priority == 'high' or metrics.overall_health_score < 40:
            return 'urgent'
        elif metrics.maintenance_priority == 'medium' or metrics.overall_health_score < 70:
            return 'planned'
        else:
            return 'routine'
    
    def _determine_recommended_actions(self, pole: PoleInfo, metrics: PoleHealthMetrics) -> List[str]:
        """Determine specific maintenance actions needed."""
        actions = []
        
        # Based on health score
        if metrics.overall_health_score < 30:
            actions.append('Pole replacement recommended')
        elif metrics.overall_health_score < 50:
            actions.append('Detailed structural inspection')
        
        # Based on specific risk factors
        if metrics.moisture_risk > 0.7:
            actions.append('Soil drainage assessment')
            actions.append('Erosion control measures')
        
        if metrics.chemical_corrosion_risk > 0.6:
            actions.append('Corrosion protection assessment')
        
        if metrics.bearing_capacity_risk > 0.6:
            actions.append('Foundation reinforcement evaluation')
        
        if metrics.freeze_thaw_risk > 0.7:
            actions.append('Freeze-thaw damage inspection')
        
        # Age-based actions
        if pole.age_years and pole.age_years > 20:
            if pole.pole_type.lower() == 'wood':
                actions.append('Wood preservation treatment')
        
        # Default inspection if no specific actions
        if not actions:
            actions.append('Routine visual inspection')
        
        return actions
    
    def _estimate_maintenance_cost(self, pole: PoleInfo, actions: List[str]) -> float:
        """Estimate cost for recommended maintenance actions."""
        cost_estimates = {
            'Routine visual inspection': 150,
            'Detailed structural inspection': 500,
            'Soil drainage assessment': 800,
            'Erosion control measures': 1200,
            'Corrosion protection assessment': 600,
            'Foundation reinforcement evaluation': 1500,
            'Freeze-thaw damage inspection': 400,
            'Wood preservation treatment': 800,
            'Pole replacement recommended': 5000  # Base replacement cost
        }
        
        total_cost = 0
        for action in actions:
            # Find matching cost estimate
            for cost_key, cost in cost_estimates.items():
                if cost_key in action:
                    total_cost += cost
                    break
            else:
                # Default cost for unknown actions
                total_cost += 300
        
        # Adjust for pole type and size
        if pole.pole_type.lower() == 'concrete':
            total_cost *= 1.3
        elif pole.pole_type.lower() == 'steel':
            total_cost *= 1.5
        elif pole.pole_type.lower() == 'composite':
            total_cost *= 1.8
        
        # Adjust for pole height
        if pole.height_ft and pole.height_ft > 40:
            total_cost *= (pole.height_ft / 40)
        
        return round(total_cost, 2)
    
    def generate_maintenance_report(self, schedule_df: pd.DataFrame, 
                                   budget_limit: Optional[float] = None) -> Dict:
        """Generate comprehensive maintenance report with budget analysis."""
        report = {}
        
        # Summary statistics
        total_poles = len(schedule_df)
        urgent_poles = len(schedule_df[schedule_df['maintenance_window'].isin(['emergency', 'urgent'])])
        total_estimated_cost = schedule_df['estimated_cost'].sum()
        
        report['summary'] = {
            'total_poles': total_poles,
            'urgent_poles': urgent_poles,
            'total_estimated_cost': total_estimated_cost,
            'average_cost_per_pole': total_estimated_cost / total_poles if total_poles > 0 else 0,
            'urgent_percentage': (urgent_poles / total_poles * 100) if total_poles > 0 else 0
        }
        
        # Priority breakdown
        priority_counts = schedule_df['maintenance_priority'].value_counts().to_dict()
        priority_costs = schedule_df.groupby('maintenance_priority')['estimated_cost'].sum().to_dict()
        
        report['by_priority'] = {
            'counts': priority_counts,
            'costs': priority_costs
        }
        
        # Budget analysis
        if budget_limit:
            budget_analysis = self._analyze_budget_constraints(schedule_df, budget_limit)
            report['budget_analysis'] = budget_analysis
        
        # Timeline analysis
        timeline_analysis = self._analyze_maintenance_timeline(schedule_df)
        report['timeline_analysis'] = timeline_analysis
        
        return report
    
    def _analyze_budget_constraints(self, schedule_df: pd.DataFrame, budget_limit: float) -> Dict:
        """Analyze what can be accomplished within budget constraints."""
        # Sort by priority and cost-effectiveness
        sorted_df = schedule_df.sort_values(['maintenance_priority', 'estimated_cost'])
        
        cumulative_cost = 0
        affordable_poles = []
        
        for _, row in sorted_df.iterrows():
            if cumulative_cost + row['estimated_cost'] <= budget_limit:
                cumulative_cost += row['estimated_cost']
                affordable_poles.append(row['pole_id'])
            else:
                break
        
        return {
            'poles_within_budget': len(affordable_poles),
            'cost_within_budget': cumulative_cost,
            'budget_utilization': (cumulative_cost / budget_limit * 100) if budget_limit > 0 else 0,
            'poles_deferred': len(schedule_df) - len(affordable_poles),
            'cost_deferred': schedule_df['estimated_cost'].sum() - cumulative_cost
        }
    
    def _analyze_maintenance_timeline(self, schedule_df: pd.DataFrame) -> Dict:
        """Analyze maintenance timeline and resource requirements."""
        # Group by maintenance window
        timeline_groups = schedule_df.groupby('maintenance_window').agg({
            'pole_id': 'count',
            'estimated_cost': 'sum',
            'days_until_action': 'mean'
        }).rename(columns={'pole_id': 'pole_count'})
        
        return timeline_groups.to_dict('index')
