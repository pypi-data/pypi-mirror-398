# import torch
# from torch.utils.data import Dataset
import gc
import json
import math
import os
from pathlib import Path
from typing import Callable, Dict, Optional

from datasets import DatasetDict, disable_caching, load_dataset
from datasets import Image as HFImage

disable_caching()


def create_chatml_dataset(data_dir: str, dataset_name: str) -> DatasetDict:
    """
    Creates a Hugging Face DatasetDict for ChatML data.

    Reads 'metadata.json' (if present) and injects it into dataset.info.description
    as a JSON string. Validates conversation structure.
    """
    root_dir = Path(data_dir) / dataset_name
    metadata_path = Path(data_dir) / "metadata.json"
    cache_dir = root_dir / "cache"

    # --- 1. Load Metadata (if available) ---
    description_str = ""
    if metadata_path.exists():
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                meta_dict = json.load(f)
                # Dump metadata dict to string to store in description
                description_str = json.dumps(meta_dict)
        except Exception as e:
            print(f"Warning: Failed to load metadata.json: {e}")

    # --- 2. Define Validation Logic ---
    def is_valid_conversation(example):
        msgs = example.get("messages")  # Use .get to avoid KeyErrors

        # Must be a list and have content
        if not isinstance(msgs, list) or len(msgs) < 2:
            return False

        try:
            # Check for required keys in the first turn
            if "role" not in msgs[0] or "content" not in msgs[0]:
                return False

            # Validates that the conversation starts with user -> assistant
            # (Note: This logic excludes conversations starting with System prompts.
            #  Adjust indices if your data includes System prompts).
            return msgs[0]["role"] == "user" and msgs[1]["role"] == "assistant"
        except (IndexError, TypeError):
            return False

    ds_splits = {}

    # Only iterate over directories (avoids trying to load metadata.json as a split)
    items = os.listdir(root_dir)
    splits = [item for item in items if (root_dir / item).is_dir() if item != "cache"]

    print(f"Found splits: {splits}")

    for split in splits:
        split_path = root_dir / split

        # Load raw data
        try:
            raw_ds = load_dataset(
                "parquet",
                data_files=str(split_path / "*.parquet"),
                split="train",
                cache_dir=cache_dir,
            )
        except Exception as e:
            print(f"Skipping {split}: Could not load parquet files. Error: {e}")
            continue

        # # Filter using the validation logic
        # processed_ds = raw_ds.filter(is_valid_conversation)
        

        # --- 3. Inject Metadata ---
        if description_str:
            raw_ds.info.description = description_str

        ds_splits[split] = raw_ds

    # shutil.rmtree(cache_dir, ignore_errors=True)

    return DatasetDict(ds_splits)


def create_image_classification_dataset(
    data_dir: str, dataset_name: str, transform: Optional[Callable] = None
) -> DatasetDict:
    """
    Creates a Hugging Face DatasetDict for image classification.

    Reads 'metadata.json' (if present) and injects it into dataset.info.description
    as a JSON string.
    """
    root_dir = Path(data_dir) / dataset_name
    structure_path = root_dir / "structure.parquet"
    metadata_path = Path(data_dir) / "metadata.json"

    cache_dir = root_dir / "cache"
    # --- 1. Load Metadata (if available) ---
    description_str = ""
    if metadata_path.exists():
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                meta_dict = json.load(f)
                description_str = json.dumps(meta_dict)
                # print(f"discription loaded metadata{description_str}")
        except Exception as e:
            print(f"Warning: Failed to load metadata.json: {e}")

    ds_splits: Dict[str, any] = {}

    # --- Case A: Load from split folders (train/*.parquet, test/*.parquet) ---
    if not structure_path.exists():
        # Check specific directories or list root directories
        # Filtering out files, keeping only directories
        splits = [
            item
            for item in os.listdir(root_dir)
            if (root_dir / item).is_dir() and item != "cache"
        ]

        for split in splits:
            split_path = root_dir / split
            # Load parquet files from specific folder
            split_data = load_dataset(
                "parquet",
                data_files=str(split_path / "*.parquet"),
                split="train",
                cache_dir=cache_dir,
            )

            features = split_data.features.copy()
            features["image"] = HFImage()  # Cast to HF Image feature
            dataset_with_images = split_data.cast(features)

            # print(f"discription: (building object){description_str}")

            if description_str:
                dataset_with_images.info.description = description_str

            ds_splits[split] = dataset_with_images
            print(f"Loaded split '{split}' with {len(split_data)} samples.")

        final_dataset_dict = DatasetDict(ds_splits)

    # --- Case B: Load from single structure file ---
    else:
        raw_dataset = load_dataset(
            "parquet",
            data_files=str(structure_path),
            split="train",
            cache_dir=cache_dir,
        )

        # Convert relative paths to absolute paths
        def add_absolute_path(example):
            return {"image": str(root_dir / example["file_path"])}

        dataset_with_paths = raw_dataset.map(add_absolute_path)

        # Cast the 'image' column to the native Image feature
        features = dataset_with_paths.features.copy()
        features["image"] = HFImage()
        dataset_with_images = dataset_with_paths.cast(features)

        # Separate into splits
        unique_splits = set(dataset_with_images["split"])

        for split_name in unique_splits:
            # Filter and cleanup
            ds_splits[split_name] = dataset_with_images.filter(
                lambda x: x["split"] == split_name
            )
            ds_splits[split_name] = ds_splits[split_name].remove_columns(
                ["file_path", "split"]
            )

            # Inject Metadata
            if description_str:
                ds_splits[split_name].info.description = description_str

        final_dataset_dict = DatasetDict(ds_splits)

    # --- 3. Apply Transforms (Optional) ---
    if transform:

        def apply_transform(batch):
            # batch['image'] is a list of PIL images because of the cast() above
            batch["pixel_values"] = [
                transform(img.convert("RGB")) for img in batch["image"]
            ]
            return batch

        final_dataset_dict.set_transform(apply_transform)

    # shutil.rmtree(cache_dir, ignore_errors=True)
    return final_dataset_dict


