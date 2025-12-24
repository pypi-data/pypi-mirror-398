"""
AWS integration for cloud-based soil moisture processing.
"""

import os
import json
from typing import Dict, List, Optional, Union, Any
from pathlib import Path
import logging
from datetime import datetime, timedelta
import tempfile

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class AWSProcessor:
    """
    AWS cloud processing integration for soil moisture analysis.
    """
    
    def __init__(self, region_name: str = 'us-east-1'):
        if not BOTO3_AVAILABLE:
            raise ImportError("boto3 is required for AWS integration. Install with: pip install boto3")
        
        self.region_name = region_name
        self.session = boto3.Session()
        
        # Initialize AWS services
        try:
            self.s3_client = self.session.client('s3', region_name=region_name)
            self.batch_client = self.session.client('batch', region_name=region_name)
            self.lambda_client = self.session.client('lambda', region_name=region_name)
            self.ec2_client = self.session.client('ec2', region_name=region_name)
        except NoCredentialsError:
            logger.error("AWS credentials not found. Please configure AWS credentials.")
            raise
    
    def submit_batch_job(self, job_definition: str, job_queue: str, 
                        job_name: str, parameters: Dict[str, Any]) -> str:
        """
        Submit a batch processing job to AWS Batch.
        
        Args:
            job_definition: AWS Batch job definition name
            job_queue: AWS Batch job queue name
            job_name: Name for this job
            parameters: Job parameters
            
        Returns:
            Job ID
        """
        try:
            response = self.batch_client.submit_job(
                jobName=job_name,
                jobQueue=job_queue,
                jobDefinition=job_definition,
                parameters=parameters
            )
            
            job_id = response['jobId']
            logger.info(f"Submitted batch job {job_name} with ID: {job_id}")
            
            return job_id
            
        except ClientError as e:
            logger.error(f"Failed to submit batch job: {e}")
            raise
    
    def get_batch_job_status(self, job_id: str) -> Dict:
        """
        Get the status of a batch job.
        
        Args:
            job_id: AWS Batch job ID
            
        Returns:
            Job status information
        """
        try:
            response = self.batch_client.describe_jobs(jobs=[job_id])
            
            if not response['jobs']:
                raise ValueError(f"Job {job_id} not found")
            
            job = response['jobs'][0]
            
            return {
                'job_id': job_id,
                'job_name': job['jobName'],
                'status': job['status'],
                'created_at': job.get('createdAt'),
                'started_at': job.get('startedAt'),
                'stopped_at': job.get('stoppedAt'),
                'exit_code': job.get('attempts', [{}])[0].get('exitCode'),
                'status_reason': job.get('statusReason')
            }
            
        except ClientError as e:
            logger.error(f"Failed to get job status: {e}")
            raise
    
    def invoke_lambda_function(self, function_name: str, payload: Dict) -> Dict:
        """
        Invoke an AWS Lambda function for processing.
        
        Args:
            function_name: Lambda function name
            payload: Function payload
            
        Returns:
            Function response
        """
        try:
            response = self.lambda_client.invoke(
                FunctionName=function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            result = json.loads(response['Payload'].read())
            
            if response.get('FunctionError'):
                logger.error(f"Lambda function error: {result}")
                raise Exception(f"Lambda function failed: {result}")
            
            return result
            
        except ClientError as e:
            logger.error(f"Failed to invoke Lambda function: {e}")
            raise
    
    def create_processing_cluster(self, cluster_config: Dict) -> str:
        """
        Create an EC2 processing cluster for large-scale analysis.
        
        Args:
            cluster_config: Cluster configuration
            
        Returns:
            Cluster identifier
        """
        # This is a simplified example - in practice you'd use services like
        # AWS Batch, EKS, or ECS for managed clusters
        
        try:
            # Launch EC2 instances
            response = self.ec2_client.run_instances(
                ImageId=cluster_config.get('ami_id', 'ami-0abcdef1234567890'),
                MinCount=cluster_config.get('min_instances', 1),
                MaxCount=cluster_config.get('max_instances', 4),
                InstanceType=cluster_config.get('instance_type', 't3.medium'),
                KeyName=cluster_config.get('key_name'),
                SecurityGroupIds=cluster_config.get('security_groups', []),
                SubnetId=cluster_config.get('subnet_id'),
                UserData=cluster_config.get('user_data', ''),
                TagSpecifications=[
                    {
                        'ResourceType': 'instance',
                        'Tags': [
                            {'Key': 'Name', 'Value': 'SoilMoistureProcessor'},
                            {'Key': 'Project', 'Value': 'SoilMoistureAnalysis'}
                        ]
                    }
                ]
            )
            
            instance_ids = [instance['InstanceId'] for instance in response['Instances']]
            logger.info(f"Created processing cluster with instances: {instance_ids}")
            
            return json.dumps({
                'cluster_id': f"cluster_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'instance_ids': instance_ids,
                'region': self.region_name
            })
            
        except ClientError as e:
            logger.error(f"Failed to create processing cluster: {e}")
            raise


class S3DataManager:
    """
    Manage soil moisture data storage in AWS S3.
    """
    
    def __init__(self, bucket_name: str, region_name: str = 'us-east-1'):
        if not BOTO3_AVAILABLE:
            raise ImportError("boto3 is required for S3 integration")
        
        self.bucket_name = bucket_name
        self.region_name = region_name
        self.s3_client = boto3.client('s3', region_name=region_name)
        self.s3_resource = boto3.resource('s3', region_name=region_name)
        
        # Verify bucket exists
        try:
            self.s3_client.head_bucket(Bucket=bucket_name)
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                logger.warning(f"Bucket {bucket_name} not found")
            else:
                logger.error(f"Error accessing bucket {bucket_name}: {e}")
    
    def upload_file(self, local_file_path: Union[str, Path], 
                   s3_key: str, metadata: Optional[Dict] = None) -> bool:
        """
        Upload a file to S3.
        
        Args:
            local_file_path: Local file path
            s3_key: S3 object key
            metadata: Optional metadata
            
        Returns:
            True if successful
        """
        try:
            extra_args = {}
            if metadata:
                extra_args['Metadata'] = metadata
            
            self.s3_client.upload_file(
                str(local_file_path), 
                self.bucket_name, 
                s3_key, 
                ExtraArgs=extra_args
            )
            
            logger.info(f"Uploaded {local_file_path} to s3://{self.bucket_name}/{s3_key}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to upload file: {e}")
            return False
    
    def download_file(self, s3_key: str, 
                     local_file_path: Union[str, Path]) -> bool:
        """
        Download a file from S3.
        
        Args:
            s3_key: S3 object key
            local_file_path: Local file path to save to
            
        Returns:
            True if successful
        """
        try:
            self.s3_client.download_file(
                self.bucket_name, 
                s3_key, 
                str(local_file_path)
            )
            
            logger.info(f"Downloaded s3://{self.bucket_name}/{s3_key} to {local_file_path}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to download file: {e}")
            return False
    
    def list_files(self, prefix: str = '', 
                  file_extension: Optional[str] = None) -> List[Dict]:
        """
        List files in S3 bucket.
        
        Args:
            prefix: S3 key prefix to filter by
            file_extension: File extension to filter by
            
        Returns:
            List of file information dictionaries
        """
        try:
            paginator = self.s3_client.get_paginator('list_objects_v2')
            
            page_iterator = paginator.paginate(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            files = []
            for page in page_iterator:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        key = obj['Key']
                        
                        # Filter by file extension if specified
                        if file_extension and not key.endswith(file_extension):
                            continue
                        
                        files.append({
                            'key': key,
                            'size': obj['Size'],
                            'last_modified': obj['LastModified'],
                            'etag': obj['ETag'].strip('"'),
                            'storage_class': obj.get('StorageClass', 'STANDARD')
                        })
            
            logger.info(f"Found {len(files)} files with prefix '{prefix}'")
            return files
            
        except ClientError as e:
            logger.error(f"Failed to list files: {e}")
            return []
    
    def upload_dataframe(self, df: pd.DataFrame, s3_key: str, 
                        format: str = 'csv') -> bool:
        """
        Upload a pandas DataFrame to S3.
        
        Args:
            df: DataFrame to upload
            s3_key: S3 object key
            format: File format ('csv', 'parquet', 'json')
            
        Returns:
            True if successful
        """
        try:
            with tempfile.NamedTemporaryFile(mode='w+b', delete=False) as tmp_file:
                if format == 'csv':
                    df.to_csv(tmp_file.name, index=False)
                elif format == 'parquet':
                    df.to_parquet(tmp_file.name, index=False)
                elif format == 'json':
                    df.to_json(tmp_file.name, orient='records', date_format='iso')
                else:
                    raise ValueError(f"Unsupported format: {format}")
                
                # Upload the temporary file
                success = self.upload_file(tmp_file.name, s3_key)
                
                # Clean up
                os.unlink(tmp_file.name)
                
                return success
                
        except Exception as e:
            logger.error(f"Failed to upload DataFrame: {e}")
            return False
    
    def download_dataframe(self, s3_key: str, 
                          format: str = 'csv') -> Optional[pd.DataFrame]:
        """
        Download a DataFrame from S3.
        
        Args:
            s3_key: S3 object key
            format: File format ('csv', 'parquet', 'json')
            
        Returns:
            DataFrame or None if failed
        """
        try:
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                if not self.download_file(s3_key, tmp_file.name):
                    return None
                
                if format == 'csv':
                    df = pd.read_csv(tmp_file.name)
                elif format == 'parquet':
                    df = pd.read_parquet(tmp_file.name)
                elif format == 'json':
                    df = pd.read_json(tmp_file.name, orient='records')
                else:
                    raise ValueError(f"Unsupported format: {format}")
                
                # Clean up
                os.unlink(tmp_file.name)
                
                return df
                
        except Exception as e:
            logger.error(f"Failed to download DataFrame: {e}")
            return None
    
    def create_data_lake_structure(self) -> bool:
        """
        Create a standard data lake structure for soil moisture data.
        
        Returns:
            True if successful
        """
        try:
            # Create folder structure
            folders = [
                'raw-data/satellite/amsr2/',
                'raw-data/satellite/smap/',
                'raw-data/satellite/smos/',
                'raw-data/insitu/',
                'processed-data/daily/',
                'processed-data/monthly/',
                'processed-data/climatology/',
                'models/trained/',
                'models/predictions/',
                'analysis/anomalies/',
                'analysis/trends/',
                'reports/daily/',
                'reports/monthly/'
            ]
            
            for folder in folders:
                # Create empty file to establish folder
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=f"{folder}.gitkeep",
                    Body=b"# This file ensures the folder structure exists\n"
                )
            
            logger.info("Created data lake structure in S3")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to create data lake structure: {e}")
            return False
    
    def get_storage_costs(self) -> Dict:
        """
        Estimate storage costs for S3 bucket.
        
        Returns:
            Dictionary with cost estimates
        """
        try:
            # Get bucket size and object count
            total_size = 0
            object_count = 0
            storage_classes = {}
            
            paginator = self.s3_client.get_paginator('list_objects_v2')
            for page in paginator.paginate(Bucket=self.bucket_name):
                if 'Contents' in page:
                    for obj in page['Contents']:
                        total_size += obj['Size']
                        object_count += 1
                        
                        storage_class = obj.get('StorageClass', 'STANDARD')
                        storage_classes[storage_class] = storage_classes.get(storage_class, 0) + 1
            
            # Convert to GB
            total_size_gb = total_size / (1024**3)
            
            # Rough cost estimates (USD per month, varies by region)
            cost_estimates = {
                'STANDARD': 0.023,      # per GB/month
                'STANDARD_IA': 0.0125,  # per GB/month
                'GLACIER': 0.004,       # per GB/month
                'DEEP_ARCHIVE': 0.00099 # per GB/month
            }
            
            estimated_monthly_cost = sum(
                (storage_classes.get(storage_class, 0) / object_count * total_size_gb) * cost
                for storage_class, cost in cost_estimates.items()
                if storage_classes.get(storage_class, 0) > 0
            )
            
            return {
                'total_size_gb': round(total_size_gb, 2),
                'object_count': object_count,
                'storage_classes': storage_classes,
                'estimated_monthly_cost_usd': round(estimated_monthly_cost, 2)
            }
            
        except ClientError as e:
            logger.error(f"Failed to get storage costs: {e}")
            return {}
