import json
import logging
from pathlib import Path
from typing import Dict, Any
from dataclasses import dataclass

import pandas as pd
import pyarrow.parquet as pq

logger = logging.getLogger(__name__)



@dataclass(frozen=True)
class Image:
    """Represents the standard structure for image data."""
    path: str
    bytes: bytes

@dataclass(frozen=True)
class ImageClassificationRecord:
    """
    Defines the data schema for a single image classification example.
    This is the contract for the output Parquet files.
    """
    image: Image
    label: str

@dataclass(frozen=True)
class ImageSegmentationRecord:
    """
    Defines the data schema for a single image segmentation example.
    The 'mask' can be optional if not present for all splits (e.g., test set).
    """
    image: Image
    mask: Image | None # Using | None for optionality (Python 3.10+)

@dataclass(frozen=True)
class TextGenerationRecord:
    """
    Defines the data schema for an instruction-following text generation example.
    The 'input' field is optional context.
    """
    instruction: str
    output: str
    input: str | None # Using | None for optionality


def _get_class_labels(metadata_path: Path) -> list[str]:
    """Reads the metadata.csv to extract a sorted list of unique labels."""
    if not metadata_path.exists():
        logger.warning(f"Metadata file not found at {metadata_path}. Cannot determine class labels.")
        return []
    try:
        df = pd.read_csv(metadata_path)
        if "label" not in df.columns:
            logger.warning("'label' column not in metadata.csv. Cannot determine class labels.")
            return []
        
        labels = sorted(df["label"].dropna().unique().tolist())
        return [str(label) for label in labels]
    except Exception as e:
        logger.error(f"Failed to read or process {metadata_path}: {e}")
        return []


def _get_features_schema(task_type: str, source_input_path: Path) -> Dict[str, Any]:
    """Generates the Hugging Face Datasets features schema based on the task type."""
    if task_type == "image_classification":
        class_labels = _get_class_labels(source_input_path / "metadata.csv")
        return {
            "image": {
                "feature": {
                    "path": "string",
                    "bytes": "binary",
                }
            },
            "label": {
                "_type": "ClassLabel",
                "names": class_labels,
            },
        }
    elif task_type == "image_segmentation":
        return {
            "image": {"_type": "Image", "decode": True},
            "mask": {"_type": "Image", "decode": True},
        }
    elif task_type == "text_generation":
        return {
            "instruction": "string",
            "input": "string",
            "output": "string",

        }
    else:
        raise ValueError(f"Unsupported task type for schema generation: {task_type}")


def generate_dataset_info(
    output_path: Path,
    source_input_path: Path,
    dataset_name: str,
    task_type: str,
) -> None:
    """
    Generates a dataset_info.json file in the Hugging Face format.

    This function inspects the restructured Parquet output directory to gather
    statistics like file sizes and row counts for each split.

    Args:
        output_path: The root directory of the restructured Parquet dataset
                     (e.g., 'restructured_dataset').
        source_input_path: The path to the original source data, used to
                           extract class labels for classification.
        dataset_name: The desired name for the dataset.
        task_type: The task type ('image_classification' or 'image_segmentation').
    """
    logger.info(f"Generating dataset_info.json for '{dataset_name}'...")

    if not output_path.is_dir():
        logger.error(f"Output path '{output_path}' does not exist. Cannot generate info file.")
        return

    splits_info = {}
    total_size_bytes = 0

    # Iterate through split directories (train, validation, test)
    for split_dir in output_path.iterdir():
        if not split_dir.is_dir():
            continue

        split_name = split_dir.name
        logger.info(f"Processing split: '{split_name}'")

        try:
            # Efficiently read dataset metadata without loading all data
            dataset = pq.ParquetDataset(split_dir)
            num_examples = dataset.read().num_rows

            # Calculate the total size of Parquet files in the split
            num_bytes = sum(f.stat().st_size for f in split_dir.glob("*.parquet"))
            total_size_bytes += num_bytes

            splits_info[split_name] = {
                "name": split_name,
                "num_bytes": num_bytes,
                "num_examples": num_examples,
            }
        except Exception as e:
            logger.warning(f"Could not process split '{split_name}'. Skipping. Error: {e}")
            continue

    if not splits_info:
        logger.error("No valid splits found. Aborting dataset_info.json generation.")
        return

    # Generate the features schema
    features_schema = _get_features_schema(task_type, source_input_path)

    # Assemble the final dictionary
    dataset_info = {
        "citation": "",
        "description": f"Dataset for {task_type}, restructured from local files.",
        "features": features_schema,
        "homepage": "",
        "license": "",
        "dataset_name": dataset_name,
        "version": {"version_str": "1.0.0", "major": 1, "minor": 0, "patch": 0},
        "splits": splits_info,
        "size_in_bytes": total_size_bytes,
    }

    # Write the JSON file
    info_file_path = output_path / "dataset_info.json"
    with open(info_file_path, "w") as f:
        json.dump(dataset_info, f, indent=2)

    logger.info(f"Successfully created '{info_file_path}'")