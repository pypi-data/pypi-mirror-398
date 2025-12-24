import gc
import logging
import math
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
from datasets import ClassLabel, Dataset, load_dataset
from fastapi import HTTPException
from huggingface_hub import HfApi,snapshot_download

from data.data_ingestion.handlers.conditions import DatasetConditionChecker
from data.data_ingestion.models.metadata import DatasetMetadata
from data.data_ingestion.storage_handler import DatasetStorageHandler

logger = logging.getLogger(__name__)

# Constants
BATCH_SIZE_TEXT = 5000
BATCH_SIZE_IMAGE = 5000
BATCH_SIZE_PARQUET = 1000
EXPECTED_ROWS_PER_SHARD = 10000
NUM_CORES_IMAGE_PROC = 1
ACCEPTABLE_TYPES = {"text_generation", "image_classification"}

USER_STORAGE_SIZE_LIMIT_BYTES = 50 * 1024**3  # 50 GB

TEMPLATE_COLUMN_MAPPINGS = {
    "text_generation": {
        "doc_url": "https://huggingface.co/docs/trl/main/en/dataset_formats#prompt-completion",
        "required_columns": {
            "instruction": ["prompt", "instruction", "query", "question", "input","inputs"],
            "response": [
                "completion",
                "response",
                "output",
                "answer",
                "answers",
                "target",
                "summary",
                "outputs"
            ],
        },
        "optional_columns": {"input": ["input", "context"]},
    },
    "image_classification": {
        "required_columns": {
            "image": ["image", "img"],
            "label": ["label", "labels", "class", "category", "target"],
        },
        "optional_columns": {"image_path": ["image_path", "img_path"]},
    },
    "image_segmentation": {
        "required_columns": {
            "image": ["image", "img", "pixel_values"],
            "mask": [
                "mask",
                "segmentation_mask",
                "label_mask",
                "annotation",
                "gtFine",
                "label",
            ],
        },
        "optional_columns": {"image_path": ["image_path", "img_path"]},
    },
}


