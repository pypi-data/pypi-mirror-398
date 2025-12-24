import openml
from datasets import get_dataset_infos
from fastapi import HTTPException
import logging
import boto3
from botocore.exceptions import ClientError
from pathlib import Path
logger = logging.getLogger(__name__)

class DatasetConditionChecker:
    def has_enough_space(self, size_mbytes: int,size_limit_mb: float, buffer_ratio: float = 1.2) -> bool:
        """Check if there's enough available disk space with a buffer."""
        # total, used, free = shutil.disk_usage("/")
        free = size_limit_mb
        logger.info(f"dataset size: {size_mbytes} mega bytes")
        logger.info(f"Available free disk space: {free} mega bytes")
        return free >= size_mbytes * buffer_ratio , free

    def dir_size_mb(self,dir_path):
        return sum(f.stat().st_size for f in Path(dir_path).rglob('*') if f.is_file()) / (1024 * 1024)
    def check_huggingface_size(self,*,dataset_name: str,size_limit_bytes: float,revision: str = "main"):
        """
        Check if there is enough disk space for a specific revision of a Hugging Face dataset.

        Args:
            dataset_name (str): The name of the dataset on the Hugging Face Hub.
            dataset_config (str, optional): The configuration or subset of the dataset.
            revision (str, optional): The git revision (branch, tag, or commit hash) to check. Defaults to "main".
        """

        try:
            # Pass the revision parameter to get info for the specific version
            infos = get_dataset_infos(dataset_name, revision=revision)
        except Exception as e:
            # Handle cases where the dataset or revision might not exist
            logger.error(f"Could not retrieve dataset info for '{dataset_name}' at revision '{revision}': {e}")
            raise HTTPException(
                status_code=404,
                detail=f"Could not find or access dataset '{dataset_name}' at revision '{revision}'."
            )

        # The rest of the logic can remain largely the same
        total_size_bytes = 0
        config_sizes = {}

        for config_name, info in infos.items():
        # Try to get dataset_size, size_in_bytes, or download_size
            size = (
                getattr(info, "dataset_size", 0)
                or getattr(info, "size_in_bytes", 0)
                or getattr(info, "download_size", 0)
            )
            if size == 0 or size is None:
                print(f"No size information available for config '{config_name}' in dataset '{dataset_name}'")
                return size
            else:
                config_sizes[config_name] = {
                    "size_bytes": size,
                    "size_mb": size / (1024 ** 2) if size > 0 else 0
                }
                total_size_bytes += size

        estimated_size = total_size_bytes

        if estimated_size > 0:
            has_space, free_space = self.has_enough_space(estimated_size/(1024 ** 2),size_limit_bytes/(1024**2))
            if not has_space:
                # Use the buffered required size for the error message
                required_size_mb = (estimated_size * 1.2) / (1024 ** 2)
                free_space_mb = free_space
                
                message = (
                    f"Not enough disk space for dataset '{dataset_name}' (revision: {revision}). "
                    f"Required: ~{required_size_mb:.2f} MB, Available: {free_space_mb:.2f} MB"
                )
                logger.warning(message)
                raise HTTPException(status_code=507, detail=message)
            else:
                return estimated_size
        else:
            # This branch is now more critical, as some datasets might not have size info.
            
            message = f"Could not estimate size for dataset '{dataset_name}' (revision: {revision}). Proceeding with download might fail."
            logger.warning(message)
            # Depending on your policy, you might remove this HTTPException to allow proceeding with caution.
            # For now, keeping it as it was in the original code.
            raise HTTPException(
                status_code=400,
                detail=f"Unable to estimate size for dataset '{dataset_name}' at revision '{revision}'"
            )
        
    def check_openml_size(self, dataset_id: int):
        """Check if there is enough disk space for the OpenML dataset."""
        dataset = openml.datasets.get_dataset(dataset_id, download_data=False, download_qualities=True)
        instances = dataset.qualities.get("NumberOfInstances", 0)
        features = dataset.qualities.get("NumberOfFeatures", 0)

        max_bytes_per_value = 100  # Conservative estimate
        estimated_size = instances * features * max_bytes_per_value

        if estimated_size > 0:
            has_space, free_space = self.has_enough_space(estimated_size)
            if not has_space:
                required_size = estimated_size * 1.1  # Apply buffer for logging
                logger.warning(
                    f"Not enough disk space for OpenML dataset ID '{dataset_id}'. "
                    f"Required: {required_size / (1024 ** 2):.3f} MB, Available: {free_space / (1024 ** 2):.3f} MB"
                )
                raise HTTPException(
                    status_code=507,
                    detail=(
                        f"Not enough disk space for OpenML dataset ID '{dataset_id}'. "
                        f"Required: {required_size / (1024 ** 2):.3f} MB, Available: {free_space / (1024 ** 2)} MB"
                    )
                )
        else:
            logger.warning(f"Could not estimate size for OpenML dataset ID '{dataset_id}'")
            raise HTTPException(
                status_code=400,
                detail=f"Unable to estimate size for OpenML dataset ID '{dataset_id}'"
            )
    def check_s3_size(self, *, access_key: str, secret_key: str, endpoint_url: str, bucket_name: str, s3_path: str,size_limit_bytes: float) -> None:
        """Check if there is enough disk space for the S3 dataset."""
        # Validate inputs
        logger.debug(f"check_s3_size inputs: access_key={access_key}, secret_key=****, endpoint_url={endpoint_url}, "
                     f"bucket_name={bucket_name}, s3_path={s3_path}, types={[type(x).__name__ for x in [access_key, secret_key, endpoint_url, bucket_name, s3_path]]}")
        
        # Validate inputs
        if not all(isinstance(x, str) for x in [access_key, secret_key, endpoint_url, bucket_name, s3_path]):
            raise HTTPException(
                status_code=400,
               
                detail=f"All S3 parameters must be strings. Received types: "
                       f"access_key={type(access_key).__name__}, secret_key={type(secret_key).__name__}, "
                       f"endpoint_url={type(endpoint_url).__name__}, bucket_name={type(bucket_name).__name__}, "
                       f"s3_path={type(s3_path).__name__}"
            )
        if not bucket_name:
            raise HTTPException(status_code=400, detail="S3 bucket name cannot be empty")
  
        try:
            s3 = boto3.client(
                's3',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                endpoint_url=endpoint_url,
            )
            
            # try:
            #     s3.head_object(Bucket=bucket_name, Key=s3_path)  
            # except s3.exceptions.NoSuchKey:
            #     raise ValueError(f"The file or folder '{s3_path}' does not exist in the S3 bucket '{self.bucket_name}'.")
        

            total_size = 0
            paginator = s3.get_paginator('list_objects_v2')
            logger.info(f"started checking s3 size{s3_path},{bucket_name}")
            pages = paginator.paginate(Bucket=bucket_name, Prefix=s3_path)

            for page in pages:
                contents = page.get('Contents', [])
                for obj in contents:
                    total_size += obj['Size']

            if total_size > 0:
                has_space, free_space = self.has_enough_space(total_size/(1024**2),size_limit_mb=size_limit_bytes/(1024**2))
                logger.info(f"Estimated S3 size for path '{s3_path}' is {total_size / (1024 ** 2):.2f} MB")
                if not has_space:
                    required_size = total_size * 1.1  # Use 1.1 buffer as in your code
                    logger.warning(
                        f"Not enough disk space for S3 dataset at '{bucket_name}/{s3_path}'. "
                        f"Required: {required_size / (1024 ** 2):.2f} MB, Available: {free_space :.2f} MB"
                    )
                    raise HTTPException(
                        status_code=507,
                        detail=(
                            f"Not enough disk space for S3 dataset at '{bucket_name}/{s3_path}'. "
                            f"Required: {required_size / (1024 ** 2):.2f} MB, Available: {free_space:.2f} MB"
                        )
                    )
            else:
                logger.warning(f"Wrong or emplty s3 path:' {bucket_name}/{s3_path}'")
                raise HTTPException(
                    status_code=400,
                    detail=f"Wrong or empty S3 path: at '{bucket_name}/{s3_path}'"
                )

            return total_size
        except ClientError as e:
            logger.error(f"Error accessing S3 bucket '{bucket_name}/{s3_path}': {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Failed to access S3 bucket '{bucket_name}/{s3_path}': {str(e)}"
            )
