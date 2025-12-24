"""
Unified data loading utilities for the soilmoisture package.

This module consolidates all data loading functionality, eliminating
duplicate CSV parsing logic and providing consistent error handling
and data validation across the entire codebase.
"""

import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

from ..pole_health.pole_data import PoleInfo, SoilSample

logger = logging.getLogger(__name__)


class DataValidationError(Exception):
    """Raised when data validation fails."""
    pass


class DataLoader:
    """
    Unified data loading with consistent error handling and validation.
    
    This class replaces multiple duplicate data loading functions throughout
    the codebase with a single, well-tested implementation.
    """
    
    # Supported file extensions
    SUPPORTED_EXTENSIONS = {'.csv', '.txt', '.tsv'}
    
    # Standard date format patterns to try
    DATE_FORMATS = [
        '%Y-%m-%d',      # 2023-01-15
        '%Y%m%d',        # 20230115
        '%m/%d/%Y',      # 01/15/2023
        '%d/%m/%Y',      # 15/01/2023
        '%Y-%m-%d %H:%M:%S',  # 2023-01-15 10:30:00
    ]
    
    @classmethod
    def load_csv_data(
        cls, 
        filepath: Union[str, Path], 
        data_type: str = "generic",
        delimiter: Optional[str] = None,
        required_columns: Optional[List[str]] = None,
        date_columns: Optional[List[str]] = None,
        na_values: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Universal CSV loader with type-specific validation and error handling.
        
        Args:
            filepath: Path to the CSV file
            data_type: Type of data for validation ('generic', 'poles', 'soil', 'weather')
            delimiter: Column delimiter (auto-detected if None)
            required_columns: List of columns that must be present
            date_columns: List of columns to parse as dates
            na_values: Additional values to treat as NaN
            
        Returns:
            pd.DataFrame: Loaded and validated data
            
        Raises:
            FileNotFoundError: If file doesn't exist
            DataValidationError: If data validation fails
            ValueError: If file format is invalid
        """
        filepath = Path(filepath)
        
        # Validate file exists and has supported extension
        if not filepath.exists():
            raise FileNotFoundError(f"Data file not found: {filepath}")
            
        if filepath.suffix.lower() not in cls.SUPPORTED_EXTENSIONS:
            logger.warning(f"Unsupported file extension: {filepath.suffix}")
            
        logger.info(f"Loading {data_type} data from: {filepath}")
        
        # Set up parsing parameters
        na_values = na_values or ['NaN', 'nan', 'NA', 'N/A', '', 'NULL', 'null']
        
        try:
            # Auto-detect delimiter if not specified
            if delimiter is None:
                delimiter = cls._detect_delimiter(filepath)
                
            # Load the data
            if delimiter == 'whitespace':
                df = pd.read_csv(
                    filepath, 
                    sep=r'\s+',
                    na_values=na_values,
                    skipinitialspace=True
                )
            else:
                df = pd.read_csv(
                    filepath,
                    delimiter=delimiter,
                    na_values=na_values,
                    skipinitialspace=True
                )
                
            # Validate required columns
            if required_columns:
                missing_cols = set(required_columns) - set(df.columns)
                if missing_cols:
                    raise DataValidationError(
                        f"Missing required columns in {filepath}: {missing_cols}"
                    )
            
            # Parse date columns
            if date_columns:
                for col in date_columns:
                    if col in df.columns:
                        df[col] = cls._parse_date_column(df[col], col)
            
            # Data type specific validation
            cls._validate_data_type(df, data_type, filepath)
            
            logger.info(f"Successfully loaded {len(df)} rows from {filepath}")
            return df
            
        except pd.errors.EmptyDataError:
            raise DataValidationError(f"File is empty: {filepath}")
        except pd.errors.ParserError as e:
            raise ValueError(f"Could not parse file {filepath}: {str(e)}")
        except Exception as e:
            logger.error(f"Error loading data from {filepath}: {str(e)}")
            raise
    
    @classmethod
    def load_pole_data(cls, filepath: Union[str, Path]) -> List[PoleInfo]:
        """
        Load utility pole data from CSV file with standardized validation.
        
        Args:
            filepath: Path to the pole data CSV file
            
        Returns:
            List[PoleInfo]: List of validated PoleInfo objects
            
        Raises:
            FileNotFoundError: If file doesn't exist
            DataValidationError: If required pole fields are missing
        """
        required_columns = ['pole_id', 'latitude', 'longitude']
        date_columns = ['install_date']
        
        df = cls.load_csv_data(
            filepath=filepath,
            data_type='poles',
            required_columns=required_columns,
            date_columns=date_columns
        )
        
        poles = []
        
        for idx, row in df.iterrows():
            try:
                pole = PoleInfo(
                    pole_id=str(row['pole_id']),
                    latitude=float(row['latitude']),
                    longitude=float(row['longitude']),
                    pole_type=row.get('pole_type', 'wood'),
                    material=row.get('material', 'Unknown'),
                    height_ft=float(row.get('height_ft', 40.0)) if pd.notna(row.get('height_ft')) else 40.0,
                    install_date=row.get('install_date', pd.Timestamp('2000-01-01')),
                    voltage_class=row.get('voltage_class', 'distribution'),
                    structure_type=row.get('structure_type', 'tangent'),
                    diameter_base_inches=row.get('diameter_base_inches'),
                    treatment_type=row.get('treatment_type'),
                    condition_rating=row.get('condition_rating')
                )
                poles.append(pole)
                
            except (ValueError, TypeError) as e:
                logger.warning(f"Skipping invalid pole data at row {idx}: {str(e)}")
                continue
                
        logger.info(f"Successfully created {len(poles)} PoleInfo objects from {len(df)} rows")
        return poles
    
    @classmethod
    def load_soil_data(cls, filepath: Union[str, Path]) -> List[SoilSample]:
        """
        Load soil sample data from CSV file with standardized validation.
        
        Args:
            filepath: Path to the soil sample CSV file
            
        Returns:
            List[SoilSample]: List of validated SoilSample objects
            
        Raises:
            FileNotFoundError: If file doesn't exist
            DataValidationError: If required soil fields are missing
        """
        required_columns = ['pole_id', 'sample_date', 'moisture_content']
        date_columns = ['sample_date']
        
        df = cls.load_csv_data(
            filepath=filepath,
            data_type='soil',
            required_columns=required_columns,
            date_columns=date_columns
        )
        
        samples = []
        
        for idx, row in df.iterrows():
            try:
                sample = SoilSample(
                    pole_id=str(row['pole_id']),
                    sample_date=row['sample_date'],
                    depth_inches=float(row.get('depth_inches', 12.0)) if pd.notna(row.get('depth_inches')) else 12.0,
                    moisture_content=float(row['moisture_content']),
                    ph=row.get('ph') if pd.notna(row.get('ph')) else None,
                    bulk_density=row.get('bulk_density') if pd.notna(row.get('bulk_density')) else None,
                    electrical_conductivity=row.get('electrical_conductivity') if pd.notna(row.get('electrical_conductivity')) else None,
                    bearing_capacity=row.get('bearing_capacity') if pd.notna(row.get('bearing_capacity')) else None,
                    soil_type=row.get('soil_type'),
                    data_quality=row.get('data_quality', 'good')
                )
                samples.append(sample)
                
            except (ValueError, TypeError) as e:
                logger.warning(f"Skipping invalid soil sample at row {idx}: {str(e)}")
                continue
                
        logger.info(f"Successfully created {len(samples)} SoilSample objects from {len(df)} rows")
        return samples
    
    @classmethod
    def load_insitu_data(cls, filepath: Union[str, Path]) -> pd.DataFrame:
        """
        Load in-situ measurement data with standardized formatting.
        
        This handles the various formats of in-situ measurement files
        (.stm files and other whitespace-delimited formats).
        
        Args:
            filepath: Path to the in-situ data file
            
        Returns:
            pd.DataFrame: Standardized in-situ data
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"In-situ data file not found: {filepath}")
            
        try:
            # Try standard STM format first (whitespace delimited)
            df = pd.read_csv(
                filepath,
                sep=r'\s+',
                header=None,
                names=['date', 'in_situ', 'satellite'],
                na_values=['NaN', 'nan', 'NA', '-999', '-9999']
            )
            
            # Try to parse date column
            if 'date' in df.columns:
                df['date'] = cls._parse_date_column(df['date'], 'date')
            
            logger.info(f"Successfully loaded {len(df)} in-situ measurements from {filepath}")
            return df
            
        except Exception as e:
            logger.error(f"Error loading in-situ data from {filepath}: {str(e)}")
            raise
    
    @staticmethod
    def _detect_delimiter(filepath: Path) -> str:
        """
        Auto-detect the delimiter used in a CSV file.
        
        Args:
            filepath: Path to the file
            
        Returns:
            str: Detected delimiter (',' ';' '\t' or 'whitespace')
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                first_line = f.readline()
                
            # Count occurrences of common delimiters
            delimiters = {',': 0, ';': 0, '\t': 0}
            for delimiter in delimiters:
                delimiters[delimiter] = first_line.count(delimiter)
            
            # Return the most common delimiter
            best_delimiter = max(delimiters, key=delimiters.get)
            
            # If no clear delimiter found, assume whitespace
            if delimiters[best_delimiter] == 0:
                return 'whitespace'
                
            return best_delimiter
            
        except Exception:
            logger.warning(f"Could not auto-detect delimiter for {filepath}, using comma")
            return ','
    
    @classmethod
    def _parse_date_column(cls, series: pd.Series, column_name: str) -> pd.Series:
        """
        Parse a date column trying multiple common formats.
        
        Args:
            series: Pandas Series containing date strings
            column_name: Name of the column (for logging)
            
        Returns:
            pd.Series: Parsed datetime series
        """
        if series.dtype == 'datetime64[ns]':
            return series  # Already datetime
            
        # Try each date format
        for date_format in cls.DATE_FORMATS:
            try:
                return pd.to_datetime(series, format=date_format, errors='coerce')
            except (ValueError, TypeError):
                continue
        
        # Fall back to pandas automatic parsing
        try:
            return pd.to_datetime(series, infer_datetime_format=True, errors='coerce')
        except Exception:
            logger.warning(f"Could not parse dates in column '{column_name}'")
            return series
    
    @staticmethod
    def _validate_data_type(df: pd.DataFrame, data_type: str, filepath: Path) -> None:
        """
        Perform data type specific validation.
        
        Args:
            df: DataFrame to validate
            data_type: Type of data ('poles', 'soil', 'weather', etc.)
            filepath: File path (for error messages)
            
        Raises:
            DataValidationError: If validation fails
        """
        if data_type == 'poles':
            # Validate pole data
            if 'latitude' in df.columns:
                invalid_lat = (df['latitude'] < -90) | (df['latitude'] > 90)
                if invalid_lat.any():
                    raise DataValidationError(f"Invalid latitude values in {filepath}")
                    
            if 'longitude' in df.columns:
                invalid_lon = (df['longitude'] < -180) | (df['longitude'] > 180)
                if invalid_lon.any():
                    raise DataValidationError(f"Invalid longitude values in {filepath}")
                    
        elif data_type == 'soil':
            # Validate soil data
            if 'moisture_content' in df.columns:
                invalid_moisture = (df['moisture_content'] < 0) | (df['moisture_content'] > 1)
                if invalid_moisture.any():
                    logger.warning(f"Suspicious moisture content values in {filepath} (should be 0-1)")
                    
            if 'ph' in df.columns:
                invalid_ph = (df['ph'] < 0) | (df['ph'] > 14)
                if invalid_ph.any():
                    logger.warning(f"Suspicious pH values in {filepath} (should be 0-14)")
        
        # General validation
        if len(df) == 0:
            raise DataValidationError(f"No valid data rows found in {filepath}")
