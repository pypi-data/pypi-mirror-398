"""
Automated data ingestion pipeline for soil moisture data.
"""

import os
import shutil
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
import logging
import schedule
import threading
from dataclasses import dataclass, field
from enum import Enum

import pandas as pd
import numpy as np

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False

try:
    import ftplib
    import paramiko  # for SFTP
    FTP_AVAILABLE = True
except ImportError:
    FTP_AVAILABLE = False

logger = logging.getLogger(__name__)


class DataSource(Enum):
    """Data source types."""
    LOCAL_DIRECTORY = "local_directory"
    FTP_SERVER = "ftp_server"
    SFTP_SERVER = "sftp_server"
    HTTP_DOWNLOAD = "http_download"
    AWS_S3 = "aws_s3"
    DATABASE = "database"


@dataclass
class IngestionConfig:
    """Configuration for data ingestion."""
    source_type: DataSource
    source_path: str
    destination_path: str
    file_pattern: str = "*.nc"
    processing_function: Optional[Callable] = None
    quality_checks: List[Callable] = field(default_factory=list)
    move_processed_files: bool = True
    processed_files_dir: Optional[str] = None
    error_files_dir: Optional[str] = None
    max_file_age_hours: int = 24
    retry_attempts: int = 3
    retry_delay_seconds: int = 60


class FileWatcher(FileSystemEventHandler):
    """Watch for new files and trigger processing."""
    
    def __init__(self, ingestion_pipeline):
        self.pipeline = ingestion_pipeline
        super().__init__()
    
    def on_created(self, event):
        """Handle new file creation."""
        if not event.is_directory:
            logger.info(f"New file detected: {event.src_path}")
            time.sleep(2)  # Wait for file to be fully written
            self.pipeline.process_file(event.src_path)
    
    def on_moved(self, event):
        """Handle file moves (renames)."""
        if not event.is_directory:
            logger.info(f"File moved to: {event.dest_path}")
            time.sleep(2)
            self.pipeline.process_file(event.dest_path)


