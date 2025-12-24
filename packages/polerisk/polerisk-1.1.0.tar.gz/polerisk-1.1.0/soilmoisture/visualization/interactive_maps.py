"""
Interactive geospatial visualization capabilities for soil moisture data.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
import logging
from pathlib import Path
import signalplot

# Apply SignalPlot minimalist defaults
signalplot.apply()

try:
    import folium
    from folium import plugins
    FOLIUM_AVAILABLE = True
except ImportError:
    FOLIUM_AVAILABLE = False

try:
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

try:
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    CARTOPY_AVAILABLE = True
except ImportError:
    CARTOPY_AVAILABLE = False

logger = logging.getLogger(__name__)


class InteractiveMapGenerator:
    """
    Generate interactive maps for soil moisture data visualization.
    """
    
    def __init__(self):
        self.default_center = [39.8283, -98.5795]  # Geographic center of US
        self.default_zoom = 4
        
    def create_site_map(self, sites_data: Union[pd.DataFrame, Dict], 
                       output_path: Optional[str] = None) -> str:
        """
        Create an interactive map showing soil moisture monitoring sites.
        
        Args:
            sites_data: DataFrame or dict with site information (lat, lon, name, values)
            output_path: Path to save the HTML map file
            
        Returns:
            Path to the generated HTML file
        """
        if not FOLIUM_AVAILABLE:
            raise ImportError("Folium is required for interactive maps. Install with: pip install folium")
        
        # Convert dict to DataFrame if needed
        if isinstance(sites_data, dict):
            sites_data = pd.DataFrame(sites_data)
        
        # Create base map
        center_lat = sites_data['lat'].mean() if 'lat' in sites_data.columns else self.default_center[0]
        center_lon = sites_data['lon'].mean() if 'lon' in sites_data.columns else self.default_center[1]
        
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=self.default_zoom,
            tiles='OpenStreetMap'
        )
        
        # Add different tile layers
        folium.TileLayer('Stamen Terrain').add_to(m)
        folium.TileLayer('Stamen Toner').add_to(m)
        folium.TileLayer('cartodb positron').add_to(m)
        
        # Add layer control
        folium.LayerControl().add_to(m)
        
        # Add sites as markers
        for idx, row in sites_data.iterrows():
            if 'lat' in row and 'lon' in row:
                # Determine marker color based on soil moisture value if available
                color = 'blue'  # default
                if 'soil_moisture' in row:
                    sm_value = row['soil_moisture']
                    if pd.notna(sm_value):
                        if sm_value < 0.1:
                            color = 'red'      # dry
                        elif sm_value < 0.2:
                            color = 'orange'   # moderate
                        elif sm_value < 0.3:
                            color = 'yellow'   # moist
                        else:
                            color = 'green'    # wet
                
                # Create popup content
                popup_content = f"""
                <div style='width: 200px'>
                    <h4>{row.get('name', f'Site {idx}')}</h4>
                    <p><b>Location:</b> {row['lat']:.4f}°N, {row['lon']:.4f}°W</p>
                """
                
                if 'soil_moisture' in row and pd.notna(row['soil_moisture']):
                    popup_content += f"<p><b>Soil Moisture:</b> {row['soil_moisture']:.3f} m³/m³</p>"
                
                if 'date' in row and pd.notna(row['date']):
                    popup_content += f"<p><b>Date:</b> {row['date']}</p>"
                
                if 'elevation' in row and pd.notna(row['elevation']):
                    popup_content += f"<p><b>Elevation:</b> {row['elevation']:.0f} m</p>"
                
                popup_content += "</div>"
                
                # Add marker
                folium.Marker(
                    location=[row['lat'], row['lon']],
                    popup=folium.Popup(popup_content, max_width=300),
                    tooltip=row.get('name', f'Site {idx}'),
                    icon=folium.Icon(color=color, icon='tint')
                ).add_to(m)
        
        # Add a legend
        legend_html = '''
        <div style="position: fixed; 
                    bottom: 50px; left: 50px; width: 150px; height: 120px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <h4>Soil Moisture</h4>
        <p><i class="fa fa-circle" style="color:red"></i> Dry (&lt;0.1)</p>
        <p><i class="fa fa-circle" style="color:orange"></i> Moderate (0.1-0.2)</p>
        <p><i class="fa fa-circle" style="color:yellow"></i> Moist (0.2-0.3)</p>
        <p><i class="fa fa-circle" style="color:green"></i> Wet (&gt;0.3)</p>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # Save map
        if not output_path:
            output_path = 'soil_moisture_sites_map.html'
        
        m.save(output_path)
        logger.info(f"Interactive site map saved to {output_path}")
        
        return output_path
    
    def create_heatmap(self, grid_data: pd.DataFrame, 
                      output_path: Optional[str] = None) -> str:
        """
        Create a heat map of soil moisture values across a grid.
        
        Args:
            grid_data: DataFrame with lat, lon, and soil_moisture columns
            output_path: Path to save the HTML map file
            
        Returns:
            Path to the generated HTML file
        """
        if not FOLIUM_AVAILABLE:
            raise ImportError("Folium is required for heat maps")
        
        # Create base map
        center_lat = grid_data['lat'].mean()
        center_lon = grid_data['lon'].mean()
        
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=6,
            tiles='OpenStreetMap'
        )
        
        # Prepare data for heatmap
        heat_data = []
        for idx, row in grid_data.iterrows():
            if pd.notna(row['soil_moisture']):
                # Weight by soil moisture value (normalized to 0-1)
                weight = float(row['soil_moisture'])
                heat_data.append([row['lat'], row['lon'], weight])
        
        # Add heatmap layer
        plugins.HeatMap(
            heat_data,
            min_opacity=0.2,
            max_zoom=18,
            radius=15,
            blur=10,
            gradient={
                0.0: 'blue',    # low soil moisture
                0.5: 'yellow',  # medium
                1.0: 'red'      # high soil moisture
            }
        ).add_to(m)
        
        # Save map
        if not output_path:
            output_path = 'soil_moisture_heatmap.html'
        
        m.save(output_path)
        logger.info(f"Soil moisture heat map saved to {output_path}")
        
        return output_path
    
    def create_time_animation(self, time_series_data: pd.DataFrame,
                            output_path: Optional[str] = None) -> str:
        """
        Create an animated map showing soil moisture changes over time.
        
        Args:
            time_series_data: DataFrame with date, lat, lon, soil_moisture columns
            output_path: Path to save the HTML map file
            
        Returns:
            Path to the generated HTML file
        """
        if not FOLIUM_AVAILABLE:
            raise ImportError("Folium is required for animated maps")
        
        # Sort by date
        time_series_data = time_series_data.sort_values('date')
        
        # Create base map
        center_lat = time_series_data['lat'].mean()
        center_lon = time_series_data['lon'].mean()
        
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=6,
            tiles='OpenStreetMap'
        )
        
        # Group data by date
        dates = time_series_data['date'].unique()
        
        # Create time series data for animation
        features = []
        
        for date in dates:
            date_data = time_series_data[time_series_data['date'] == date]
            
            for idx, row in date_data.iterrows():
                if pd.notna(row['soil_moisture']):
                    # Create feature for this time step
                    feature = {
                        'type': 'Feature',
                        'geometry': {
                            'type': 'Point',
                            'coordinates': [row['lon'], row['lat']]
                        },
                        'properties': {
                            'time': str(date),
                            'style': {
                                'color': self._get_color_for_value(row['soil_moisture']),
                                'fillColor': self._get_color_for_value(row['soil_moisture']),
                                'fillOpacity': 0.7,
                                'radius': 8
                            },
                            'popup': f"Date: {date}<br>Soil Moisture: {row['soil_moisture']:.3f}"
                        }
                    }
                    features.append(feature)
        
        # Add time slider plugin
        plugins.TimestampedGeoJson(
            {
                'type': 'FeatureCollection',
                'features': features
            },
            period='P1D',  # 1 day period
            add_last_point=True,
            auto_play=False,
            loop=False,
            max_speed=5,
            loop_button=True,
            date_options='YYYY-MM-DD',
            time_slider_drag_update=True
        ).add_to(m)
        
        # Save map
        if not output_path:
            output_path = 'soil_moisture_animation.html'
        
        m.save(output_path)
        logger.info(f"Animated soil moisture map saved to {output_path}")
        
        return output_path
    
    def _get_color_for_value(self, value: float) -> str:
        """Get color code for soil moisture value."""
        if value < 0.1:
            return '#8B0000'  # Dark red (dry)
        elif value < 0.15:
            return '#FF4500'  # Orange red
        elif value < 0.2:
            return '#FFA500'  # Orange
        elif value < 0.25:
            return '#FFFF00'  # Yellow
        elif value < 0.3:
            return '#ADFF2F'  # Green yellow
        else:
            return '#008000'  # Green (wet)
    
    def create_3d_surface(self, grid_data: pd.DataFrame,
                         output_path: Optional[str] = None) -> str:
        """
        Create a 3D surface plot of soil moisture data using matplotlib.
        
        Args:
            grid_data: DataFrame with lat, lon, soil_moisture columns
            output_path: Path to save image file
            
        Returns:
            Path to generated image file
        """
        try:
            from mpl_toolkits.mplot3d import Axes3D
        except ImportError:
            raise ImportError("matplotlib 3D plotting is required for 3D visualizations")
        
        # Create grid for surface plot
        lats = np.sort(grid_data['lat'].unique())
        lons = np.sort(grid_data['lon'].unique())
        
        # Create meshgrid
        lon_grid, lat_grid = np.meshgrid(lons, lats)
        sm_grid = np.full_like(lon_grid, np.nan)
        
        # Fill grid with soil moisture values
        for idx, row in grid_data.iterrows():
            if pd.notna(row['soil_moisture']):
                lat_idx = np.argmin(np.abs(lats - row['lat']))
                lon_idx = np.argmin(np.abs(lons - row['lon']))
                sm_grid[lat_idx, lon_idx] = row['soil_moisture']
        
        # Create 3D surface plot using matplotlib
        fig = plt.figure(figsize=(12, 9))
        ax = fig.add_subplot(111, projection='3d')
        
        surf = ax.plot_surface(lon_grid, lat_grid, sm_grid, cmap='RdYlBu', 
                              alpha=0.8, linewidth=0, antialiased=True)
        
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
        ax.set_zlabel('Soil Moisture (m³/m³)')
        ax.set_title('3D Soil Moisture Surface')
        
        # Add colorbar
        fig.colorbar(surf, ax=ax, shrink=0.5, aspect=20, label='Soil Moisture (m³/m³)')
        
        if not output_path:
            output_path = 'soil_moisture_3d_surface.png'
        
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        logger.info(f"3D surface plot saved to {output_path}")
        
        return output_path


class GeospatialAnalyzer:
    """
    Advanced geospatial analysis for soil moisture data.
    """
    
    def __init__(self):
        self.earth_radius_km = 6371.0
    
    def calculate_distance(self, lat1: float, lon1: float, 
                          lat2: float, lon2: float) -> float:
        """
        Calculate great circle distance between two points in kilometers.
        """
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
        c = 2 * np.arcsin(np.sqrt(a))
        
        return self.earth_radius_km * c
    
    def find_nearby_sites(self, reference_point: Tuple[float, float],
                         sites_data: pd.DataFrame,
                         max_distance_km: float = 50) -> pd.DataFrame:
        """
        Find sites within a specified distance of a reference point.
        
        Args:
            reference_point: (lat, lon) tuple for reference location
            sites_data: DataFrame with site locations
            max_distance_km: Maximum distance in kilometers
            
        Returns:
            DataFrame with nearby sites and distances
        """
        ref_lat, ref_lon = reference_point
        
        # Calculate distances
        distances = []
        for idx, row in sites_data.iterrows():
            dist = self.calculate_distance(ref_lat, ref_lon, row['lat'], row['lon'])
            distances.append(dist)
        
        # Add distances to DataFrame
        nearby_sites = sites_data.copy()
        nearby_sites['distance_km'] = distances
        
        # Filter by distance
        nearby_sites = nearby_sites[nearby_sites['distance_km'] <= max_distance_km]
        nearby_sites = nearby_sites.sort_values('distance_km')
        
        return nearby_sites
    
    def spatial_interpolation(self, known_points: pd.DataFrame, 
                            grid_resolution: float = 0.1) -> pd.DataFrame:
        """
        Perform spatial interpolation of soil moisture values.
        
        Args:
            known_points: DataFrame with lat, lon, soil_moisture columns
            grid_resolution: Resolution of output grid in degrees
            
        Returns:
            DataFrame with interpolated grid values
        """
        try:
            from scipy.interpolate import griddata
        except ImportError:
            raise ImportError("SciPy is required for spatial interpolation")
        
        # Define grid bounds
        lat_min, lat_max = known_points['lat'].min(), known_points['lat'].max()
        lon_min, lon_max = known_points['lon'].min(), known_points['lon'].max()
        
        # Create grid
        lat_grid = np.arange(lat_min, lat_max + grid_resolution, grid_resolution)
        lon_grid = np.arange(lon_min, lon_max + grid_resolution, grid_resolution)
        
        lon_mesh, lat_mesh = np.meshgrid(lon_grid, lat_grid)
        
        # Prepare known points
        points = known_points[['lon', 'lat']].values
        values = known_points['soil_moisture'].values
        
        # Remove NaN values
        valid_mask = ~np.isnan(values)
        points = points[valid_mask]
        values = values[valid_mask]
        
        # Interpolate
        interpolated = griddata(
            points, values, (lon_mesh, lat_mesh), 
            method='linear', fill_value=np.nan
        )
        
        # Create result DataFrame
        result_data = []
        for i, lat in enumerate(lat_grid):
            for j, lon in enumerate(lon_grid):
                if not np.isnan(interpolated[i, j]):
                    result_data.append({
                        'lat': lat,
                        'lon': lon,
                        'soil_moisture': interpolated[i, j]
                    })
        
        return pd.DataFrame(result_data)
    
    def calculate_spatial_statistics(self, data: pd.DataFrame) -> Dict:
        """
        Calculate spatial statistics for soil moisture data.
        
        Args:
            data: DataFrame with lat, lon, soil_moisture columns
            
        Returns:
            Dictionary with spatial statistics
        """
        stats = {}
        
        # Basic spatial extent
        stats['spatial_extent'] = {
            'lat_min': float(data['lat'].min()),
            'lat_max': float(data['lat'].max()),
            'lon_min': float(data['lon'].min()),
            'lon_max': float(data['lon'].max()),
            'lat_range': float(data['lat'].max() - data['lat'].min()),
            'lon_range': float(data['lon'].max() - data['lon'].min())
        }
        
        # Calculate approximate area covered
        lat_range_km = stats['spatial_extent']['lat_range'] * 111  # ~111 km per degree
        avg_lat = data['lat'].mean()
        lon_range_km = stats['spatial_extent']['lon_range'] * 111 * np.cos(np.radians(avg_lat))
        stats['approximate_area_km2'] = lat_range_km * lon_range_km
        
        # Spatial distribution of values
        valid_data = data.dropna(subset=['soil_moisture'])
        if len(valid_data) > 0:
            stats['value_distribution'] = {
                'mean': float(valid_data['soil_moisture'].mean()),
                'std': float(valid_data['soil_moisture'].std()),
                'min': float(valid_data['soil_moisture'].min()),
                'max': float(valid_data['soil_moisture'].max()),
                'q25': float(valid_data['soil_moisture'].quantile(0.25)),
                'q75': float(valid_data['soil_moisture'].quantile(0.75))
            }
        
        # Site density
        stats['site_density_per_1000km2'] = len(data) / (stats['approximate_area_km2'] / 1000)
        
        return stats


def create_comprehensive_map_dashboard(data: pd.DataFrame, 
                                     output_dir: str = 'geospatial_output') -> List[str]:
    """
    Create a comprehensive set of geospatial visualizations.
    
    Args:
        data: DataFrame with soil moisture data
        output_dir: Directory to save output files
        
    Returns:
        List of paths to generated files
    """
    Path(output_dir).mkdir(exist_ok=True)
    
    map_gen = InteractiveMapGenerator()
    spatial_analyzer = GeospatialAnalyzer()
    
    output_files = []
    
    try:
        # Site map
        if 'lat' in data.columns and 'lon' in data.columns:
            site_map_path = Path(output_dir) / 'interactive_site_map.html'
            map_gen.create_site_map(data, str(site_map_path))
            output_files.append(str(site_map_path))
        
        # Heat map (if enough spatial data)
        if len(data) > 10 and 'lat' in data.columns and 'lon' in data.columns:
            try:
                heatmap_path = Path(output_dir) / 'soil_moisture_heatmap.html'
                map_gen.create_heatmap(data, str(heatmap_path))
                output_files.append(str(heatmap_path))
            except Exception as e:
                logger.warning(f"Could not create heat map: {e}")
        
        # 3D surface plot
        if len(data) > 20:
            try:
                surface_path = Path(output_dir) / 'soil_moisture_3d_surface.png'
                map_gen.create_3d_surface(data, str(surface_path))
                output_files.append(str(surface_path))
            except Exception as e:
                logger.warning(f"Could not create 3D surface plot: {e}")
        
        # Spatial statistics
        if 'lat' in data.columns and 'lon' in data.columns:
            stats = spatial_analyzer.calculate_spatial_statistics(data)
            stats_path = Path(output_dir) / 'spatial_statistics.json'
            
            import json
            with open(stats_path, 'w') as f:
                json.dump(stats, f, indent=2)
            output_files.append(str(stats_path))
        
        logger.info(f"Generated {len(output_files)} geospatial visualizations in {output_dir}")
        
    except Exception as e:
        logger.error(f"Error creating geospatial visualizations: {e}")
    
    return output_files
