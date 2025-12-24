"""
Automated data ingestion and processing pipeline for soil moisture analysis.

This module provides automated workflows for data processing, including
batch processing, scheduled tasks, and data quality monitoring.
"""

from .data_ingestion import DataIngestionPipeline, ScheduledIngestion
from .processing_pipeline import ProcessingPipeline, BatchProcessor
from .monitoring import PipelineMonitor, DataQualityChecker

__all__ = [
    "DataIngestionPipeline",
    "ScheduledIngestion", 
    "ProcessingPipeline",
    "BatchProcessor",
    "PipelineMonitor",
    "DataQualityChecker",
]
