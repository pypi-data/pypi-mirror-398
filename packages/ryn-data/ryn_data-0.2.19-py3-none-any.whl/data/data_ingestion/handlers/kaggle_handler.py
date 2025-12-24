import os
from pathlib import Path
from fastapi import HTTPException
from datetime import datetime
import kagglehub
import logging

from data.data_ingestion.models.metadata import DatasetMetadata
from data.data_ingestion.models.requests import KaggleDownloadRequest
from data.data_ingestion.handlers.utils import summarize_dataset
from data.data_ingestion.storage_handler import DatasetStorageHandler

logger = logging.getLogger(__name__)

def process_kaggle_dataset(request: KaggleDownloadRequest) -> dict:
    """
    Download a Kaggle dataset, persist it to S3-mounted temp directory, and return metadata.
    """
    original_kaggle_user = os.environ.get("KAGGLE_USERNAME")
    original_kaggle_key = os.environ.get("KAGGLE_KEY")

    try:
        mount_dataset_name = request.dataset_name or request.dataset_id.replace('/', '-')
        storage_handler = DatasetStorageHandler(mount_dataset_name)

        if request.kaggle_username and request.kaggle_key:
            logger.info("Using Kaggle credentials from request.")
            os.environ["KAGGLE_USERNAME"] = request.kaggle_username
            os.environ["KAGGLE_KEY"] = request.kaggle_key
        elif not (original_kaggle_user and original_kaggle_key):
            raise HTTPException(
                status_code=400,
                detail="Missing Kaggle credentials. Provide them in the request or set them in environment variables."
            )

        temp_dir = storage_handler.temp_dir
        logger.info(f"Using S3-mounted temp directory: {temp_dir}")

        logger.info(f"Downloading Kaggle dataset: {request.dataset_id}")
        download_path = Path(kagglehub.dataset_download(request.dataset_id, path=str(temp_dir)))

        dataset_id = storage_handler.generate_dataset_id()
        metadata = DatasetMetadata(
            dataset_id=dataset_id,
            dataset_name=request.dataset_name or request.dataset_id.replace("/", "_"),
            dataset_config=None,
            last_commit=None,
            last_modified=None,
            user_name=request.user_name,
            private=request.private,
            source="kaggle",
            created_at=datetime.now().isoformat(),
            file_path="",
            summary=summarize_dataset(download_path)
        )

        stored_path = storage_handler.store_dataset(download_path, metadata)

        return {
            "status": "success",
            "message": f"Kaggle dataset '{request.dataset_id}' stored.",
            "dataset_id": dataset_id,
            "stored_path": stored_path,
        }
    except Exception as e:
        logger.error(f"Error processing Kaggle dataset '{request.dataset_id}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Kaggle dataset error: {e}")
    finally:
        if original_kaggle_user:
            os.environ["KAGGLE_USERNAME"] = original_kaggle_user
        elif "KAGGLE_USERNAME" in os.environ:
            del os.environ["KAGGLE_USERNAME"]

        if original_kaggle_key:
            os.environ["KAGGLE_KEY"] = original_kaggle_key
        elif "KAGGLE_KEY" in os.environ:
            del os.environ["KAGGLE_KEY"]

        # storage_handler.unmount()