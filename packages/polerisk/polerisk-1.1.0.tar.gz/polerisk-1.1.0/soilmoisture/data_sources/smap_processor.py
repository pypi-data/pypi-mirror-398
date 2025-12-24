"""
SMAP (Soil Moisture Active Passive) data processor.
"""

import numpy as np
import pandas as pd
import h5py
from typing import Dict, List, Optional, Tuple, Union
from pathlib import Path
import logging
from datetime import datetime, timedelta

try:
    import netCDF4 as nc
    NETCDF_AVAILABLE = True
except ImportError:
    NETCDF_AVAILABLE = False

logger = logging.getLogger(__name__)


class SMAPProcessor:
    """
    Process SMAP soil moisture data products.
    
    Supports multiple SMAP products:
    - SPL3SMP (L3 Radiometer Global Daily)
    - SPL3SMA (L3 Radar/Radiometer Global Daily)
    - SPL2SMAP_S (L2 Radar/Radiometer Half-Orbit)
    """
    
    def __init__(self):
        self.product_configs = {
            'SPL3SMP': {
                'description': 'L3 Radiometer Global Daily',
                'resolution': '36km',
                'variables': {
                    'soil_moisture': 'Soil_Moisture_Retrieval_Data_AM/soil_moisture',
                    'latitude': 'Soil_Moisture_Retrieval_Data_AM/latitude',
                    'longitude': 'Soil_Moisture_Retrieval_Data_AM/longitude',
                    'quality_flag': 'Soil_Moisture_Retrieval_Data_AM/retrieval_qual_flag'
                }
            },
            'SPL3SMA': {
                'description': 'L3 Radar/Radiometer Global Daily',
                'resolution': '9km',
                'variables': {
                    'soil_moisture': 'Soil_Moisture_Retrieval_Data_AM/soil_moisture',
                    'soil_moisture_pm': 'Soil_Moisture_Retrieval_Data_PM/soil_moisture_pm',
                    'latitude': 'Soil_Moisture_Retrieval_Data_AM/latitude',
                    'longitude': 'Soil_Moisture_Retrieval_Data_AM/longitude',
                    'quality_flag_am': 'Soil_Moisture_Retrieval_Data_AM/retrieval_qual_flag_am',
                    'quality_flag_pm': 'Soil_Moisture_Retrieval_Data_PM/retrieval_qual_flag_pm'
                }
            }
        }
        
        self.quality_flags = {
            0: 'good_quality',
            1: 'acceptable_quality', 
            2: 'poor_quality',
            3: 'not_recommended'
        }
    
    def read_smap_file(self, filepath: Union[str, Path], 
                      product_type: str = 'SPL3SMP') -> Dict:
        """
        Read SMAP HDF5 file.
        
        Args:
            filepath: Path to SMAP HDF5 file
            product_type: SMAP product type ('SPL3SMP', 'SPL3SMA')
            
        Returns:
            Dictionary with SMAP data and metadata
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"SMAP file not found: {filepath}")
        
        if product_type not in self.product_configs:
            raise ValueError(f"Unknown product type: {product_type}")
        
        config = self.product_configs[product_type]
        
        try:
            with h5py.File(filepath, 'r') as f:
                data = {}
                
                # Read variables according to product configuration
                for var_name, hdf_path in config['variables'].items():
                    try:
                        if hdf_path in f:
                            dataset = f[hdf_path]
                            data[var_name] = dataset[:]
                            
                            # Get attributes
                            attrs = {}
                            for attr_name, attr_value in dataset.attrs.items():
                                attrs[attr_name] = attr_value
                            data[f'{var_name}_attrs'] = attrs
                            
                    except Exception as e:
                        logger.warning(f"Could not read {hdf_path}: {e}")
                
                # Read global attributes
                global_attrs = {}
                for attr_name, attr_value in f.attrs.items():
                    global_attrs[attr_name] = attr_value
                
                data['global_attributes'] = global_attrs
                data['product_type'] = product_type
                data['filename'] = filepath.name
                
                # Extract date from filename
                date_str = self._extract_date_from_filename(filepath.name)
                data['date'] = date_str
                
                return data
                
        except Exception as e:
            logger.error(f"Error reading SMAP file {filepath}: {e}")
            raise
    
    def _extract_date_from_filename(self, filename: str) -> Optional[str]:
        """Extract date from SMAP filename."""
        try:
            # SMAP filenames typically contain date in format YYYYMMDD
            # Example: SMAP_L3_SM_P_20230401_R18290_001.h5
            parts = filename.split('_')
            for part in parts:
                if len(part) == 8 and part.isdigit():
                    # Validate date
                    year = int(part[:4])
                    month = int(part[4:6])
                    day = int(part[6:8])
                    
                    if 1900 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31:
                        return part
            
        except Exception as e:
            logger.warning(f"Could not extract date from filename {filename}: {e}")
        
        return None
    
    def extract_point_data(self, smap_data: Dict, 
                          target_lat: float, target_lon: float,
                          search_radius: float = 0.5) -> Dict:
        """
        Extract SMAP data for a specific geographic point.
        
        Args:
            smap_data: SMAP data dictionary from read_smap_file
            target_lat: Target latitude
            target_lon: Target longitude  
            search_radius: Search radius in degrees
            
        Returns:
            Dictionary with extracted point data
        """
        if 'latitude' not in smap_data or 'longitude' not in smap_data:
            raise ValueError("Latitude/longitude data not found in SMAP file")
        
        lats = smap_data['latitude']
        lons = smap_data['longitude']
        
        # Handle different array structures
        if lats.ndim == 1 and lons.ndim == 1:
            # 1D lat/lon arrays - create meshgrid
            lon_grid, lat_grid = np.meshgrid(lons, lats)
        elif lats.ndim == 2 and lons.ndim == 2:
            # 2D lat/lon arrays
            lat_grid, lon_grid = lats, lons
        else:
            raise ValueError("Unsupported latitude/longitude array structure")
        
        # Find nearest grid point
        distance = np.sqrt((lat_grid - target_lat)**2 + (lon_grid - target_lon)**2)
        min_distance = np.nanmin(distance)
        
        if min_distance > search_radius:
            logger.warning(f"No SMAP data within {search_radius}° of target point")
            return {
                'target_lat': target_lat,
                'target_lon': target_lon,
                'found': False,
                'min_distance': min_distance
            }
        
        # Get indices of nearest point
        min_idx = np.nanargmin(distance)
        if lat_grid.ndim == 2:
            row_idx, col_idx = np.unravel_index(min_idx, lat_grid.shape)
        else:
            row_idx, col_idx = min_idx, 0
        
        # Extract data for this point
        point_data = {
            'target_lat': target_lat,
            'target_lon': target_lon,
            'actual_lat': float(lat_grid.flat[min_idx]),
            'actual_lon': float(lon_grid.flat[min_idx]),
            'distance': float(min_distance),
            'found': True,
            'date': smap_data.get('date'),
            'product_type': smap_data.get('product_type')
        }
        
        # Extract soil moisture and quality data
        if 'soil_moisture' in smap_data:
            sm_data = smap_data['soil_moisture']
            if sm_data.ndim >= 2:
                point_data['soil_moisture'] = float(sm_data.flat[min_idx])
            else:
                point_data['soil_moisture'] = float(sm_data[min_idx])
        
        # Handle PM data for SPL3SMA
        if 'soil_moisture_pm' in smap_data:
            sm_pm_data = smap_data['soil_moisture_pm']
            if sm_pm_data.ndim >= 2:
                point_data['soil_moisture_pm'] = float(sm_pm_data.flat[min_idx])
            else:
                point_data['soil_moisture_pm'] = float(sm_pm_data[min_idx])
        
        # Extract quality flags
        for qf_name in ['quality_flag', 'quality_flag_am', 'quality_flag_pm']:
            if qf_name in smap_data:
                qf_data = smap_data[qf_name]
                if qf_data.ndim >= 2:
                    qf_value = int(qf_data.flat[min_idx])
                else:
                    qf_value = int(qf_data[min_idx])
                
                point_data[qf_name] = qf_value
                point_data[f'{qf_name}_description'] = self.quality_flags.get(qf_value, 'unknown')
        
        return point_data
    
    def process_time_series(self, file_list: List[Union[str, Path]],
                           target_lat: float, target_lon: float,
                           product_type: str = 'SPL3SMP',
                           quality_threshold: int = 2) -> pd.DataFrame:
        """
        Process multiple SMAP files to create time series.
        
        Args:
            file_list: List of SMAP file paths
            target_lat: Target latitude
            target_lon: Target longitude
            product_type: SMAP product type
            quality_threshold: Maximum acceptable quality flag
            
        Returns:
            DataFrame with time series data
        """
        time_series_data = []
        
        for filepath in file_list:
            try:
                # Read SMAP file
                smap_data = self.read_smap_file(filepath, product_type)
                
                # Extract point data
                point_data = self.extract_point_data(smap_data, target_lat, target_lon)
                
                if not point_data['found']:
                    logger.warning(f"No data found in {filepath}")
                    continue
                
                # Apply quality filtering
                quality_ok = True
                for qf_name in ['quality_flag', 'quality_flag_am']:
                    if qf_name in point_data:
                        if point_data[qf_name] > quality_threshold:
                            quality_ok = False
                            break
                
                if not quality_ok:
                    logger.debug(f"Quality flag failed for {filepath}")
                    continue
                
                # Add to time series
                row_data = {
                    'date': point_data.get('date'),
                    'latitude': point_data['actual_lat'],
                    'longitude': point_data['actual_lon'],
                    'distance_km': point_data['distance'] * 111,  # Approximate conversion
                    'soil_moisture': point_data.get('soil_moisture'),
                    'product_type': product_type,
                    'filename': Path(filepath).name
                }
                
                # Add PM data if available
                if 'soil_moisture_pm' in point_data:
                    row_data['soil_moisture_pm'] = point_data['soil_moisture_pm']
                
                # Add quality flags
                for qf_name in ['quality_flag', 'quality_flag_am', 'quality_flag_pm']:
                    if qf_name in point_data:
                        row_data[qf_name] = point_data[qf_name]
                
                time_series_data.append(row_data)
                
            except Exception as e:
                logger.error(f"Error processing {filepath}: {e}")
                continue
        
        if not time_series_data:
            logger.warning("No valid SMAP data found")
            return pd.DataFrame()
        
        # Create DataFrame
        df = pd.DataFrame(time_series_data)
        
        # Convert date column
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], format='%Y%m%d', errors='coerce')
        
        # Sort by date
        df = df.sort_values('date').reset_index(drop=True)
        
        logger.info(f"Created SMAP time series with {len(df)} valid points")
        
        return df
    
    def get_data_info(self, smap_data: Dict) -> Dict:
        """Get information about SMAP data."""
        info = {
            'product_type': smap_data.get('product_type'),
            'date': smap_data.get('date'),
            'filename': smap_data.get('filename')
        }
        
        # Data array shapes
        for var in ['soil_moisture', 'latitude', 'longitude']:
            if var in smap_data:
                info[f'{var}_shape'] = smap_data[var].shape
        
        # Global attributes
        if 'global_attributes' in smap_data:
            attrs = smap_data['global_attributes']
            info['global_attributes'] = {
                k: (v.decode('utf-8') if isinstance(v, bytes) else v) 
                for k, v in attrs.items()
            }
        
        return info
    
    def validate_data_quality(self, point_data: Dict) -> Dict:
        """
        Validate SMAP data quality for a point.
        
        Args:
            point_data: Point data dictionary
            
        Returns:
            Dictionary with quality assessment
        """
        quality_assessment = {
            'overall_quality': 'unknown',
            'issues': [],
            'recommendations': []
        }
        
        # Check if data was found
        if not point_data.get('found', False):
            quality_assessment['overall_quality'] = 'no_data'
            quality_assessment['issues'].append('No data found at target location')
            return quality_assessment
        
        # Check soil moisture values
        sm_value = point_data.get('soil_moisture')
        if sm_value is not None:
            if np.isnan(sm_value):
                quality_assessment['issues'].append('Soil moisture is NaN')
            elif sm_value < 0 or sm_value > 1:
                quality_assessment['issues'].append(f'Soil moisture out of range: {sm_value}')
            elif sm_value == -9999:  # Common fill value
                quality_assessment['issues'].append('Soil moisture is fill value')
        
        # Check quality flags
        quality_scores = []
        for qf_name in ['quality_flag', 'quality_flag_am', 'quality_flag_pm']:
            if qf_name in point_data:
                qf_value = point_data[qf_name]
                quality_scores.append(qf_value)
                
                if qf_value > 2:
                    quality_assessment['issues'].append(f'{qf_name} indicates poor quality: {qf_value}')
        
        # Check distance from target
        distance = point_data.get('distance', 0)
        if distance > 0.25:  # > 0.25 degrees
            quality_assessment['issues'].append(f'Data point far from target: {distance:.3f}°')
        
        # Overall quality assessment
        if not quality_assessment['issues']:
            quality_assessment['overall_quality'] = 'good'
        elif len(quality_assessment['issues']) <= 2 and all(qf <= 1 for qf in quality_scores):
            quality_assessment['overall_quality'] = 'acceptable'
        else:
            quality_assessment['overall_quality'] = 'poor'
        
        # Add recommendations
        if quality_scores and max(quality_scores) > 1:
            quality_assessment['recommendations'].append('Consider additional quality filtering')
        
        if distance > 0.1:
            quality_assessment['recommendations'].append('Consider using higher resolution product')
        
        return quality_assessment
