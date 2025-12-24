from pydantic import BaseModel
from typing import Optional

class DatasetMetadata(BaseModel):
    """Schema for the final, persisted metadata of a dataset."""
    dataset_id: str
    dataset_name: str
    dataset_config: Optional[str] = None
    last_commit: Optional[str] = None
    last_modified: Optional[str] = None 
    user_name: str
    private: bool = False
    version: int = 0
    temp: bool = True
    source: str
    created_at: str
    s3_path: str
    summary: Optional[dict] = {}
    revision: str
    dataset_type: str
    restructure_valid: bool
    validation: bool
    tags: Optional[list[str]] = []
