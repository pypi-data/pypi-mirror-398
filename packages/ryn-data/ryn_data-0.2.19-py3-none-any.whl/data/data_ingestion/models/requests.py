from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ClearMLCredentials(BaseModel):
    access_key: str
    secret_key: str

class S3Credentials(BaseModel):
    access_key: Optional[str] = None
    secret_key: Optional[str] = None
    endpoint_url: Optional[str] = None
    bucket_name: Optional[str] = None
class KaggleCredentials(BaseModel):
    user_name: str
    key: str

# --- Enum for Download Method ---

class DownloadMethod(str, Enum):
    """Enumeration for the available dataset download methods."""
    PRESIGNED_URLS = "presigned_urls"
    STREAM_ZIP = "stream_zip"
    DIRECT_STREAM = "direct_stream"

class S3DownloadRequest(BaseModel):
    # Core dataset and S3 file information
    s3_file_path: str
    # user_name: str
    dataset_name: Optional[str] = None
    private: bool = False
    dataset_type: Optional[str] = Field(default=None, alias="dataset_type")
    s3_source: Optional[S3Credentials] = None
    # token: str
    restructure: bool = True
    
    
class KaggleDownloadRequest(BaseModel):
    dataset_id: str
    user_name: str
    dataset_name: Optional[str] = None
    private: bool = False
    kaggle: KaggleCredentials
    dataset_type : str
    queue_name: str = "default" 
    clearml: ClearMLCredentials
    s3_config: S3Credentials

class HuggingFaceDownloadRequest(BaseModel):
    # Hugging Face dataset information
    dataset_name: str
    dataset_config: Optional[str] = "default"
    dataset_type: str
    
    # ClearML dataset metadata
    # user_name: str
    private: bool = False
    revision: Optional[str] = "main"
    
    # token: str
    restructure: bool = True



class OpenMLDownloadRequest(BaseModel):
    dataset_id: int
    user_name: str
    dataset_name: Optional[str] = None
    private: bool = False
    dataset_type : str
    queue_name: str = "default" 
    clearml: ClearMLCredentials
    s3_config: S3Credentials

class ListDatasetsRequest(BaseModel):
#     clearml_access_key: str
#     clearml_secret_key: str
#     user_name: Optional[str] = None
#     private_only: Optional[bool] = False
    queue_name: str = "default" 
    
class DownloadDatasetRequest(BaseModel):
    dataset_name: str
    # user_name: str  # Added user_name for filtering
    # # Nested credentials for the S3 target where the dataset will be stored
    # token: str
    download_method: DownloadMethod = DownloadMethod.PRESIGNED_URLS
    expiration: int = 3600  # For presigned URLs, expiration in seconds (default 1 hour)
    version : Optional[str] = "latest"

class TaskStatusRequest(BaseModel):
    task_id: str
    # user_name: str
    # token: str


class ListTasksRequest(BaseModel):
    # user_name: str
    # token: str
    limit: int = 50

class ListClearMLDatasetsRequest(BaseModel):
    tags: Optional[list[str]] = None

    @field_validator("tags", mode="before")
    def normalize_tags(cls, v):
        if isinstance(v, str):
            return [t.strip() for t in v.split(",") if t.strip()]
        return v

    
class LocalUploadRequest(BaseModel):
    """Request model for local file upload to S3 and ClearML."""
    
    local_folder_path: str = Field(
        ..., 
        description="Absolute path to the local folder containing the dataset"
    )
    dataset_name: str = Field(
        ..., 
        description="Name of the dataset"
    )
    user_name: str = Field(
        ..., 
        description="Username of the dataset owner"
    )
    private: bool = Field(
        default=False, 
        description="Whether the dataset is private"
    )
    dataset_type: Optional[str] = Field(
        None, 
        description="Tag/category for the dataset (e.g., 'image_classification', 'text_generation')"
    )
    s3_folder_prefix: Optional[str] = Field(
        None, 
        description="S3 folder prefix (default: datasets/{user_name}/{dataset_name})"
    )
    sync_mode: Optional[str] = Field(
        default="SKIP", 
        description="Sync mode: OVERWRITE, SKIP, or SYNC"
    )
    s3_config: S3Credentials = Field(
        ..., 
        description="S3 credentials for target storage"
    )
    clearml: ClearMLCredentials = Field(
        ..., 
        description="ClearML credentials"
    )
    queue_name: str = Field(
        default="default", 
        description="ClearML queue name"
    )
    