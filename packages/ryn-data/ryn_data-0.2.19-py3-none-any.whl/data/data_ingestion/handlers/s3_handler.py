import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from aipmodel.model_registry import CephS3Manager
from fastapi import HTTPException

from data.data_ingestion.handlers.conditions import DatasetConditionChecker
from data.data_ingestion.models.metadata import DatasetMetadata
from data.data_ingestion.storage_handler import DatasetStorageHandler
from data.data_restructure.restructure import Restructurer
from data.data_validation.config import validation_config
from data.data_validation.structures import ValidationReport, ValidationResult
from data.data_validation.validation import DirectoryValidator

logger = logging.getLogger(__name__)

# Constants
ACCEPTABLE_DATASET_TYPES = {
    "text_generation",
    "image_segmentation",
    "image_classification",
}

USER_STORAGE_SIZE_LIMIT_BYTES = 50 * 1024**3  # 50 GB



class S3Handler:
    def __init__(
        self, *, access_key: str, secret_key: str, endpoint_url: str, bucket_name: str
    ):
        self.access_key = access_key
        self.secret_key = secret_key
        self.endpoint_url = endpoint_url
        self.bucket_name = bucket_name
        logger.info(
            f"S3Handler initialized for endpoint '{endpoint_url}' and bucket '{bucket_name}'."
        )

    def _log_event(
        self,
        level: int,
        message: Optional[str],
        category: str,
        event_type: str,
        status: str,
        base_extra: Dict[str, Any],
        additional_data: Dict[str, Any] = None,
        exc_info: bool = False,
    ):
        """Helper to handle structured logging to reduce code duplication."""
        extra = base_extra.copy()

        event_dict = {
            "category": category,
            "type": event_type,
            "status": status,
        }

        extra.update({"event": event_dict})

        if additional_data:
            extra.update(additional_data)

        if message:
            logger.log(level, message, exc_info=exc_info, extra=extra)
        else:
            # Sometimes we just want to log the event structure without a specific message
            logger.log(
                level,
                f"{category} - {event_type}: {status}",
                exc_info=exc_info,
                extra=extra,
            )

    def download_file(self, remote_path: str, local_path: Path, s3_client) -> None:
        """Standard Boto3 download (kept for compatibility/public interface)."""
        if not s3_client:
            raise HTTPException(status_code=503, detail="S3 service is not available.")
        try:
            local_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                s3_client.head_object(Bucket=self.bucket_name, Key=remote_path)
            except s3_client.exceptions.NoSuchKey:
                raise ValueError(
                    f"The file or folder '{remote_path}' does not exist in the S3 bucket '{self.bucket_name}'."
                )

            s3_client.download_file(self.bucket_name, remote_path, str(local_path))
            logger.info(
                f"S3 Download: '{remote_path}' -> '{local_path}' (bucket='{self.bucket_name}')"
            )
        except Exception as e:
            logger.error(
                f"S3 download failed for '{remote_path}' in bucket '{self.bucket_name}': {e}"
            )
            raise HTTPException(status_code=500, detail=f"S3 download error: {e}")

    @staticmethod
    def validate_dataset_structure(local_folder: Union[str, Path]) -> bool:
        """
        Validates that a directory has the required dataset structure.
        """
        root_path = Path(local_folder)

        if not root_path.is_dir():
            raise FileNotFoundError(f"Root directory not found: '{root_path}'")

        train_path = root_path / "train"
        if not train_path.is_dir():
            raise FileNotFoundError(
                f"Required 'train' split directory not found in '{root_path}'"
            )

        # Check if 'train' has at least one parquet file
        if not next(train_path.glob("*.parquet"), None):
            raise ValueError(
                "The 'train' split directory exists but contains no .parquet files."
            )

        # Check optional splits
        for split_name in ["test", "validation"]:
            split_path = root_path / split_name
            if split_path.is_dir():
                if not next(split_path.glob("*.parquet"), None):
                    raise ValueError(
                        f"The optional '{split_name}' split directory exists "
                        "but contains no .parquet files."
                    )

        print(f"✅ Validation successful for directory: '{root_path}'")
        return True

    def _validate_and_cleanup_dataset(
        self,
        local_file: Path,
        s3_file_path: str,
        base_extra: dict,
        is_soft: bool = True,
    ) -> Tuple[str, str, List[dict], List[dict]]:
        self._log_event(
            logging.INFO,
            f"Starting validation for dataset at: {local_file}",
            "validation",
            "start_validation",
            "success",
            base_extra,
        )

        validator = DirectoryValidator(config=validation_config, unzip_first=True)
        report = validator.validate(Path(local_file))

        if isinstance(report, ValidationResult):
            report = ValidationReport(directory_path=local_file, results=[report])

        error_details = []
        warning_details = []
        final_status = "success"
        final_message = "Dataset from S3 stored successfully."

        invalid_file_paths: Set[Path] = set()
        warning_file_paths: Set[Path] = set()

        if report.has_failures():
            final_status = "completed_with_errors"
            final_message = (
                "Dataset stored, but some files failed validation and were excluded."
            )

            for result in report.results:
                if not result.is_valid:
                    error_details.append(
                        {
                            "file": result.file_path,
                            "errors": result.errors,
                            "warnings": result.warnings,
                        }
                    )
                    invalid_file_paths.add(result.file_path)
                elif result.warnings:
                    warning_details.append(
                        {"warnings": result.warnings, "file": result.file_path}
                    )
                    warning_file_paths.add(result.file_path)

            logger.info(f"warning paths: {warning_file_paths}")

            count_to_remove = (
                len(invalid_file_paths)
                if is_soft
                else len(invalid_file_paths) + len(warning_file_paths)
            )
            logger.info(f"Removing {count_to_remove} invalid file(s)...")
            logger.info(f"errors: {error_details}")

            # Remove Errors
            for file_path in invalid_file_paths:
                try:
                    os.remove(file_path)
                    logger.debug(f"Removed invalid file: {file_path}")
                except OSError as e:
                    logger.error(f"Error removing invalid file {file_path}: {e}")

            # Remove Warnings (if hard validation)
            if not is_soft:
                for file_path in warning_file_paths:
                    try:
                        os.remove(file_path)
                        logger.debug(
                            f"Removed invalid file: {file_path} (hard validating)"
                        )
                    except OSError as e:
                        logger.error(f"Error removing invalid file {file_path}: {e}")

        # Final check if dataset is empty
        files = (
            [
                f
                for f in local_file.rglob("*")
                if f.is_file()
                and f.suffix in (".csv", ".parquet", ".jpg", ".png", ".json")
            ]
            if local_file.is_dir()
            else ([local_file] if local_file.exists() else [])
        )

        if not files:
            final_status = "failed"
            final_message = (
                "All files in the dataset failed validation. No files were stored."
            )
            logger.error(
                f"All files in dataset from S3 path '{s3_file_path}' failed validation. Nothing to store."
            )

        return final_status, final_message, error_details, warning_details

    def _download_dataset_ceph(
        self, s3_file_path: str, local_file: Path, base_extra: dict
    ) -> None:
        """Handles the download using CephS3Manager."""
        manager = CephS3Manager(
            endpoint_url=self.endpoint_url,
            access_key=self.access_key,
            secret_key=self.secret_key,
            bucket_name=self.bucket_name,
        )
        print("0" * 10)
        try:
            manager.download(s3_file_path, local_file)
        except Exception as e:
            self._log_event(
                logging.ERROR,
                f"error in downloading dataset from source s3 : {e}",
                "s3_handler",
                "s3_download",
                "failed",
                base_extra,
            )
            raise

        self._log_event(
            logging.INFO,
            "downloaded source s3 dataset successfully",
            "s3_handler",
            "s3_download",
            "success",
            base_extra,
        )

    def _process_restructuring(
        self,
        *,
        local_file: Path,
        dataset_type: str,
        temp_dir: Path,
        dataset_name: str,
        base_extra: dict,
    ) -> Tuple[Path, bool, dict]:
        """
        Handles the restructuring logic.
        Returns (current_local_file_path, restructure_success_bool).
        """
        result = {}

        if local_file.is_dir():
            restructurer = Restructurer(task_type=dataset_type)
            output_path = temp_dir / f"{local_file.stem}_restructured"

            result = restructurer.restructure(
                input_path=local_file,
                output_path=output_path,
            )

            if not result:
                self._log_event(
                    logging.ERROR,
                    "restructuring failed",
                    "restructure",
                    "restructure_result",
                    "failed",
                    base_extra,
                )
                raise HTTPException(
                    status_code=500, detail=f"restructure failed for {dataset_name}"
                )

            # Success
            return output_path, False, result

        return local_file, True, result

    def process_s3_dataset(
        self,
        s3_file_path: str,
        dataset_name: str,
        user_name: str,
        private: bool,
        dataset_type: str,
        base_extra: dict,
        restructure: bool,
        s3_config_target: dict = None,
        clearml_config: dict = None,
        tags: list = [],
        parent_id: Optional[str] = None
    ) -> dict:
        start_time = datetime.now(timezone.utc)

        try:
            # 1. Setup Storage & Pathing
            mount_dataset_name = dataset_name or Path(s3_file_path).stem
            storage_handler = DatasetStorageHandler(mount_dataset_name)
            print(f"storage_handler:{storage_handler}")

            estimated_size = DatasetConditionChecker().check_s3_size(
                access_key=self.access_key,
                secret_key=self.secret_key,
                endpoint_url=self.endpoint_url,
                bucket_name=self.bucket_name,
                s3_path=s3_file_path,
                size_limit_bytes=USER_STORAGE_SIZE_LIMIT_BYTES
            )

            temp_dir = storage_handler.temp_dir
            logger.info(f"Using S3-mounted temp directory: {temp_dir}")

            local_file = temp_dir / Path(s3_file_path).name
            logger.info(f"temp_dir: {temp_dir}")
            print(s3_file_path)

            # 2. Download
            self._download_dataset_ceph(s3_file_path, local_file, base_extra)

            # 3. Create ID and Log Metadata start
            dataset_id = storage_handler.generate_dataset_id()
            base_extra["dataset"] = base_extra.get("dataset", {})
            base_extra["dataset"]["id"] = dataset_id

            self._log_event(
                logging.INFO,
                "metadata object created",
                "s3_handler",
                "metadata",
                "success",
                base_extra,
            )

            # 4. Validation (if restructuring is enabled)
            validation_result_status = "failed"
            logger.info(f"restructure={restructure}")

            if restructure:
                is_soft = False
                final_status, _, error_details, warning_details = (
                    self._validate_and_cleanup_dataset(
                        local_file, s3_file_path, base_extra, is_soft=is_soft
                    )
                )

                # Construct complex validation result dict
                validation_results = {
                    "validation": {
                        "errors": [
                            {
                                "file": str(e["file"]).split("/")[-1],
                                "details": d["error"],
                                "removed": True,
                            }
                            for e in error_details
                            for d in e["errors"]
                        ],
                        "warnings": [
                            {
                                "file": str(w["file"]).split("/")[-1],
                                "details": d["warning"],
                                "removed": not is_soft,
                            }
                            for w in warning_details
                            for d in w["warnings"]
                        ],
                        "status": final_status,
                    }
                }

                if final_status == "failed":
                    self._log_event(
                        logging.ERROR,
                        "validation completely failed (all files removed)",
                        "validation",
                        "end_validation",
                        "failed",
                        base_extra,
                        additional_data=validation_results,
                    )
                    raise HTTPException(
                        status_code=500, detail="Validation failed completely"
                    )
                else:
                    self._log_event(
                        logging.INFO,
                        "validation ended",
                        "validation",
                        "end_validation",
                        "success",
                        base_extra,
                        additional_data=validation_results,
                    )

                validation_result_status = final_status

            # 5. Restructuring
            restructure_failed = False

            summary = {}

            is_acceptable = dataset_type in ACCEPTABLE_DATASET_TYPES

            if is_acceptable and restructure:
                local_file, restructure_failed, summary = self._process_restructuring(
                    local_file=local_file,
                    dataset_type=dataset_type,
                    temp_dir=temp_dir,
                    dataset_name=dataset_name,
                    base_extra=base_extra,
                )
            else:
                if not is_acceptable:
                    restructure_failed = True
                    logger.info(f"task {dataset_type} not supported")
                if not restructure:
                    restructure_failed = True
                    logger.info("restructure=False")

            summary["estimated_size_bytes"] = estimated_size


            # 6. Metadata Creation
            metadata = DatasetMetadata(
                dataset_id=dataset_id,
                dataset_name=dataset_name or local_file.stem,
                revision="main",
                last_commit=None,
                last_modified=None,
                user_name=user_name,
                private=private,
                source="s3",
                created_at=datetime.now().isoformat(),
                s3_path="",
                summary=summary,
                dataset_type=dataset_type or "ML",
                restructure_valid=not restructure_failed,
                validation=(validation_result_status != "failed"),
                tags=tags,
            )

            # 7. Store Dataset
            files_to_upload = (
                [f.name for f in local_file.rglob("*") if f.is_file()]
                if local_file.is_dir()
                else [local_file.name]
            )
            logger.info(f"uploading {len(files_to_upload)} files: {files_to_upload}")

            try:
                stored_path = storage_handler.store_dataset(
                    local_file,
                    metadata,
                    s3_config=s3_config_target,
                    clearml_config=clearml_config,
                )
            except Exception as e:
                self._log_event(
                    logging.ERROR,
                    f"error in saving s3 dataset: {e}",
                    "s3_handler",
                    "error_saving",
                    "failed",
                    base_extra,
                )
                # Note: Original code logs error but doesn't raise, however `stored_path` would be undefined.
                # Assuming standard error flow is needed or to mirror strict behavior:
                # The original code's try/except wraps the storage call, logs error, then proceeds to use `stored_path`
                # which causes UnboundLocalError. I will treat this as a flow that stops here.
                raise

            self._log_event(
                logging.INFO,
                None,
                "store_dataset",
                "end_storing",
                "success",
                base_extra,
            )

            return {
                "status": "success",
                "dataset_id": dataset_id,
                "stored_path": stored_path,
                "metadata": metadata.model_dump()
            }

        except Exception as e:
            # Duration calculation in Exception block
            duration_ms = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds() * 1000

            fail_event_data = {
                "category": "process",
                "type": "s3_processing_failed",
                "status": "failure",
                "duration": int(duration_ms),
            }

            # Construct extra locally to handle trace info if available
            fail_extra = base_extra.copy()
            fail_extra["event"] = fail_event_data
            job_id = fail_extra.get("trace", {}).get("job_id", "unknown")

            logger.error(
                f"Failed to process S3 dataset for job {job_id}",
                exc_info=True,
                extra=fail_extra,
            )

            if not isinstance(e, HTTPException):
                raise HTTPException(status_code=500, detail=str(e))
            raise

        finally:
            # Duration calculation in Finally block
            duration_ms = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds() * 1000

            end_event_data = {
                "category": "process",
                "type": "s3_processing_finished",
                "status": "success",
                "duration": int(duration_ms),
            }

            end_extra = base_extra.copy()
            end_extra["event"] = end_event_data
            job_id = end_extra.get("trace", {}).get("job_id", "unknown")

            logger.info(
                f"Finished processing S3 dataset for job {job_id}", extra=end_extra
            )
