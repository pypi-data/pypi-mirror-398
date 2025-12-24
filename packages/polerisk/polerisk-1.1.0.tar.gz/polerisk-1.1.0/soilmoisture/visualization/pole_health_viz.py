"""
Visualization tools for utility pole health assessment and maintenance planning.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import signalplot
from typing import Dict, List, Optional, Tuple
import folium
from folium import plugins
import warnings
import logging

warnings.filterwarnings('ignore')

# Apply SignalPlot minimalist defaults
signalplot.apply()

logger = logging.getLogger(__name__)


class PoleHealthVisualizer:
    """Comprehensive visualization suite for utility pole health assessment."""
    
    def __init__(self, figsize: Tuple[int, int] = (12, 8)):
        self.figsize = figsize
        self.colors = {
            'critical': '#d32f2f',
            'high': '#f57c00', 
            'medium': '#fbc02d',
            'low': '#388e3c',
            'excellent': '#1976d2'
        }
        
    def create_health_overview_dashboard(self, assessment_df: pd.DataFrame, 
                                       schedule_df: pd.DataFrame,
                                       output_dir: str = 'Analysis') -> str:
        """Create comprehensive health overview dashboard."""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        # Create figure with subplots
        fig = plt.figure(figsize=(20, 16))
        
        # 1. Health Score Distribution
        ax1 = plt.subplot(3, 4, 1)
        self._plot_health_distribution(assessment_df, ax1)
        
        # 2. Priority Breakdown Pie Chart
        ax2 = plt.subplot(3, 4, 2)
        self._plot_priority_breakdown(assessment_df, ax2)
        
        # 3. Risk Factors Heatmap
        ax3 = plt.subplot(3, 4, 3)
        self._plot_risk_heatmap(assessment_df, ax3)
        
        # 4. Age vs Health Scatter
        ax4 = plt.subplot(3, 4, 4)
        self._plot_age_health_scatter(assessment_df, ax4)
        
        # 5. Pole Type Analysis
        ax5 = plt.subplot(3, 4, 5)
        self._plot_pole_type_analysis(assessment_df, ax5)
        
        # 6. Maintenance Cost Analysis  
        ax6 = plt.subplot(3, 4, 6)
        self._plot_cost_analysis(schedule_df, ax6)
        
        # 7. Risk Score Distribution
        ax7 = plt.subplot(3, 4, 7)
        self._plot_risk_distribution(assessment_df, ax7)
        
        # 8. Maintenance Timeline
        ax8 = plt.subplot(3, 4, 8)
        self._plot_maintenance_timeline(schedule_df, ax8)
        
        # 9. Health Score vs Risk Factors
        ax9 = plt.subplot(3, 4, (9, 10))
        self._plot_health_vs_risks(assessment_df, ax9)
        
        # 10. Geographic Risk Distribution (if lat/lon available)
        ax10 = plt.subplot(3, 4, (11, 12))
        if 'latitude' in assessment_df.columns and 'longitude' in assessment_df.columns:
            self._plot_geographic_scatter(assessment_df, ax10)
        else:
            ax10.text(0.5, 0.5, 'Geographic data\nnot available', 
                     ha='center', va='center', transform=ax10.transAxes)
            ax10.set_title('Geographic Distribution')
        
        plt.tight_layout()
        plt.suptitle('Utility Pole Health Assessment Dashboard', 
                    fontsize=20, fontweight='bold', y=0.98)
        
        # Save dashboard
        dashboard_file = os.path.join(output_dir, 'pole_health_dashboard.png')
        plt.savefig(dashboard_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        return dashboard_file
    
    def _plot_health_distribution(self, df: pd.DataFrame, ax):
        """Plot health score distribution histogram."""
        if 'overall_health_score' in df.columns:
            scores = df['overall_health_score'].dropna()
            ax.hist(scores, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
            ax.axvline(scores.mean(), color='red', linestyle='--', 
                      label=f'Mean: {scores.mean():.1f}')
            ax.set_xlabel('Health Score')
            ax.set_ylabel('Number of Poles')
            ax.set_title('Health Score Distribution')
            ax.legend()
        else:
            ax.text(0.5, 0.5, 'Health score\ndata not available', 
                   ha='center', va='center', transform=ax.transAxes)
    
    def _plot_priority_breakdown(self, df: pd.DataFrame, ax):
        """Plot maintenance priority breakdown."""
        if 'maintenance_priority' in df.columns:
            priority_counts = df['maintenance_priority'].value_counts()
            colors = [self.colors.get(p, 'gray') for p in priority_counts.index]
            ax.pie(priority_counts.values, labels=priority_counts.index, 
                  autopct='%1.1f%%', colors=colors, startangle=90)
            ax.set_title('Maintenance Priority\nBreakdown')
        else:
            ax.text(0.5, 0.5, 'Priority data\nnot available', 
                   ha='center', va='center', transform=ax.transAxes)
    
    def _plot_risk_heatmap(self, df: pd.DataFrame, ax):
        """Plot risk factors heatmap."""
        risk_columns = ['moisture_risk', 'erosion_risk', 'chemical_corrosion_risk', 
                       'bearing_capacity_risk']
        available_risks = [col for col in risk_columns if col in df.columns]
        
        if available_risks:
            risk_data = df[available_risks].fillna(0)
            # Calculate correlation matrix
            corr_matrix = risk_data.corr()
            
            im = ax.imshow(corr_matrix, cmap='RdYlBu_r', aspect='auto', vmin=-1, vmax=1)
            ax.set_xticks(range(len(corr_matrix.columns)))
            ax.set_yticks(range(len(corr_matrix.columns)))
            ax.set_xticklabels([col.replace('_risk', '').replace('_', ' ').title() 
                               for col in corr_matrix.columns], rotation=45)
            ax.set_yticklabels([col.replace('_risk', '').replace('_', ' ').title() 
                               for col in corr_matrix.columns])
            ax.set_title('Risk Factor\nCorrelations')
            
            # Add correlation values
            for i in range(len(corr_matrix)):
                for j in range(len(corr_matrix.columns)):
                    ax.text(j, i, f'{corr_matrix.iloc[i, j]:.2f}', 
                           ha='center', va='center', color='white', fontweight='bold')
        else:
            ax.text(0.5, 0.5, 'Risk factor data\nnot available', 
                   ha='center', va='center', transform=ax.transAxes)
    
    def _plot_age_health_scatter(self, df: pd.DataFrame, ax):
        """Plot age vs health score scatter plot."""
        if 'age_years' in df.columns and 'overall_health_score' in df.columns:
            # Color by priority
            if 'maintenance_priority' in df.columns:
                priority_colors = df['maintenance_priority'].map(self.colors)
                scatter = ax.scatter(df['age_years'], df['overall_health_score'], 
                                   c=priority_colors, alpha=0.7, s=60)
            else:
                ax.scatter(df['age_years'], df['overall_health_score'], 
                          alpha=0.7, s=60, color='blue')
            
            ax.set_xlabel('Pole Age (years)')
            ax.set_ylabel('Health Score')
            ax.set_title('Age vs Health Score')
            
            # Add trend line
            if len(df.dropna(subset=['age_years', 'overall_health_score'])) > 1:
                z = np.polyfit(df['age_years'].dropna(), 
                              df['overall_health_score'].dropna(), 1)
                p = np.poly1d(z)
                ax.plot(df['age_years'], p(df['age_years']), "r--", alpha=0.8)
        else:
            ax.text(0.5, 0.5, 'Age/Health data\nnot available', 
                   ha='center', va='center', transform=ax.transAxes)
    
    def _plot_pole_type_analysis(self, df: pd.DataFrame, ax):
        """Plot pole type health analysis."""
        if 'pole_type' in df.columns and 'overall_health_score' in df.columns:
            pole_health = df.groupby('pole_type')['overall_health_score'].agg(['mean', 'std']).reset_index()
            
            bars = ax.bar(pole_health['pole_type'], pole_health['mean'], 
                         yerr=pole_health['std'], capsize=5, alpha=0.7)
            ax.set_xlabel('Pole Type')
            ax.set_ylabel('Average Health Score')
            ax.set_title('Health by Pole Type')
            ax.tick_params(axis='x', rotation=45)
            
            # Color bars by health level
            for i, bar in enumerate(bars):
                health = pole_health.iloc[i]['mean']
                if health < 30:
                    bar.set_color(self.colors['critical'])
                elif health < 50:
                    bar.set_color(self.colors['high'])
                elif health < 70:
                    bar.set_color(self.colors['medium'])
                else:
                    bar.set_color(self.colors['low'])
        else:
            ax.text(0.5, 0.5, 'Pole type data\nnot available', 
                   ha='center', va='center', transform=ax.transAxes)
    
    def _plot_cost_analysis(self, df: pd.DataFrame, ax):
        """Plot maintenance cost analysis."""
        if 'estimated_cost' in df.columns and 'maintenance_priority' in df.columns:
            cost_by_priority = df.groupby('maintenance_priority')['estimated_cost'].sum()
            
            bars = ax.bar(cost_by_priority.index, cost_by_priority.values)
            ax.set_xlabel('Priority Level')
            ax.set_ylabel('Total Estimated Cost ($)')
            ax.set_title('Cost by Priority')
            ax.tick_params(axis='x', rotation=45)
            
            # Color bars by priority
            for i, bar in enumerate(bars):
                priority = cost_by_priority.index[i]
                bar.set_color(self.colors.get(priority, 'gray'))
        else:
            ax.text(0.5, 0.5, 'Cost data\nnot available', 
                   ha='center', va='center', transform=ax.transAxes)
    
    def _plot_risk_distribution(self, df: pd.DataFrame, ax):
        """Plot composite risk score distribution."""
        if 'composite_risk' in df.columns:
            risk_scores = df['composite_risk'].dropna()
            ax.hist(risk_scores, bins=15, alpha=0.7, color='orange', edgecolor='black')
            ax.axvline(risk_scores.mean(), color='red', linestyle='--', 
                      label=f'Mean: {risk_scores.mean():.3f}')
            ax.set_xlabel('Composite Risk Score')
            ax.set_ylabel('Number of Poles')
            ax.set_title('Risk Score Distribution')
            ax.legend()
        else:
            ax.text(0.5, 0.5, 'Risk score data\nnot available', 
                   ha='center', va='center', transform=ax.transAxes)
    
    def _plot_maintenance_timeline(self, df: pd.DataFrame, ax):
        """Plot maintenance timeline."""
        if 'days_until_action' in df.columns and 'maintenance_priority' in df.columns:
            priority_order = ['critical', 'high', 'medium', 'low']
            timeline_data = []
            
            for priority in priority_order:
                if priority in df['maintenance_priority'].values:
                    days = df[df['maintenance_priority'] == priority]['days_until_action']
                    timeline_data.append(days.tolist())
                else:
                    timeline_data.append([])
            
            # Create box plot
            bp = ax.boxplot(timeline_data, labels=priority_order, patch_artist=True)
            
            # Color boxes by priority
            for patch, priority in zip(bp['boxes'], priority_order):
                patch.set_facecolor(self.colors.get(priority, 'gray'))
                patch.set_alpha(0.7)
            
            ax.set_xlabel('Priority Level')
            ax.set_ylabel('Days Until Action')
            ax.set_title('Maintenance Timeline\nby Priority')
        else:
            ax.text(0.5, 0.5, 'Timeline data\nnot available', 
                   ha='center', va='center', transform=ax.transAxes)
    
    def _plot_health_vs_risks(self, df: pd.DataFrame, ax):
        """Plot health score vs individual risk factors."""
        risk_columns = ['moisture_risk', 'erosion_risk', 'chemical_corrosion_risk', 
                       'bearing_capacity_risk']
        available_risks = [col for col in risk_columns if col in df.columns]
        
        if available_risks and 'overall_health_score' in df.columns:
            for i, risk_col in enumerate(available_risks):
                risk_data = df[risk_col].dropna()
                health_data = df.loc[risk_data.index, 'overall_health_score']
                
                ax.scatter(risk_data, health_data, alpha=0.6, 
                          label=risk_col.replace('_risk', '').replace('_', ' ').title(),
                          s=40)
            
            ax.set_xlabel('Risk Score (0-1)')
            ax.set_ylabel('Health Score (0-100)')
            ax.set_title('Health Score vs Risk Factors')
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            ax.grid(True, alpha=0.3)
        else:
            ax.text(0.5, 0.5, 'Health/Risk data\nnot available', 
                   ha='center', va='center', transform=ax.transAxes)
    
    def _plot_geographic_scatter(self, df: pd.DataFrame, ax):
        """Plot geographic distribution of poles."""
        if 'latitude' in df.columns and 'longitude' in df.columns:
            # Color by health score
            if 'overall_health_score' in df.columns:
                scatter = ax.scatter(df['longitude'], df['latitude'], 
                                   c=df['overall_health_score'], 
                                   cmap='RdYlGn', alpha=0.7, s=60)
                plt.colorbar(scatter, ax=ax, label='Health Score')
            else:
                ax.scatter(df['longitude'], df['latitude'], alpha=0.7, s=60)
            
            ax.set_xlabel('Longitude')
            ax.set_ylabel('Latitude')
            ax.set_title('Geographic Distribution\n(colored by health)')
            ax.grid(True, alpha=0.3)
        else:
            ax.text(0.5, 0.5, 'Geographic data\nnot available', 
                   ha='center', va='center', transform=ax.transAxes)
    
    def create_interactive_map(self, assessment_df: pd.DataFrame, 
                              output_dir: str = 'Analysis') -> str:
        """Create interactive map of pole locations with health indicators."""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        if 'latitude' not in assessment_df.columns or 'longitude' not in assessment_df.columns:
            logger.debug("Geographic coordinates not available for mapping")
            return None
        
        # Calculate map center
        center_lat = assessment_df['latitude'].mean()
        center_lon = assessment_df['longitude'].mean()
        
        # Create base map
        m = folium.Map(location=[center_lat, center_lon], zoom_start=10)
        
        # Add markers for each pole
        for idx, row in assessment_df.iterrows():
            # Determine marker color based on priority
            priority = row.get('maintenance_priority', 'unknown')
            color = {
                'critical': 'red',
                'high': 'orange', 
                'medium': 'yellow',
                'low': 'green',
                'unknown': 'gray'
            }.get(priority, 'gray')
            
            # Create popup content
            popup_content = f"""
            <b>Pole ID:</b> {row.get('pole_id', 'Unknown')}<br>
            <b>Health Score:</b> {row.get('overall_health_score', 'N/A'):.1f}/100<br>
            <b>Priority:</b> {priority.title()}<br>
            <b>Pole Type:</b> {row.get('pole_type', 'Unknown')}<br>
            <b>Age:</b> {row.get('age_years', 'Unknown'):.1f} years<br>
            <b>Safety Risk:</b> {row.get('safety_risk', 0):.3f}<br>
            <b>Reliability Risk:</b> {row.get('reliability_risk', 0):.3f}
            """
            
            folium.CircleMarker(
                location=[row['latitude'], row['longitude']],
                radius=8,
                popup=folium.Popup(popup_content, max_width=300),
                color='black',
                fillColor=color,
                fillOpacity=0.7,
                weight=2
            ).add_to(m)
        
        # Add legend
        legend_html = """
        <div style="position: fixed; 
                    bottom: 50px; left: 50px; width: 150px; height: 120px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <p><b>Maintenance Priority</b></p>
        <p><i class="fa fa-circle" style="color:red"></i> Critical</p>
        <p><i class="fa fa-circle" style="color:orange"></i> High</p>
        <p><i class="fa fa-circle" style="color:yellow"></i> Medium</p>
        <p><i class="fa fa-circle" style="color:green"></i> Low</p>
        </div>
        """
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # Save map
        map_file = os.path.join(output_dir, 'pole_health_map.html')
        m.save(map_file)
        
        return map_file
    
    def create_trend_analysis(self, soil_history: pd.DataFrame, 
                             output_dir: str = 'Analysis') -> str:
        """Create soil condition trend analysis over time."""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        if 'sample_date' not in soil_history.columns:
            logger.debug("Date information not available for trend analysis")
            return None
        
        # Convert date column
        soil_history['sample_date'] = pd.to_datetime(soil_history['sample_date'])
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Soil Condition Trends Over Time', fontsize=16, fontweight='bold')
        
        # Plot moisture content trends
        if 'moisture_content' in soil_history.columns:
            for pole_id in soil_history['pole_id'].unique():
                pole_data = soil_history[soil_history['pole_id'] == pole_id]
                axes[0, 0].plot(pole_data['sample_date'], pole_data['moisture_content'], 
                               marker='o', label=pole_id, alpha=0.7)
            axes[0, 0].set_title('Moisture Content Trends')
            axes[0, 0].set_ylabel('Moisture Content (m³/m³)')
            axes[0, 0].legend()
            axes[0, 0].grid(True, alpha=0.3)
        
        # Plot pH trends
        if 'ph' in soil_history.columns:
            for pole_id in soil_history['pole_id'].unique():
                pole_data = soil_history[soil_history['pole_id'] == pole_id]
                if not pole_data['ph'].isna().all():
                    axes[0, 1].plot(pole_data['sample_date'], pole_data['ph'], 
                                   marker='s', label=pole_id, alpha=0.7)
            axes[0, 1].set_title('pH Trends')
            axes[0, 1].set_ylabel('pH Level')
            axes[0, 1].legend()
            axes[0, 1].grid(True, alpha=0.3)
        
        # Plot electrical conductivity trends
        if 'electrical_conductivity' in soil_history.columns:
            for pole_id in soil_history['pole_id'].unique():
                pole_data = soil_history[soil_history['pole_id'] == pole_id]
                if not pole_data['electrical_conductivity'].isna().all():
                    axes[1, 0].plot(pole_data['sample_date'], pole_data['electrical_conductivity'], 
                                   marker='^', label=pole_id, alpha=0.7)
            axes[1, 0].set_title('Electrical Conductivity Trends')
            axes[1, 0].set_ylabel('EC (dS/m)')
            axes[1, 0].legend()
            axes[1, 0].grid(True, alpha=0.3)
        
        # Plot bearing capacity trends  
        if 'bearing_capacity' in soil_history.columns:
            for pole_id in soil_history['pole_id'].unique():
                pole_data = soil_history[soil_history['pole_id'] == pole_id]
                if not pole_data['bearing_capacity'].isna().all():
                    axes[1, 1].plot(pole_data['sample_date'], pole_data['bearing_capacity'], 
                                   marker='d', label=pole_id, alpha=0.7)
            axes[1, 1].set_title('Bearing Capacity Trends')
            axes[1, 1].set_ylabel('Bearing Capacity (kPa)')
            axes[1, 1].legend()
            axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Save plot
        trend_file = os.path.join(output_dir, 'soil_condition_trends.png')
        plt.savefig(trend_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        return trend_file
    
    def generate_visual_report(self, assessment_df: pd.DataFrame, 
                              schedule_df: pd.DataFrame,
                              soil_history: Optional[pd.DataFrame] = None,
                              output_dir: str = 'Analysis') -> Dict[str, str]:
        """Generate complete visual assessment report."""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        generated_files = {}
        
        logger.debug("Generating visual assessment report...")
        
        # 1. Main dashboard
        logger.debug("  - Creating health overview dashboard...")
        dashboard_file = self.create_health_overview_dashboard(assessment_df, schedule_df, output_dir)
        generated_files['dashboard'] = dashboard_file
        
        # 2. Interactive map
        logger.debug("  - Creating interactive pole map...")
        map_file = self.create_interactive_map(assessment_df, output_dir)
        if map_file:
            generated_files['map'] = map_file
        
        # 3. Trend analysis
        if soil_history is not None and len(soil_history) > 0:
            logger.debug("  - Creating soil condition trends...")
            trend_file = self.create_trend_analysis(soil_history, output_dir)
            if trend_file:
                generated_files['trends'] = trend_file
        
        logger.debug(f"Visual report generated in: {output_dir}")
        return generated_files