class HuggingFaceHandler:
    def _log_event(
        self,
        level: int,
        message: str,
        category: str,
        event_type: str,
        status: str,
        base_extra: Dict[str, Any],
        exc_info: bool = False,
    ):
        """Helper to handle structured logging to reduce code duplication."""
        extra = base_extra.copy()
        extra.update(
            {"event": {"category": category, "type": event_type, "status": status}}
        )
        logger.log(level, message, exc_info=exc_info, extra=extra)

    def _check_schema(
        self, features: Any, dataset_type: str
    ) -> Optional[List[Tuple[str, str]]]:
        """
        Validates the dataset schema against the template.
        Returns a list of tuples (original_name, new_name) for renaming, or None if validation fails.
        """
        if not dataset_type:
            logger.info("No dataset_type provided; skipping schema check.")
            return None

        if dataset_type not in TEMPLATE_COLUMN_MAPPINGS:
            logger.error(
                f"Unknown dataset_type '{dataset_type}'; skipping schema check."
            )
            return None

        template = TEMPLATE_COLUMN_MAPPINGS[dataset_type]
        required_columns = template.get("required_columns", {})
        renamable_columns = []
        missing_columns = []

        for role, possible_names in required_columns.items():
            if not any(name.lower() in features for name in possible_names):
                missing_columns.append((role, possible_names))
            else:
                # Identify columns that need renaming
                if role not in features:
                    for name in possible_names:
                        if name.lower() in features:
                            renamable_columns.append((name, role))
                            break

        if missing_columns:
            error_msgs = [
                f"role '{role}': expected one of {names}"
                for role, names in missing_columns
            ]
            logger.warning(
                f"Dataset schema validation failed for '{dataset_type}'. Missing: {'; '.join(error_msgs)}"
            )
            return None

        return renamable_columns

    def _rename_columns(
        self, dataset: Dataset, renamables: List[Tuple[str, str]]
    ) -> Dataset:
        for original, new in renamables:
            if original != new:
                dataset = dataset.rename_column(original, new)
                logger.info(f"Renamed column '{original}' to '{new}'")
        return dataset

    def _process_text_generation(self, dataset: Dataset, local_dataset_dir: Path):
        """Restructures text generation datasets into ChatML format and saves as Parquet."""
        first_split = list(dataset.keys())[0]
        features = dataset[first_split].features
        instr_feat = features.get("instruction")
        resp_feat = features.get("response")

        instr_is_label = isinstance(instr_feat, ClassLabel)
        resp_is_label = isinstance(resp_feat, ClassLabel)

        def convert_to_chatml(example):
            instr_raw = example["instruction"]
            resp_raw = example["response"]

            if instr_is_label and instr_raw is not None:
                instruction_str = instr_feat.int2str(instr_raw)
            else:
                instruction_str = str(instr_raw) if instr_raw is not None else ""

            if resp_is_label and resp_raw is not None:
                response_str = resp_feat.int2str(resp_raw)
            else:
                response_str = str(resp_raw) if resp_raw is not None else ""

            return {
                "messages": [
                    {"role": "user", "content": instruction_str},
                    {"role": "assistant", "content": response_str},
                ]
            }

        for split_name, split_dataset in dataset.items():
            split_output_dir = local_dataset_dir / split_name
            split_output_dir.mkdir(exist_ok=True)

            mapped_ds = split_dataset.map(
                convert_to_chatml,
                remove_columns=["instruction", "response"],
                batch_size=BATCH_SIZE_TEXT,
            )

            num_shards = math.ceil(max(1, mapped_ds.num_rows / EXPECTED_ROWS_PER_SHARD))

            for shard_idx in range(num_shards):
                shard_ds = mapped_ds.shard(num_shards, shard_idx)
                file_path = str(
                    split_output_dir / f"{shard_idx:04d}-of-{num_shards:04d}.parquet"
                )
                shard_ds.to_parquet(file_path, batch_size=BATCH_SIZE_PARQUET)

    def _process_image_classification(
    self, dataset: Dataset, local_dataset_dir: Path
    ) -> pd.DataFrame:
        """
        Saves the dataset to Parquet files organized by split.
        Format: split_name/0000-of-000n.parquet
        """
        import io



        # 1. Helper function to ensure images are stored as JPEG bytes (reduces Parquet size)
        def encode_image_to_bytes(batch):
            images = batch["image"]
            new_images = []
            for img in images:
                if img is None:
                    new_images.append(None)
                    continue
                
                try:
                    # Convert to RGB (handles RGBA/Grayscale issues)
                    img = img.convert("RGB")
                    # Save to bytes buffer as JPEG
                    with io.BytesIO() as buffer:
                        img.save(buffer, format="JPEG", quality=95)
                        new_images.append({"bytes": buffer.getvalue(), "path": None})
                except Exception:
                    new_images.append(None)
            
            return {"image": new_images}

        logger.info("Encoding images to Bytes for Parquet storage...")
        
        # Apply encoding. This ensures the column type in Parquet is binary/struct compatible
        dataset = dataset.map(
            encode_image_to_bytes,
            batched=True,
            batch_size=500,
            num_proc=NUM_CORES_IMAGE_PROC,    
        )
        # dataset = dataset.cast_column("image", Image())

        # 2. Iterate over every split (train, test, validation)
        for split_name, split_dataset in dataset.items():
            
            # Create directory: local_dataset_dir/train/
            split_dir = local_dataset_dir / split_name
            split_dir.mkdir(parents=True, exist_ok=True)

            logger.info(f"Processing split '{split_name}' with {len(split_dataset)} examples.")


            num_shards = math.ceil(max(1, len(split_dataset) / EXPECTED_ROWS_PER_SHARD))
            num_examples = len(split_dataset)
            shard_size = math.ceil(num_examples / num_shards)

            for shard_idx in range(num_shards):
                # Calculate the shard slice
                start_idx = shard_idx * shard_size
                end_idx = min(start_idx + shard_size, num_examples)
                
                # Slice the dataset if needed (for 1 shard, this is the whole dataset)
                shard_ds = split_dataset.select(range(start_idx, end_idx))

                # Format: 0000-of-0001.parquet
                file_name = f"{str(shard_idx).zfill(4)}-of-{str(num_shards).zfill(4)}.parquet"
                output_path = split_dir / file_name

                # Save to Parquet
                shard_ds.to_parquet(output_path)

                # Record metadata about the generated file
                # generated_files_metadata.append({
                #     "split": split_name,
                #     "file_path": str(output_path.relative_to(local_dataset_dir)),
                #     "num_examples": len(shard_ds),
                #     "shard_index": shard_idx
                # })

        logger.info(f"Dataset successfully saved to Parquet in {local_dataset_dir}")

        # # Return a DataFrame describing the generated Parquet files
        # return pd.DataFrame(generated_files_metadata)

    def _load_dataset(
        self, dataset_name: str, dataset_config: str,revision: str, temp_dir: Path, base_extra: dict
    ):
        """Loads the dataset from Hugging Face."""
        # 1. Check features via streaming first
        ds_stream = load_dataset(dataset_name, dataset_config, streaming=True)

        has_features = getattr(ds_stream[list(ds_stream.keys())[0]], "features", None) is not None
        if not has_features:
            raise ValueError("Dataset features could not be determined. (failed dataset)")

        

        snapshot_download(
        repo_id=dataset_name,
        revision=revision,
        local_dir=temp_dir / "dataset_files",
        local_dir_use_symlinks=False,
        repo_type="dataset")




        ds = load_dataset(
            path=str(temp_dir / "dataset_files"),
            name=dataset_config,
        )

        self._log_event(
            logging.INFO,
            "huggingface dataset downloaded successfully",
            "huggingface_handler",
            "dataset_downloaded",
            "success",
            base_extra,
        )
        return ds

    def _handle_restructuring(
        self, ds: Dataset, dataset_type: str, local_dataset_dir: Path, base_extra: dict
    ) -> bool:
        """
        Attempts to restructure the dataset based on type.
        Returns True if valid/successful (or if restructure wasn't needed), False if failed.
        """
        features = ds[list(ds.keys())[0]].features
        renamables = self._check_schema(features, dataset_type)

        # Check basic existence if no renames are needed
        is_schema_okay = False
        if dataset_type == "text_generation":
            is_schema_okay = "instruction" in features and "response" in features
        elif dataset_type == "image_classification":
            is_schema_okay = "image" in features and "label" in features

        if not (renamables or is_schema_okay):
            self._log_event(
                logging.ERROR,
                "schema enforcement failed for huggingface dataset.",
                "huggingface_handler",
                "column_rename",
                "failed",
                base_extra,
            )
            raise HTTPException(
                status_code=400,
                detail=f"Schema enforcement failed for huggingface dataset for type {dataset_type}",
            )

        # Apply renames
        ds = self._rename_columns(ds, renamables)

        # Process based on type
        if dataset_type == "text_generation":
            try:
                self._process_text_generation(ds, local_dataset_dir)
                self._log_event(
                    logging.INFO,
                    "text data restructured successfully",
                    "huggingface_handler",
                    "restructure",
                    "success",
                    base_extra,
                )
                return True
            except Exception as e:
                self._log_event(
                    logging.ERROR,
                    f"text restructure failed:{e}",
                    "huggingface_handler",
                    "restructure",
                    "failed",
                    base_extra,
                )
                raise HTTPException(
                    status_code=500, detail=f"Restructure failed for {dataset_type}"
                )

        elif dataset_type == "image_classification":
            try:
                self._process_image_classification(
                    ds, local_dataset_dir
                )
                # if final_metadata_df.empty:
                #     raise ValueError("Metadata dataframe is empty")

                # logger.info(
                #     f"Saving metadata for {len(final_metadata_df)} images to Parquet file."
                # )
                # final_metadata_df.to_parquet(
                #     local_dataset_dir / "structure.parquet", index=False
                # )

                self._log_event(
                    logging.INFO,
                    None,  # Message implied by log
                    "huggingface_handler",
                    "resturcture",
                    "success",
                    base_extra,
                )
                return True
            except Exception as e:
                self._log_event(
                    logging.ERROR,
                    f"error in restructuring huggingface dataset: {e}",
                    "huggingface_handler",
                    "restructure_failed",
                    "success",
                    base_extra,  # Check status key in original
                )
                raise HTTPException(
                    status_code=500, detail=f"Restructure failed for {dataset_type}"
                )

        return False

    def process(
        self,
        dataset_name: str,
        dataset_config: str,
        user_name: str,
        private: bool,
        base_extra: dict = {},
        restructure: bool = True,
        s3_config: dict = None,
        clearml_config: dict = None,
        revision: str = "main",
        dataset_type: str = None,
        tags: list = [],
        parent_id: Optional[str] = None
    ) -> dict:
        storage_handler = None
        try:
            # Setup Storage
            mount_dataset_name = dataset_name.replace("/", "-")
            storage_handler = DatasetStorageHandler(mount_dataset_name)
            temp_dir = storage_handler.temp_dir
            local_dataset_dir = temp_dir
            local_dataset_dir.mkdir(parents=True, exist_ok=True)

            # Pre-flight Size Check
            try:
                estimated_size = DatasetConditionChecker().check_huggingface_size(
                    dataset_name=dataset_name, revision=revision,size_limit_bytes=USER_STORAGE_SIZE_LIMIT_BYTES
                )
            except Exception as e:
                self._log_event(
                    logging.ERROR,
                    f"Dataset size check failed: {e}",
                    "huggingface_handler",
                    "check_size",
                    "failed",
                    base_extra,
                )
                raise HTTPException(
                    status_code=400, detail=f"Dataset size check failed: {e}"
                )

            # Download Dataset
            ds = self._load_dataset(dataset_name, dataset_config,revision,local_dataset_dir, base_extra)

            split_0 = list(ds.keys())[0]
            original_columns = ds[split_0].column_names
            rename_mapping = {col: col.lower() for col in original_columns if col != col.lower()}
            if rename_mapping:
                ds = ds.rename_columns(rename_mapping)
                logger.info(f"Converted column names to lowercase: {rename_mapping}")

            # Determine Processing Logic
            is_acceptable_type = dataset_type in ACCEPTABLE_TYPES
            restructure_valid = False

            if not is_acceptable_type:
                logger.warning("dataset_type is general: skipping restructuring")

            if restructure and is_acceptable_type:
                restructure_valid = self._handle_restructuring(
                    ds, dataset_type, local_dataset_dir, base_extra
                )
            else:
                if is_acceptable_type:
                    logger.info("restructure=False: not doing restructuring")

            # Fallback: Save to disk as-is if restructuring was skipped or failed (though handle_restructuring raises on explicit fail)
            # Note: The original logic implies if restructure failed (returned False from schema check), we save raw.
            if not restructure_valid:
                logger.info("Saving dataset to disk in raw format.")
                ds.save_to_disk(local_dataset_dir)

            # Cleanup Cache
            if (temp_dir / "cache").exists():
                shutil.rmtree(temp_dir / "cache")
                logger.info("deleted cache folder")

            if (temp_dir / "dataset_files").exists():
                shutil.rmtree(temp_dir / "dataset_files")
                logger.info("deleted dataset_files folder")
                
            # Post-processing Size/Space Validation
            if not estimated_size:
                dataset_size_mb = DatasetConditionChecker().dir_size_mb(
                    local_dataset_dir
                )
                estimated_size = dataset_size_mb * (1024**2)
                has_space, free_space_mb = DatasetConditionChecker().has_enough_space(
                    dataset_size_mb,USER_STORAGE_SIZE_LIMIT_BYTES/(1024**2)
                )

                if not has_space:
                    required_mb = dataset_size_mb * 1.2
                    message = (
                        f"Not enough disk space for dataset '{dataset_name}' (revision: {revision}). "
                        f"Required: ~{required_mb:.2f} MB, Available: {free_space_mb:.2f} MB"
                    )
                    logger.warning(message)
                    raise HTTPException(status_code=507, detail=message)
            else:
                logger.info(f"dataset size={estimated_size / (1024**2)}MB")

            # Generate Metadata
            api = HfApi()
            info = api.repo_info(dataset_name, repo_type="dataset")
            ds_id = storage_handler.generate_dataset_id()

            summary = {}

            if restructure_valid:
                summary["num_rows"] = sum([ds[split].num_rows for split in ds.keys()])
                summary["num_splits"] = len(ds.keys())
                summary["estimated_size_bytes"] = estimated_size
                summary["columns"] = list(ds[list(ds.keys())[0]].features.keys())

            metadata = DatasetMetadata(
                dataset_id=ds_id,
                dataset_name=mount_dataset_name,
                dataset_config=dataset_config,
                last_commit=getattr(info, "sha", None),
                last_modified=getattr(info, "last_modified", None).isoformat()
                if getattr(info, "last_modified", None)
                else None,
                user_name=user_name,
                private=private,
                revision=revision,
                source="huggingface",
                created_at=datetime.now().isoformat(),
                s3_path="",
                summary=summary,
                dataset_type=dataset_type,
                restructure_valid=restructure_valid,
                validation=False,
                tags=tags,
            )

            # Update ID in logs
            base_extra["dataset"] = base_extra.get("dataset", {})
            base_extra["dataset"]["id"] = ds_id
            self._log_event(
                logging.INFO,
                "metadata object created",
                "huggingface_handler",
                "metadata",
                "success",
                base_extra,
            )

            # Store to Persistent Storage (PVC/S3)
            try:
                stored_path = storage_handler.store_dataset(
                    local_dataset_dir,
                    metadata,
                    s3_config=s3_config,
                    clearml_config=clearml_config,
                    parent_id=parent_id
                )
            except Exception as e:
                self._log_event(
                    logging.ERROR,
                    f"error in saving huggingface dataset: {e}",
                    "huggingface_handler",
                    "error_saving",
                    "failed",
                    base_extra,
                )
                raise e

            return {
                "status": "ok",
                "message": "Hugging Face dataset stored successfully.",
                "dataset_id": ds_id,
                "stored_path": stored_path,
                "metadata" : metadata.model_dump(),
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Error processing Hugging Face dataset '{dataset_name}': {e}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=500, detail=f"Error with Hugging Face dataset: {e}"
            )
        finally:
            gc.collect()
            if storage_handler:
                storage_handler.cleanup_temp()


def process_huggingface_dataset(
    dataset_name: str,
    dataset_config: str,
    user_name: str,
    private: bool,
    dataset_type: str,
    s3_config: dict = None,
    tags: list = []
) -> dict:
    return HuggingFaceHandler().process(
        dataset_name=dataset_name,
        dataset_config=dataset_config,
        user_name=user_name,
        private=private,
        dataset_type=dataset_type,
        s3_config=s3_config,
    )