def create_dataset_object(
    absolute_path: str, dataset_name: str, dataset_type: Optional[str] = None
):
    if dataset_type == "text_generation":
        ds = create_chatml_dataset(absolute_path, dataset_name)
        return ds
    elif dataset_type == "image_classification":
        ds = create_image_classification_dataset(absolute_path, dataset_name)
        return ds
    return None


def save_dataset_object(dataset_name: str, ds: DatasetDict, store_path: Path):
    """
    Docstring for save_dataset_object

    :param ds: huggingface datasetDict
    :type ds: DatasetDict
    :param store_path: path to store data
    :type store_path: Path

    store data in store_path in the following format:

    store_path/split/0000-000n.parquet
    """
    store_path = Path(store_path) / dataset_name

    metadata_path = Path(store_path) / "metadata.json"

    store_path.mkdir(parents=True, exist_ok=True)

    if len(ds) > 0:
        # Get the first dataset object (e.g., 'train')
        first_split_ds = next(iter(ds.values()))

        # Retrieve the description string
        description_str = first_split_ds.info.description

        if description_str:
            try:
                metadata = json.loads(description_str)

                print(f"Saving metadata to {metadata_path}")
                with open(metadata_path, "w", encoding="utf-8") as f:
                    json.dump(metadata, f, indent=2)
            except json.JSONDecodeError:
                print(
                    f"Warning: Description in {dataset_name} is not valid JSON. Skipping metadata.json."
                )
            except Exception as e:
                print(f"Warning: Failed to save metadata: {e}")

    if metadata["dataset_type"] == "image_classification":
        EXPECTED_NUM_ROWS = 5000
    else:
        EXPECTED_NUM_ROWS = 50000
    print(f"expected num rows per parquet file: {EXPECTED_NUM_ROWS}")
    for split, dataset in ds.items():
        # Create the directory: store_path/split
        split_dir = store_path / split
        split_dir.mkdir(parents=True, exist_ok=True)

        total_rows = len(dataset)

        # Calculate total shards needed based on row count
        if total_rows == 0:
            num_shards = 1
        else:
            num_shards = math.ceil(total_rows / EXPECTED_NUM_ROWS)

        for i in range(num_shards):
            # Generate filename: 0000.parquet, 0001.parquet, etc.
            filename = f"part-{i:04d}-of-{num_shards:04d}.parquet"
            file_path = split_dir / filename

            # Create the shard
            if total_rows > 0:
                # contiguous=True ensures rows 0-N go to file 1, N+1-M to file 2, etc.
                # rather than round-robin distribution.
                dataset_shard = dataset.shard(
                    num_shards=num_shards, index=i, contiguous=True, keep_in_memory=True
                )
            else:
                dataset_shard = dataset

            # Save to Parquet
            dataset_shard.to_parquet(file_path)

            del dataset_shard
            gc.collect()

        # dataset.cleanup_cache_files()


# # #print sample image from the dataset
# if __name__ == "__main__":
#     dataset = ImageClassificationDataset(data_dir="downloaded_datasett",dataset_name="microsoft-cats_vs_dogs",split="train")
#     import matplotlib.pyplot as plt

#     image, label = dataset[100]

#     #save image
#     plt.imshow(image)
#     plt.title(f"Label: {label}")
#     plt.savefig("sample_image.png")
#     plt.show()

#     text_dataset = TextGenerationDataset(data_dir="/home/mlops/abolfazl/tools/data_platform/ryn/data/data_restructure/text_generation_test_output", dataset_name="restructured_text_dataset", split="validation")

#     sample = text_dataset[10]
#     print("Instruction:", sample["instruction"])
#     print("Response:", sample["response"])
