# s3_sdk.py

import hashlib
import json
import math
import os
import sys
import threading
from typing import Dict, Optional
import time  # Added for ETA calculation
from contextlib import contextmanager

import boto3
from boto3.s3.transfer import TransferConfig
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError

from clearml import Dataset

@contextmanager
def clearml_client_session(credentials: dict, log_extra={}):
    """
    A context manager that creates an explicit, isolated ClearML Session and APIClient
    based on the provided user credentials.
    """
    # 1. Create the explicit Session object with credentials
    try:
        from clearml.backend_api.session import Session

        Session(
        api_key=credentials.get("access_key"),
        secret_key=credentials.get("secret_key"),
        # You might need to specify the api_server if not using the default
        # host="https://api.clear.ml"
        )
    
        # Task.set_credentials(
        #     key=credentials.get("access_key"),
        #     secret=credentials.get("secret_key"),
        #     api_host="http://144.172.105.98:30003",
        # )
    except Exception as e:
        print(e)
        print("authorization failed", extra=log_extra)
        raise

    try:
        # 3. Yield the fully configured client for the 'with' block to use
        yield
    finally:
        print("ClearML session restored and client cleaned up.")

class ProgressPercentage:
    """A thread-safe progress callback for Boto3 uploads with ETA."""

    def __init__(self, filename: str, size: int, initial_bytes: int = 0):
        self._filename = os.path.basename(filename)
        self._size = float(size)
        self._seen_so_far = float(initial_bytes)
        self._lock = threading.Lock()
        self._start_time = time.time()
        self._initial_bytes = float(initial_bytes)  # Store initial offset for rate calculation

        if self._seen_so_far > 0:
            self.__call__(0)  # Immediately display resume progress

    @staticmethod
    def _format_time(seconds: float) -> str:
        """Formats seconds into HH:MM:SS or MM:SS."""
        if seconds < 0 or not math.isfinite(seconds):
            return "--:--"
        
        seconds = int(seconds)
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"

    def __call__(self, bytes_amount: int):
        with self._lock:
            self._seen_so_far += bytes_amount
            # Clamp the value to the file size to prevent > 100% display
            self._seen_so_far = min(self._seen_so_far, self._size)
            percentage = (self._seen_so_far / self._size) * 100

            elapsed_time = time.time() - self._start_time
            bytes_this_session = self._seen_so_far - self._initial_bytes
            
            speed_str = "0.00 MB/s"
            eta_str = "--:--"

            if elapsed_time > 0 and bytes_this_session > 0:
                rate = bytes_this_session / elapsed_time  # bytes/sec
                speed_mbps = rate / 1024 / 1024
                speed_str = f"{speed_mbps:.2f} MB/s"

                remaining_bytes = self._size - self._seen_so_far
                if rate > 0:
                    eta_seconds = remaining_bytes / rate
                    eta_str = self._format_time(eta_seconds)

            progress_line = (
                f"\r  ↳  Uploading {self._filename} ... "
                f"{self._seen_so_far / 1024 / 1024:.2f}MB / {self._size / 1024 / 1024:.2f}MB "
                f"({percentage:.2f}%) [{speed_str} | ETA: {eta_str}]  "
            )
            
            sys.stdout.write(progress_line)
            sys.stdout.flush()

            if self._seen_so_far >= self._size:
                # Overwrite the final line with a clean "Done" message
                done_line = (
                    f"\r  ↳  Uploading {self._filename} ... "
                    f"{self._size / 1024 / 1024:.2f}MB / {self._size / 1024 / 1024:.2f}MB "
                    f"(100.00%) [Done]                        \n"
                )
                sys.stdout.write(done_line)

