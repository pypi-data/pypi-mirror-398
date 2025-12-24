import pandas as pd
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def summarize_dataset(path: Path,dataset_type) -> str:
    summary = {}

    #read metadata.parquet to return number of samples and columns
    if dataset_type == "image_classification":
        try:
            df = pd.read_parquet(path / "metadata.parquet")
            summary["num_samples"] = len(df)
            summary["num_classes"] = df['label'].nunique() if 'label' in df.columns else None
            summary["columns"] = df.columns.tolist()
        except Exception as e:
            logger.warning(f"Could not read metadata.parquet for summary: {e}")
            summary["num_samples"] = None
            summary["num_classes"] = None
            summary["columns"] = None
        return summary
    return None


def save_request_info_to_temp(temp_path: Path, request_info: dict):
    try:
        with open(temp_path / "_request_info.json", 'w') as f:
            request_info["timestamp"] = datetime.now().isoformat()
            json.dump(request_info, f, indent=4)
    except (IOError, TypeError) as e:
        logger.warning(f"Could not save request info to temp directory {temp_path}: {e}")