class DataIngestionPipeline:
    """
    Automated data ingestion pipeline.
    """
    
    def __init__(self, config: IngestionConfig):
        self.config = config
        self.processed_files = set()
        self.failed_files = {}  # filename -> (error, retry_count)
        self.is_running = False
        self.observer = None
        
        # Create directories
        Path(config.destination_path).mkdir(parents=True, exist_ok=True)
        
        if config.processed_files_dir:
            Path(config.processed_files_dir).mkdir(parents=True, exist_ok=True)
        
        if config.error_files_dir:
            Path(config.error_files_dir).mkdir(parents=True, exist_ok=True)
    
    def start_watching(self) -> bool:
        """Start watching for new files."""
        if not WATCHDOG_AVAILABLE:
            logger.error("Watchdog not available for file watching")
            return False
        
        if self.config.source_type != DataSource.LOCAL_DIRECTORY:
            logger.error("File watching only supported for local directories")
            return False
        
        try:
            self.observer = Observer()
            event_handler = FileWatcher(self)
            
            self.observer.schedule(
                event_handler, 
                self.config.source_path, 
                recursive=True
            )
            
            self.observer.start()
            self.is_running = True
            
            logger.info(f"Started watching directory: {self.config.source_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start file watcher: {e}")
            return False
    
    def stop_watching(self):
        """Stop watching for new files."""
        if self.observer and self.is_running:
            self.observer.stop()
            self.observer.join()
            self.is_running = False
            logger.info("Stopped file watcher")
    
    def scan_and_process_existing_files(self):
        """Scan for and process existing files."""
        try:
            source_path = Path(self.config.source_path)
            
            if not source_path.exists():
                logger.error(f"Source path does not exist: {source_path}")
                return
            
            # Find matching files
            if self.config.file_pattern:
                files = list(source_path.glob(self.config.file_pattern))
            else:
                files = [f for f in source_path.iterdir() if f.is_file()]
            
            logger.info(f"Found {len(files)} files to process")
            
            for file_path in files:
                if file_path.name not in self.processed_files:
                    self.process_file(str(file_path))
                    
        except Exception as e:
            logger.error(f"Error scanning existing files: {e}")
    
    def process_file(self, file_path: str) -> bool:
        """
        Process a single file.
        
        Args:
            file_path: Path to file to process
            
        Returns:
            True if processing succeeded
        """
        file_path = Path(file_path)
        
        try:
            # Check if file has already been processed
            if file_path.name in self.processed_files:
                logger.debug(f"File already processed: {file_path.name}")
                return True
            
            # Check file age
            if self._is_file_too_old(file_path):
                logger.warning(f"File too old, skipping: {file_path.name}")
                return False
            
            # Wait for file to be fully written
            self._wait_for_file_stability(file_path)
            
            # Run quality checks
            if not self._run_quality_checks(file_path):
                logger.warning(f"Quality checks failed for: {file_path.name}")
                self._move_to_error_dir(file_path, "Quality checks failed")
                return False
            
            # Run processing function if specified
            if self.config.processing_function:
                try:
                    result = self.config.processing_function(str(file_path))
                    if not result:
                        raise ValueError("Processing function returned False")
                except Exception as e:
                    logger.error(f"Processing function failed for {file_path.name}: {e}")
                    self._handle_processing_failure(file_path, str(e))
                    return False
            
            # Move file to destination
            destination_path = Path(self.config.destination_path) / file_path.name
            
            if file_path != destination_path:
                shutil.move(str(file_path), str(destination_path))
                logger.info(f"Moved file to: {destination_path}")
            
            # Mark as processed
            self.processed_files.add(file_path.name)
            
            # Move to processed files directory if configured
            if self.config.move_processed_files and self.config.processed_files_dir:
                processed_path = Path(self.config.processed_files_dir) / file_path.name
                shutil.move(str(destination_path), str(processed_path))
                logger.info(f"Moved processed file to: {processed_path}")
            
            # Clear any previous failure record
            if file_path.name in self.failed_files:
                del self.failed_files[file_path.name]
            
            logger.info(f"Successfully processed: {file_path.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            self._handle_processing_failure(file_path, str(e))
            return False
    
    def _wait_for_file_stability(self, file_path: Path, 
                                stability_time: int = 2) -> bool:
        """Wait for file to be stable (not being written to)."""
        try:
            previous_size = -1
            stable_count = 0
            max_wait = 30  # seconds
            wait_time = 0
            
            while wait_time < max_wait:
                current_size = file_path.stat().st_size
                
                if current_size == previous_size:
                    stable_count += 1
                    if stable_count >= stability_time:
                        return True
                else:
                    stable_count = 0
                
                previous_size = current_size
                time.sleep(1)
                wait_time += 1
            
            logger.warning(f"File may still be writing: {file_path}")
            return True  # Proceed anyway
            
        except Exception as e:
            logger.warning(f"Could not check file stability: {e}")
            return True
    
    def _is_file_too_old(self, file_path: Path) -> bool:
        """Check if file is too old to process."""
        try:
            file_age = datetime.now() - datetime.fromtimestamp(file_path.stat().st_mtime)
            return file_age.total_seconds() > (self.config.max_file_age_hours * 3600)
        except Exception:
            return False
    
    def _run_quality_checks(self, file_path: Path) -> bool:
        """Run quality checks on file."""
        for check_function in self.config.quality_checks:
            try:
                if not check_function(str(file_path)):
                    return False
            except Exception as e:
                logger.error(f"Quality check failed: {e}")
                return False
        
        return True
    
    def _handle_processing_failure(self, file_path: Path, error_msg: str):
        """Handle processing failure with retry logic."""
        filename = file_path.name
        
        # Update failure count
        if filename in self.failed_files:
            error, retry_count = self.failed_files[filename]
            self.failed_files[filename] = (error_msg, retry_count + 1)
        else:
            self.failed_files[filename] = (error_msg, 1)
        
        error, retry_count = self.failed_files[filename]
        
        # Check if we should retry
        if retry_count < self.config.retry_attempts:
            logger.info(f"Will retry processing {filename} (attempt {retry_count + 1})")
            # Schedule retry (in a real implementation, you might use a task queue)
            return
        
        # Max retries reached, move to error directory
        logger.error(f"Max retries reached for {filename}, moving to error directory")
        self._move_to_error_dir(file_path, error_msg)
    
    def _move_to_error_dir(self, file_path: Path, error_msg: str):
        """Move failed file to error directory."""
        if not self.config.error_files_dir:
            return
        
        try:
            error_path = Path(self.config.error_files_dir) / file_path.name
            shutil.move(str(file_path), str(error_path))
            
            # Create error log file
            error_log_path = Path(self.config.error_files_dir) / f"{file_path.name}.error.txt"
            with open(error_log_path, 'w') as f:
                f.write(f"Error processing file: {file_path.name}\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"Error: {error_msg}\n")
            
            logger.info(f"Moved failed file to: {error_path}")
            
        except Exception as e:
            logger.error(f"Could not move file to error directory: {e}")
    
    def get_status(self) -> Dict:
        """Get pipeline status."""
        return {
            'is_running': self.is_running,
            'processed_files_count': len(self.processed_files),
            'failed_files_count': len(self.failed_files),
            'source_path': self.config.source_path,
            'destination_path': self.config.destination_path,
            'config': {
                'source_type': self.config.source_type.value,
                'file_pattern': self.config.file_pattern,
                'max_file_age_hours': self.config.max_file_age_hours,
                'retry_attempts': self.config.retry_attempts
            }
        }


class ScheduledIngestion:
    """
    Schedule periodic data ingestion tasks.
    """
    
    def __init__(self):
        self.scheduled_jobs = {}
        self.is_running = False
        self.scheduler_thread = None
    
    def add_hourly_job(self, job_name: str, pipeline: DataIngestionPipeline):
        """Add hourly ingestion job."""
        schedule.every().hour.do(pipeline.scan_and_process_existing_files).tag(job_name)
        self.scheduled_jobs[job_name] = {
            'frequency': 'hourly',
            'pipeline': pipeline,
            'added_at': datetime.now()
        }
        logger.info(f"Added hourly job: {job_name}")
    
    def add_daily_job(self, job_name: str, pipeline: DataIngestionPipeline, 
                     time_str: str = "02:00"):
        """Add daily ingestion job."""
        schedule.every().day.at(time_str).do(
            pipeline.scan_and_process_existing_files
        ).tag(job_name)
        
        self.scheduled_jobs[job_name] = {
            'frequency': f'daily at {time_str}',
            'pipeline': pipeline,
            'added_at': datetime.now()
        }
        logger.info(f"Added daily job: {job_name} at {time_str}")
    
    def add_custom_job(self, job_name: str, pipeline: DataIngestionPipeline,
                      schedule_func: Callable):
        """Add custom scheduled job."""
        schedule_func().do(pipeline.scan_and_process_existing_files).tag(job_name)
        
        self.scheduled_jobs[job_name] = {
            'frequency': 'custom',
            'pipeline': pipeline,
            'added_at': datetime.now()
        }
        logger.info(f"Added custom job: {job_name}")
    
    def remove_job(self, job_name: str):
        """Remove a scheduled job."""
        schedule.clear(job_name)
        if job_name in self.scheduled_jobs:
            del self.scheduled_jobs[job_name]
        logger.info(f"Removed job: {job_name}")
    
    def start_scheduler(self):
        """Start the job scheduler."""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        def run_scheduler():
            self.is_running = True
            logger.info("Started job scheduler")
            
            while self.is_running:
                try:
                    schedule.run_pending()
                    time.sleep(60)  # Check every minute
                except Exception as e:
                    logger.error(f"Scheduler error: {e}")
                    time.sleep(60)
        
        self.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()
    
    def stop_scheduler(self):
        """Stop the job scheduler."""
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        logger.info("Stopped job scheduler")
    
    def get_next_run_times(self) -> Dict:
        """Get next run times for all jobs."""
        next_runs = {}
        
        for job in schedule.jobs:
            if hasattr(job, 'tags') and job.tags:
                job_name = list(job.tags)[0]
                next_runs[job_name] = {
                    'next_run': job.next_run.isoformat() if job.next_run else None,
                    'last_run': job.last_run.isoformat() if job.last_run else None
                }
        
        return next_runs
    
    def get_status(self) -> Dict:
        """Get scheduler status."""
        return {
            'is_running': self.is_running,
            'job_count': len(self.scheduled_jobs),
            'jobs': self.scheduled_jobs,
            'next_run_times': self.get_next_run_times()
        }
