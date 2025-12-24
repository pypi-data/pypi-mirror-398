"""
Unified configuration management for the soilmoisture package.

This module consolidates all configuration and parameter handling,
replacing the duplicate get_parameters() functions and providing
a consistent interface for path resolution and environment variables.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from netCDF4 import Dataset

logger = logging.getLogger(__name__)


class ConfigManager:
    """
    Unified configuration management for the soil moisture analysis system.
    
    This class provides a single point of configuration management,
    replacing the duplicate get_parameters() functions and adding
    enhanced environment variable support.
    """
    
    _instance = None
    _config_cache = None
    
    def __new__(cls):
        """Singleton pattern to ensure consistent configuration across modules."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def get_project_paths(cls) -> Dict[str, Path]:
        """
        Get standardized project directory paths.
        
        Returns:
            dict: Dictionary containing all project paths
        """
        # Determine project root - go up from this file to find project root
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent.parent  # soilmoisture/common/config.py -> project root
        
        paths = {
            'project_root': project_root,
            'input_dir': project_root / 'Input',
            'output_dir': project_root / 'Output', 
            'analysis_dir': project_root / 'Analysis',
            'uploads_dir': project_root / 'uploads',
            'lprm_netcdf_dir': project_root / 'Input' / 'LPRM_NetCDF',
            'insitu_data_dir': project_root / 'Input' / 'In-situ data',
        }
        
        # Create directories that should always exist
        for dir_key in ['output_dir', 'analysis_dir', 'uploads_dir', 'lprm_netcdf_dir']:
            paths[dir_key].mkdir(parents=True, exist_ok=True)
            
        return paths
    
    @classmethod
    def get_environment_config(cls) -> Dict[str, Any]:
        """
        Get configuration from environment variables.
        
        Returns:
            dict: Environment-based configuration
        """
        return {
            'debug': os.getenv('DEBUG', 'False').lower() == 'true',
            'log_level': os.getenv('LOG_LEVEL', 'INFO').upper(),
            'data_dir': os.getenv('DATA_DIR'),
            'output_dir': os.getenv('OUTPUT_DIR'), 
            'upload_folder': os.getenv('UPLOAD_FOLDER'),
            'max_content_length': int(os.getenv('MAX_CONTENT_LENGTH', '16777216')),  # 16MB
            'secret_key': os.getenv('SECRET_KEY', 'dev-key-change-in-production'),
            'flask_debug': os.getenv('FLASK_DEBUG', 'False').lower() == 'true',
            'weather_api_key': os.getenv('OPENWEATHERMAP_API_KEY'),
            'aws_access_key': os.getenv('AWS_ACCESS_KEY_ID'),
            'aws_secret_key': os.getenv('AWS_SECRET_ACCESS_KEY'),
            'aws_region': os.getenv('AWS_DEFAULT_REGION', 'us-east-1'),
        }
    
    @classmethod 
    def get_parameters(cls, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get complete configuration parameters for soil moisture analysis.
        
        This method replaces both duplicate get_parameters() functions
        and provides the superset of functionality from both.
        
        Args:
            force_refresh: Whether to bypass cache and reload configuration
            
        Returns:
            dict: Complete configuration dictionary
        """
        # Use cache unless forced refresh
        if not force_refresh and cls._config_cache is not None:
            return cls._config_cache.copy()
            
        logger.info("Loading soil moisture analysis configuration...")
        
        # Start with project paths
        config = cls.get_project_paths()
        
        # Add environment configuration
        env_config = cls.get_environment_config()
        config.update(env_config)
        
        # NetCDF file discovery and validation
        lprm_dir = config['lprm_netcdf_dir']
        netcdf_files = sorted(lprm_dir.glob("*.nc"))
        
        config.update({
            'lprm_des': lprm_dir,  # Legacy key name for compatibility
            'file_lprm_des': netcdf_files,
            'size_lprm_des': len(netcdf_files),
        })
        
        # NetCDF files validation and lat/lon extraction
        if len(netcdf_files) == 0:
            logger.warning(
                f"No NetCDF files found in {lprm_dir}. "
                "Please ensure your AMSR2 LPRM NetCDF files are in this directory."
            )
            config['lat_lprm'] = None
            config['lon_lprm'] = None
        else:
            logger.info(f"Found {len(netcdf_files)} NetCDF files in {lprm_dir}")
            
            # Try to read lat/lon from first available NetCDF file
            lat_lprm, lon_lprm = cls._extract_netcdf_coordinates(netcdf_files, config['input_dir'])
            config['lat_lprm'] = lat_lprm
            config['lon_lprm'] = lon_lprm
        
        # In-situ data path (look for standard file or first available .stm file)
        insitu_dir = config['insitu_data_dir'] 
        standard_insitu_file = (
            insitu_dir / "REMEDHUS_REMEDHUS_ElTomillar_sm_0.000000_0.050000_"
            "Stevens-Hydra-Probe_20150401_20150430.stm"
        )
        
        if standard_insitu_file.exists():
            config['in_situ'] = standard_insitu_file
        else:
            # Look for any .stm file
            stm_files = list(insitu_dir.glob("*.stm"))
            if stm_files:
                config['in_situ'] = stm_files[0]
                logger.info(f"Using in-situ data file: {stm_files[0]}")
            else:
                config['in_situ'] = standard_insitu_file  # Keep expected path for error messages
                logger.warning(f"No in-situ data files found in {insitu_dir}")
        
        # Legacy compatibility - add 'out' key
        config['out'] = config['output_dir']
        
        # Cache the configuration
        cls._config_cache = config.copy()
        
        logger.info("Configuration loaded successfully")
        return config
    
    @staticmethod
    def _extract_netcdf_coordinates(netcdf_files: List[Path], input_dir: Path) -> tuple:
        """
        Extract latitude and longitude coordinates from NetCDF files.
        
        Args:
            netcdf_files: List of NetCDF file paths
            input_dir: Input directory path for fallback files
            
        Returns:
            tuple: (latitude array, longitude array) or (None, None) if failed
        """
        # Try different NetCDF files and variable names
        candidates = list(netcdf_files)
        
        # Add fallback file if it exists
        fallback_file = input_dir / "LPRM-AMSR2_L3_D_SOILM3_V001_20150401013507.nc4"
        if fallback_file.exists():
            candidates.append(fallback_file)
        
        # Try different variable name patterns
        lat_var_names = ['lat', 'latitude', 'Latitude', 'LAT']
        lon_var_names = ['lon', 'longitude', 'Longitude', 'LON']
        
        for nc_file in candidates:
            try:
                with Dataset(nc_file, "r") as ds:
                    lat_data = None
                    lon_data = None
                    
                    # Try to find latitude variable
                    for lat_name in lat_var_names:
                        if lat_name in ds.variables:
                            lat_data = ds.variables[lat_name][:]
                            break
                    
                    # Try to find longitude variable  
                    for lon_name in lon_var_names:
                        if lon_name in ds.variables:
                            lon_data = ds.variables[lon_name][:]
                            break
                    
                    if lat_data is not None and lon_data is not None:
                        logger.info(f"Successfully extracted coordinates from {nc_file}")
                        return lat_data, lon_data
                        
            except Exception as e:
                logger.warning(f"Could not read coordinates from {nc_file}: {e}")
                continue
        
        logger.error("Could not extract lat/lon coordinates from any NetCDF file")
        return None, None
    
    @classmethod
    def validate_configuration(cls, config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Validate that the configuration contains required elements.
        
        Args:
            config: Configuration dictionary to validate (gets current config if None)
            
        Returns:
            bool: True if configuration is valid
        """
        if config is None:
            config = cls.get_parameters()
            
        required_paths = ['project_root', 'input_dir', 'output_dir']
        
        for path_key in required_paths:
            if path_key not in config or not config[path_key]:
                logger.error(f"Missing required configuration path: {path_key}")
                return False
                
            path_obj = Path(config[path_key])
            if not path_obj.exists():
                logger.error(f"Configuration path does not exist: {path_obj}")
                return False
        
        logger.info("Configuration validation passed")
        return True