class S3Uploader:
    """An SDK for robust, resumable file uploads to S3-compatible storage."""

    SYNC_MODES = {"OVERWRITE", "SKIP", "SYNC"}

    def __init__(
        self,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        region_name: str = None,
        endpoint_url: str = None,
        clearml_access_key: str = None,
        clearml_secret_key: str = None,
        clearml_save: bool = True,
        dataset_name: str = "default",
        verbose: bool = False,
    ):
        if not region_name and not endpoint_url:
            raise ValueError("You must provide either 'region_name' or 'endpoint_url'.")

        self.verbose = verbose
        self.dataset_name = dataset_name
        self.clearml_save = clearml_save
        try:
            client_kwargs = {
                "aws_access_key_id": aws_access_key_id,
                "aws_secret_access_key": aws_secret_access_key,
            }
            if region_name:
                client_kwargs["region_name"] = region_name
            if endpoint_url:
                client_kwargs["endpoint_url"] = endpoint_url

            self.clearml_credentials = {}
            if self.clearml_save:
                self.clearml_credentials["access_key"] = clearml_access_key
                self.clearml_credentials["secret_key"] = clearml_secret_key


            self.s3_client = boto3.client("s3", **client_kwargs)
            self.s3_client.list_buckets()  # Verify credentials

            target = endpoint_url or f"AWS Region '{region_name}'"
            print(f"✅ Connection successful to: {target}")

        except (NoCredentialsError, PartialCredentialsError) as e:
            raise ConnectionError("AWS credentials not found or incomplete.") from e
        except ClientError as e:
            if e.response["Error"]["Code"] in [
                "InvalidClientTokenId",
                "SignatureDoesNotMatch",
            ]:
                raise ValueError("Invalid AWS credentials provided.") from e
            raise ConnectionError(f"An AWS client error occurred: {e}") from e
        except Exception as e:
            raise ConnectionError(f"An unexpected error occurred: {e}") from e

    def upload_folder(
        self,
        local_folder_path: str,
        bucket_name: str,
        s3_folder_prefix: str = "",
        sync_mode: str = "SKIP",
        transfer_config: TransferConfig = None,
    ):
        """Uploads a local folder to an S3 bucket, respecting the sync mode."""
        print(
            f"\n Starting upload of '{local_folder_path}' to '{bucket_name}' (Mode: {sync_mode.upper()})..."
        )
        if sync_mode not in self.SYNC_MODES:
            raise ValueError(
                f"Invalid sync_mode '{sync_mode}'. Must be one of {self.SYNC_MODES}"
            )
        if not os.path.isdir(local_folder_path):
            print(f"❌ Error: Local folder not found at '{local_folder_path}'")
            return

        files_to_process = self._get_files_in_folder(local_folder_path)
        print(f"Found {len(files_to_process)} files to process.")

        summary = {"uploaded": 0, "skipped": 0, "failed": 0}

        for local_path in files_to_process:
            relative_path = os.path.relpath(local_path, local_folder_path)
            s3_key = os.path.join(s3_folder_prefix, relative_path).replace("\\", "/")

            if sync_mode != "OVERWRITE" and self._is_file_synced(
                local_path, bucket_name, s3_key, sync_mode
            ):
                summary["skipped"] += 1
                continue

            success = self.upload_file(local_path, bucket_name, s3_key, transfer_config)
            summary["uploaded" if success else "failed"] += 1

        print("\nS3 Upload complete!")

        if self.clearml_save:

            with clearml_client_session(self.clearml_credentials):

                print("Creating ClearML dataset...")
                dataset = Dataset.create(
                    dataset_name=self.dataset_name,
                    dataset_project=f"localupload_{self.dataset_name}",
                    description="Dataset uploaded from local",
                    # output_uri=s3_main_path
                )

                # Use ClearML's S3 configuration to point to the external data
                dataset.add_external_files(
                    source_url=local_folder_path, dataset_path=self.dataset_name
                )
                s3_path = "s3://"+bucket_name+"/"+s3_folder_prefix

                dataset.add_tags(
                    [f"s3_path:{s3_path}"]
                )

                dataset.upload()
                dataset.finalize()
        print(f"Total files processed: {len(files_to_process)}")
        print(f"✅ Successfully uploaded: {summary['uploaded']}")
        print(f"⏭️  Skipped (already synced): {summary['skipped']}")
        if summary["failed"] > 0:
            print(f"❌ Failed: {summary['failed']}")

    def upload_file(
        self,
        local_path: str,
        bucket_name: str,
        s3_key: str,
        transfer_config: TransferConfig = None,
    ) -> bool:
        """
        Uploads a single file, automatically choosing between standard and
        resumable multipart upload based on file size.
        """
        if not os.path.exists(local_path):
            print(f"\n  ❌ Error: File not found at {local_path}")
            return False

        config = transfer_config or TransferConfig(
            multipart_threshold=100 * 1024 * 1024,
            max_concurrency=10,
            multipart_chunksize=16 * 1024 * 1024,
            use_threads=True,
        )

        file_size = os.path.getsize(local_path)

        if file_size < config.multipart_threshold:
            return self._perform_standard_upload(
                local_path, bucket_name, s3_key, config
            )
        else:
            return self._perform_multipart_upload(
                local_path, bucket_name, s3_key, config
            )

    # --- Internal Helper Methods ---

    def _perform_standard_upload(self, local_path, bucket, key, config) -> bool:
        """Handles the upload of a small file."""
        print(f"  ⬆️  Queueing for standard upload: {local_path}")
        file_size = os.path.getsize(local_path)
        file_md5 = self._calculate_md5(local_path)
        extra_args = {"Metadata": {"md5": file_md5}}
        progress = ProgressPercentage(local_path, file_size)
        try:
            self.s3_client.upload_file(
                local_path,
                bucket,
                key,
                Config=config,
                Callback=progress,
                ExtraArgs=extra_args,
            )
            return True
        except ClientError as e:
            print(f"\n  ❌ Error uploading {local_path}: {e}")
            return False

    def _perform_multipart_upload(self, local_path, bucket, key, config) -> bool:
        """Handles the resumable multipart upload of a large file."""
        print(f"  ⬆️  Queueing for resumable multipart upload: {local_path}")
        file_size = os.path.getsize(local_path)
        cache_path = self._get_cache_path(local_path)
        cache = self._load_resume_cache(cache_path, local_path, bucket, key)

        upload_id, uploaded_parts = self._get_or_create_multipart_upload(
            cache, local_path, bucket, key, config
        )
        if not upload_id:
            return False

        initial_bytes = len(uploaded_parts) * config.multipart_chunksize
        progress = ProgressPercentage(
            local_path, file_size, initial_bytes=initial_bytes
        )

        try:
            with open(local_path, "rb") as f:
                f.seek(initial_bytes)
                start_part = len(uploaded_parts) + 1
                num_parts = math.ceil(file_size / config.multipart_chunksize)

                for i in range(start_part, num_parts + 1):
                    part_data = f.read(config.multipart_chunksize)
                    if not part_data:
                        break

                    response = self.s3_client.upload_part(
                        Bucket=bucket,
                        Key=key,
                        PartNumber=i,
                        UploadId=upload_id,
                        Body=part_data,
                    )
                    uploaded_parts[i] = response["ETag"]
                    self._update_resume_cache(
                        cache_path, {"UploadedParts": uploaded_parts}
                    )
                    progress(len(part_data))

            # Finalize the upload
            parts = [
                {"PartNumber": pn, "ETag": etag}
                for pn, etag in sorted(uploaded_parts.items())
            ]
            self.s3_client.complete_multipart_upload(
                Bucket=bucket,
                Key=key,
                UploadId=upload_id,
                MultipartUpload={"Parts": parts},
            )
            os.remove(cache_path)  # Clean up on success
            return True

        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchUpload":
                print(f"\n  ⚠️  Upload ID expired. Restarting upload for {local_path}.")
                os.remove(cache_path)
                return self.upload_file(local_path, bucket, key, config)  # Retry
            print(f"\n  ❌ Upload interrupted: {e}. State saved for resume.")
            return False
        except (Exception, KeyboardInterrupt) as e:
            print(f"\n  ❌ Upload interrupted: {e}. State saved for resume.")
            return False

    def _get_or_create_multipart_upload(self, cache, local_path, bucket, key, config):
        """Returns an existing UploadId from cache or creates a new one."""
        if cache:
            upload_id = cache.get("UploadId")
            uploaded_parts = {
                int(k): v for k, v in cache.get("UploadedParts", {}).items()
            }
            print(
                f"  -  Resuming previous upload (found {len(uploaded_parts)} completed parts)."
            )
            return upload_id, uploaded_parts
        try:
            file_md5 = self._calculate_md5(local_path)
            mpu = self.s3_client.create_multipart_upload(
                Bucket=bucket, Key=key, Metadata={"md5": file_md5}
            )
            upload_id = mpu["UploadId"]

            cache_data = {
                "Bucket": bucket,
                "S3Key": key,
                "UploadId": upload_id,
                "FileSize": os.path.getsize(local_path),
                "FileMTime": os.path.getmtime(local_path),
                "PartSize": config.multipart_chunksize,
                "UploadedParts": {},
            }
            self._save_resume_cache(self._get_cache_path(local_path), cache_data)
            return upload_id, {}
        except ClientError as e:
            print(f"\n  ❌ Could not start multipart upload: {e}")
            return None, {}

    def _is_file_synced(
        self, local_path: str, bucket: str, s3_key: str, sync_mode: str
    ) -> bool:
        """Checks if a file is already synced based on the specified mode."""
        try:
            s3_object = self.s3_client.head_object(Bucket=bucket, Key=s3_key)
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False  # Not synced because it doesn't exist remotely.
            print(f"  - [WARN] Error checking {s3_key}: {e}")
            return False  # Treat other errors as "not synced" to be safe.

        if sync_mode == "SKIP":
            print(f"  - Skipping (file exists): {s3_key}")
            return True

        # For SYNC mode, we must verify size and MD5
        local_size = os.path.getsize(local_path)
        if local_size != s3_object.get("ContentLength"):
            if self.verbose:
                print(f"  - [DEBUG] Sync failed (size mismatch): {s3_key}")
            return False

        local_md5 = self._calculate_md5(local_path)
        remote_md5 = s3_object.get("Metadata", {}).get("md5")
        if local_md5 == remote_md5:
            print(f"  - Skipping (in sync): {s3_key}")
            return True

        if self.verbose:
            print(f"  - [DEBUG] Sync failed (MD5 mismatch): {s3_key}")
        return False  # MD5 mismatch or remote MD5 not present

    # --- Static & Caching Helpers ---

    @staticmethod
    def _get_files_in_folder(folder_path: str) -> list[str]:
        """Recursively finds all files in a folder, excluding cache files."""
        file_list = []
        for root, _, files in os.walk(folder_path):
            for filename in files:
                if not filename.endswith(".s3_upload.json"):
                    file_list.append(os.path.join(root, filename))
        return file_list

    @staticmethod
    def _calculate_md5(file_path: str) -> str:
        """Calculates the MD5 hash of a file efficiently."""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    @staticmethod
    def _get_cache_path(file_path: str) -> str:
        return f"{file_path}.s3_upload.json"

    def _load_resume_cache(
        self, path: str, local_path: str, bucket: str, key: str
    ) -> Optional[Dict]:
        """Loads and validates the resume cache file."""
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r") as f:
                cache = json.load(f)
            # Validate that the cache is for the exact same file and destination
            if (
                cache.get("Bucket") != bucket
                or cache.get("S3Key") != key
                or cache.get("FileSize") != os.path.getsize(local_path)
                or cache.get("FileMTime") != os.path.getmtime(local_path)
            ):
                os.remove(path)  # Stale cache, remove it
                return None
            return cache
        except (json.JSONDecodeError, IOError):
            os.remove(path)  # Corrupt cache
            return None

    def _save_resume_cache(self, path: str, data: dict):
        with open(path, "w") as f:
            json.dump(data, f)

    def _update_resume_cache(self, path: str, updates: dict):
        """Atomically updates fields in an existing cache file."""
        # This is a simplified update; a robust implementation might use file locks
        if not os.path.exists(path):
            return
        try:
            with open(path, "r+") as f:
                data = json.load(f)
                data.update(updates)
                f.seek(0)
                f.truncate()
                json.dump(data, f)
        except (json.JSONDecodeError, IOError):
            pass  # Ignore if cache is corrupt or unreadable
