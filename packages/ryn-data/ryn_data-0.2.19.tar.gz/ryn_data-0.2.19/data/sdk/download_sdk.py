import io
import json
import logging
import os
import zipfile
from contextlib import contextmanager
from typing import Optional

import boto3
import requests
from botocore.client import BaseClient
from fastapi import HTTPException
from tqdm import tqdm

from data.sdk.datasets_object import create_dataset_object

# This line loads the variables from .env into the environment
# env_path = Path(__file__).resolve().parent / ".env"
# print(env_path)
# load_dotenv(env_path)

# Set up logger for consistent output
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
# USER_MANAGEMENT_API = os.environ["USER_MANAGEMENT_API"]
# CLEARML_API_URL = os.environ["CLEARML_API_HOST"]
# USER_MANAGEMENT_API = os.environ["USER_MANAGEMENT_API"]


def get_user_info_with_bearer(bearer_token: str, user_management_url):
    """Get user information using bearer token only"""
    try:
        print("user_management_url", user_management_url)
        url = f"{user_management_url}/metadata"
        response = requests.get(
            url,
            headers={"Authorization": f"Bearer {bearer_token}"},
            timeout=100,
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to authenticate with bearer token: {response.text}",
            )

        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error calling user management API with bearer token: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error communicating with user management service: {str(e)}",
        )


def get_user_metadata(
    bearer_token: Optional[str] = None, user_management_url: str = None
):
    """
    Get user metadata using either bearer token or username.
    Priority: Bearer token > Username

    Args:
        bearer_token: Bearer token from Authorization header
        username: Username from query params

    Returns:
        Tuple of (user_metadata dict, username string)
    """
    if bearer_token:
        # Method 1: If bearer token is provided, use it (no username needed)
        logger.info("Authenticating with bearer token")
        user_data = get_user_info_with_bearer(bearer_token, user_management_url)
        user_metadata = user_data.get("metadata")
        # Extract username from the response
        authenticated_username = user_metadata.get("normalized_username")
        return user_metadata, authenticated_username

    else:
        raise HTTPException(
            status_code=401,
            detail="Authentication required: Provide either Bearer token in Authorization header OR username in query parameters",
        )


# --- tqdm Progress Bar Callback for Boto3 ---
class TqdmProgressCallback:
    """
    A boto3 download callback that updates a tqdm progress bar.
    """

    def __init__(self, pbar: tqdm):
        self.pbar = pbar

    def __call__(self, bytes_transferred: int):
        self.pbar.update(bytes_transferred)


@contextmanager
def clearml_client_session(credentials: dict, log_extra={}, username=None):
    """
    A context manager that creates an explicit, isolated ClearML Session and APIClient
    based on the provided user credentials.
    """

    clearml_access_key = credentials.get("access_key")
    clearml_secret_key = credentials.get("secret_key")
    api_host = credentials.get("api_host")
    auth = requests.auth.HTTPBasicAuth(clearml_access_key, clearml_secret_key)

    search_payload = {
        "meta": {"requested_version": "1.0"},
        "name": f"DatasetIngestion_{username}_stage",  # Exact match using regex
    }
    headers = {"Content-Type": "application/json"}

    session = requests.Session()

    search_resp = session.post(
        f"{api_host}/projects.get_all_ex",
        data=json.dumps(search_payload),
        auth=auth,
        headers=headers,
    )

    if search_resp.status_code != 200:
        raise HTTPException(
            detail=search_resp.json()["meta"]["result_msg"],
            status_code=search_resp.status_code,
        )
    from clearml import Task

    Task.set_credentials(
        key=clearml_access_key, secret=clearml_secret_key, api_host=api_host
    )
    # 1. Create the explicit Session object with credentials
    # try:
    #     from clearml.backend_api.session import Session

    #     session = Session(
    #         api_key=credentials.get("access_key"),
    #         secret_key=credentials.get("secret_key"),
    #         # You might need to specify the api_server if not using the default
    #         # host="https://api.clear.ml"
    #     )

    #     # Task.set_credentials(
    #     #     key=credentials.get("access_key"),
    #     #     secret=credentials.get("secret_key"),
    #     #     api_host="http://144.172.105.98:30003",
    #     # )
    # except Exception as e:
    #     print(e)
    #     logger.error("authorization failed", extra=log_extra)
    #     raise HTTPException(
    #         401,
    #         detail=f"{e}",
    #     )

    try:
        # 3. Yield the fully configured client for the 'with' block to use
        yield
    finally:
        session.close()
        logger.info("ClearML session restored and client cleaned up.")


