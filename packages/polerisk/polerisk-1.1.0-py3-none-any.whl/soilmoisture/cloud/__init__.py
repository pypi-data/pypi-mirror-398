"""
Cloud processing and storage integration for soil moisture analysis.

This module provides cloud computing capabilities including AWS S3 integration,
batch processing, and distributed computing support.
"""

from .aws_integration import AWSProcessor, S3DataManager
from .batch_processing import BatchProcessor, DistributedProcessor
from .cloud_storage import CloudStorageManager

__all__ = [
    "AWSProcessor",
    "S3DataManager", 
    "BatchProcessor",
    "DistributedProcessor",
    "CloudStorageManager",
]