def get_s3_path_from_clearml_dataset(
    clearml_access_key: str,
    clearml_secret_key: str,
    clearml_api_host,
    dataset_name: str,
    # clearml_host: str,
    version: str = "latest",
    user_name: str = "default",
) -> str:
    """
    Retrieve the S3 path of a ClearML dataset using provided credentials.
    """
    from clearml import Dataset, Task

    credentials = {
        "access_key": clearml_access_key,
        "secret_key": clearml_secret_key,
        "api_host": clearml_api_host,
    }

    with clearml_client_session(credentials):
        Task.set_credentials(
            key=credentials.get("access_key"), secret=credentials.get("secret_key")
        )
        project_path = f"DatasetIngestion_{user_name}_stage"

        datasets = Dataset.list_datasets(
            partial_name=dataset_name,
            only_completed=True,
            dataset_project=project_path,
            recursive_project_search=True,
        )
        datasets = datasets.copy()
        new_datasets = []
        print(f"dataset_name={dataset_name}")
        for index, data in enumerate(datasets):
            if data["name"] == dataset_name:
                new_datasets.append(data)

        datasets = new_datasets.copy()
        if not datasets:
            raise ValueError(
                f"No datasets found with name containing '{dataset_name}'."
            )

        logger.info(
            f"Found {len(datasets)} potential dataset(s) matching '{dataset_name}'. Searching for exact match..."
        )

        versions = [d["version"] for d in datasets]
        print(f"available versions:{versions}")
        print(datasets)

        if version not in versions and version != "latest":
            raise ValueError("no such version exists")

        restructured = False

        if version == "latest":
            datasets = sorted(datasets, key=lambda x: x["version"], reverse=True)

            if "restructure" in datasets[0]["tags"]:
                restructured = True

            for i in datasets[0]["tags"]:
                if "s3_path" in i:
                    return ":".join(i.split(":")[1:]), restructured
        else:
            for d in datasets:
                if d["version"] == version:
                    if "restructure" in d["tags"]:
                        restructured = True

                    for i in d["tags"]:
                        if "s3_path" in i:
                            return ":".join(i.split(":")[1:]), restructured


def download_dataset_from_s3(
    s3_client: BaseClient,
    s3_path: str,
    absolute_path: str,
    dataset_name: str,
    dataset_type: Optional[str] = None,
    is_structured: bool = False,
):
    """
    Download dataset files from an S3 path to a local directory with a progress bar.
    """
    if not s3_path.startswith("s3://"):
        raise ValueError(f"Invalid S3 path format: {s3_path}. Must start with 's3://'.")

    s3_path_parts = s3_path[5:].split("/", 1)
    if len(s3_path_parts) < 2:
        raise ValueError(
            f"Invalid S3 path format: {s3_path}. Must be 's3://bucket/key'."
        )

    s3_bucket, s3_key_prefix = s3_path_parts

    # --- Step 1: List all objects and calculate total size ---
    logger.info("Listing files in S3 and calculating total size...")
    paginator = s3_client.get_paginator("list_objects_v2")
    pages = paginator.paginate(Bucket=s3_bucket, Prefix=s3_key_prefix)

    files_to_download = []
    total_size = 0
    for page in pages:
        for obj in page.get("Contents", []):
            files_to_download.append(obj)
            total_size += obj["Size"]

    if not files_to_download:
        logger.warning(f"No files found at S3 path: {s3_path}. Nothing to download.")
        return

    logger.info(
        f"Found {len(files_to_download)} files. Total size: {total_size / (1024 * 1024):.2f} MB"
    )

    # --- Step 2: Download files with a tqdm progress bar ---
    with tqdm(
        total=total_size, unit="B", unit_scale=True, desc="Downloading dataset"
    ) as pbar:
        progress_callback = TqdmProgressCallback(pbar)

        for obj in files_to_download:
            s3_key = obj["Key"]
            # Create a relative path for the local file system
            relative_path = os.path.relpath(s3_key, start=s3_key_prefix)
            local_file_path = os.path.join(absolute_path, relative_path)

            # Update progress bar description to show the current file
            pbar.set_postfix_str(os.path.basename(local_file_path), refresh=True)

            # Ensure local directory for the file exists
            os.makedirs(os.path.dirname(local_file_path), exist_ok=True)

            # Download the file with the progress callback
            s3_client.download_file(
                s3_bucket, s3_key, local_file_path, Callback=progress_callback
            )
    if is_structured:
        ds = create_dataset_object(
            absolute_path=absolute_path,
            dataset_name=dataset_name,
            dataset_type=dataset_type,
        )
        return ds
    else:
        logger.warning("data is not restructured: returning None")

        return None


# Helper function to generate presigned URLs
def generate_presigned_urls(s3_client, s3_path: str, expiration: int = 3600):
    """Generate presigned URLs for all files under the S3 path"""
    try:
        s3_path_parts = s3_path[5:].split("/", 1)
        bucket_name, s3_key_prefix = s3_path_parts

        paginator = s3_client.get_paginator("list_objects_v2")
        page_iterator = paginator.paginate(Bucket=bucket_name, Prefix=s3_key_prefix)

        presigned_urls = []

        print(s3_key_prefix, bucket_name)

        for page in page_iterator:
            if "Contents" in page:
                for obj in page["Contents"]:
                    obj_key = obj["Key"]
                    obj_size = obj["Size"]

                    # Skip directories
                    if obj_key.endswith("/"):
                        continue

                    try:
                        presigned_url = s3_client.generate_presigned_url(
                            "get_object",
                            Params={"Bucket": str(bucket_name), "Key": str(obj_key)},
                            ExpiresIn=expiration,
                        )

                        # Extract filename from key
                        filename = obj_key.split("/")[-1]
                        relative_path = obj_key[len(s3_key_prefix) :].lstrip("/")
                        if not relative_path:
                            relative_path = filename

                        presigned_urls.append(
                            {
                                "filename": filename,
                                "s3_key": obj_key,
                                "size": obj_size,
                                "download_url": presigned_url,
                            }
                        )
                    except Exception as e:
                        logger.error(
                            f"Error generating presigned URL for {obj_key}: {e}"
                        )
                        continue

        return presigned_urls
    except Exception as e:
        logger.error(f"Error generating presigned URLs: {e}")
        raise


# Helper function to create streaming zip
def create_streaming_zip(s3_client, bucket_name: str, s3_key: str):
    """Create a streaming zip response of S3 files"""

    def generate_zip():
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            try:
                paginator = s3_client.get_paginator("list_objects_v2")
                page_iterator = paginator.paginate(Bucket=bucket_name, Prefix=s3_key)

                for page in page_iterator:
                    if "Contents" in page:
                        for obj in page["Contents"]:
                            obj_key = obj["Key"]

                            # Skip directories
                            if obj_key.endswith("/"):
                                continue

                            try:
                                # Get object from S3
                                response = s3_client.get_object(
                                    Bucket=bucket_name, Key=obj_key
                                )
                                file_data = response["Body"].read()

                                # Add to zip with relative path
                                relative_path = obj_key[len(s3_key) :].lstrip("/")
                                if not relative_path:
                                    relative_path = obj_key.split("/")[-1]

                                zip_file.writestr(relative_path, file_data)
                                logger.info(
                                    f"Added {obj_key.split('/')[-1]} to zip as {relative_path}"
                                )

                            except Exception as e:
                                logger.error(f"Error adding {obj_key} to zip: {e}")
                                continue

            except Exception as e:
                logger.error(f"Error creating zip: {e}")
                raise

        zip_buffer.seek(0)
        return zip_buffer.getvalue()

    return generate_zip()


def s3_download(
    dataset_name: str,
    absolute_path: str,
    token: str,
    clearml_api_host: str,
    user_management_url: str,
    dataset_type: Optional[str] = None,
    s3_endpoint_url: Optional[str] = None,
    method: str = "download",
    version: str = "latest",
):
    """
    Main function to download a ClearML dataset from S3 to a local directory.
    """

    user_metadata, authenticated_username = get_user_metadata(
        token, user_management_url
    )
    s3_access_key = user_metadata["s3_access_key"]
    s3_secret_key = user_metadata["s3_secret_key"]
    user_metadata["s3_bucket"]
    clearml_access_key = user_metadata["clearml_access_key"]
    clearml_secret_key = user_metadata["clearml_secret_key"]
    s3_endpoint_url = s3_endpoint_url

    s3_client = boto3.client(
        "s3",
        aws_access_key_id=s3_access_key,
        aws_secret_access_key=s3_secret_key,
        endpoint_url=s3_endpoint_url,
    )

    # 1. Get the S3 path from ClearML metadata
    s3_path, is_structured = get_s3_path_from_clearml_dataset(
        clearml_access_key,
        clearml_secret_key,
        clearml_api_host,
        dataset_name,
        user_name=authenticated_username,
        version=version,
    )
    logger.info(f"Retrieved S3 path from ClearML: {s3_path}")

    # 2. Download the dataset from S3
    logger.info(f"Starting download to local directory: {absolute_path}")

    if method == "download":
        ds = download_dataset_from_s3(
            s3_client, s3_path, absolute_path, dataset_name, dataset_type, is_structured
        )

        logger.info("Download complete.")
        return ds

    elif method == "presigned_urls":
        urls = generate_presigned_urls(s3_client, s3_path)
        logger.info(f"Generated {len(urls)} presigned URLs.")
        return urls

    elif method == "streaming_zip":
        s3_path_parts = s3_path[5:].split("/", 1)
        bucket_name, s3_key_prefix = s3_path_parts
        zip_data = create_streaming_zip(s3_client, bucket_name, s3_key_prefix)
        logger.info("Created streaming zip of dataset.")
        return zip_data
