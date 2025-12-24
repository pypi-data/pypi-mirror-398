import abc
import logging
import math
import shutil
from functools import reduce
from pathlib import Path
from typing import Any, Dict, List, Tuple
from PIL import Image
import io
from fastapi import HTTPException
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import ArrayType, StructType,BinaryType

logger = logging.getLogger(__name__)


TEMPLATE_COLUMN_MAPPINGS = {
    "text_generation": {
        "doc_url": "https://huggingface.co/docs/trl/main/en/dataset_formats#prompt-completion",
        "required_columns": {
            "instruction": ["prompt", "instruction", "query", "question"],
            "response": [
                "completion",
                "response",
                "output",
                "answer",
                "answers",
                "target",
                "summary",
            ],
        },
        "optional_columns": {"input": ["input", "context"]},
    },
    "image_classification": {
        "required_columns": {
            # "image": [
            #     "image",
            #     "img"
            # ],
            "label": ["label", "labels", "class", "category", "target"],
            "file_path": [
                "image_path",
                "img_path",
                "file_path",
                "filepath",
            ],
        },
        "optional_columns": {},
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

class BaseRestructurer(abc.ABC):
    """Abstract base class for dataset restructurers."""

    def __init__(self, spark_session: SparkSession = None):
        self.spark = spark_session or self._get_spark_session()
        self._created_session = (
            spark_session is None
        )  # Flag to know if we should stop it

    def stop(self):
        # Only stop the session if this class created it
        if self.spark and self._created_session:
            self.spark.stop()
            logger.info("ending spark session")
            try:
                gateway = getattr(self.spark.sparkContext, "_gateway", None)
                if gateway:
                    gateway.shutdown()
                    logger.info("Py4J gateway shut down successfully.")
            except Exception as e:
                logger.warning(f"Error shutting down Py4J gateway: {e}")

    def _get_spark_session(self) -> SparkSession:
        """Initializes and returns a Spark session."""
        return (
            SparkSession.builder.appName("DatasetRestructuring")
            .master("local[8]")
            .config("spark.driver.memory", "4g")
            .config("spark.sql.execution.arrow.pyspark.enabled", "false")
            .config(
                "spark.driver.extraJavaOptions",
                "-Djava.security.egd=file:/dev/./urandom",
            )
            .config(
                "spark.executor.extraJavaOptions",
                "-Djava.security.egd=file:/dev/./urandom",
            )
            .getOrCreate()
        )

    def check_schema(self, task: str, columns) -> None:
        """
        Validates that the DataFrame contains all required columns.
        Raises ValueError if any are missing.
        """

        if task not in TEMPLATE_COLUMN_MAPPINGS:
            raise ValueError(f"Unsupported task type: {task}")

        required_columns = TEMPLATE_COLUMN_MAPPINGS[task]["required_columns"]
        print(list(required_columns.keys()))

        # if all(names for names in list(required_columns.keys()) in columns):
        #     return None

        if set(required_columns.keys()) <= set(columns):
            return None
        missing_columns = []
        renameable_columns = []
        for logical_col, possible_names in required_columns.items():
            if not any(col in columns for col in possible_names):
                missing_columns.append((logical_col, possible_names))

        if missing_columns:
            error_messages = [
                f"Missing required column for role '{role}': expected one of {names}"
                for role, names in missing_columns
            ]
            full_error_message = (
                f"Dataset schema validation failed for tag '{task}'. "
                f"Details: " + "; ".join(error_messages)
            )
            logger.error(full_error_message)
            raise HTTPException(
                status_code=400,
                detail=full_error_message,
            )
        else:
            # return renamable columns
            for role, possible_names in required_columns.items():
                for name in possible_names:
                    if name in columns:
                        logger.info(
                            f"Mapping column '{name}' to logical role '{role}'."
                        )
                        renameable_columns.append((name, role))
                        break
            logger.info(f"Dataset schema validation passed for tag '{task}'.")

        return renameable_columns

    @abc.abstractmethod
    def restructure(self, input_path: Path, output_path: Path) -> None:
        """
        Reads data from input_path, transforms it, and writes to output_path.
        """
        pass

    @property
    @abc.abstractmethod
    def task_type(self) -> str:
        """
        Returns the task type this restructurer handles.
        """
        pass


class ImageClassificationRestructurer(BaseRestructurer):
    """
    Restructures a dataset for Image Classification tasks.
    Moves images into a standardized directory structure and generates
    clean Parquet metadata.
    """

    TARGET_ROWS_PER_FILE = 5000

    def task_type(self) -> str:
        return "image_classification"

    def _load_from_folders(self, input_path: Path) -> DataFrame:
        """
        Scenario 2: Reads a nested directory structure where folders implies labels.
        """
        logger.info(f"Scanning directory for images: {input_path}")
        df = (
            self.spark.read.format("binaryFile")
            .option("pathGlobFilter", "*.{jpg,jpeg,png,JPG,JPEG,PNG,bmp,BMP,gif,GIF}")
            .option("recursiveFileLookup", "true")
            .load(str(input_path))
            .select("path")
        )

        df = df.withColumn(
            "file_path", F.regexp_replace(F.col("path"), "^file:/*", "/")
        )

        # Extract label (assuming parent folder is label)
        # /path/to/dataset/images/cat/001.jpg -> label = cat
        df = df.withColumn("label", F.element_at(F.split(F.col("file_path"), "/"), -2))
        return df

    def _load_data(self, input_path: Path) -> DataFrame:
        """
        Orchestrator for loading data from CSV metadata or direct folder scan.
        """
        images_path = input_path / "images"
        metadata_path = input_path / "metadata.csv"

        binary_df = (
            self.spark.read.format("binaryFile")
            .option("pathGlobFilter", "*.{jpg,jpeg,png,JPG,JPEG,PNG,bmp,BMP,gif,GIF}")
            .option("recursiveFileLookup", "true")
            .load(str(input_path))
        )
        binary_df = binary_df.withColumn(
            "abs_path", F.regexp_replace(F.col("path"), "^file:/*", "/")
        )

        binary_df.printSchema()
        # Check images directory existence
        if not images_path.exists() or not images_path.is_dir():
            # Sometimes datasets are flat, so we check input_path directly if images folder is missing
            # But standard requirement usually asks for 'images' folder.
            # If strictly required:
            if not (input_path).exists():
                raise FileNotFoundError(f"Input path not found: {input_path}")
            # Relaxed check: if no 'images' folder, assume input_path is the root
            images_path = input_path

        # 1. Try Loading Metadata CSV
        if metadata_path.exists():
            logger.info(f"Reading metadata from: {metadata_path}")
            
            # Read the CSV (Contains: file_path, label, split)
            meta_df = (
                self.spark.read.option("header", "true")
                .option("inferSchema", "true")
                .csv(str(metadata_path))
            )
            for c in meta_df.columns:
                meta_df = meta_df.withColumnRenamed(c, c.lower())

            # --- JOIN LOGIC ---
            # Challenge: CSV usually has relative paths ("images/cat/1.jpg")
            # BinaryDF has absolute paths ("/data/dataset/images/cat/1.jpg")
            
            # We construct the expected absolute path in the Metadata DF to enable a fast join
            # We assume input_path is the root.
            
            # 1. Clean CSV path (remove leading slash if present)
            source_col = "image_path" if "image_path" in meta_df.columns else "file_path"

            # Apply the transformation
            meta_df = meta_df.withColumn(
                "clean_rel_path", 
                F.regexp_replace(F.col(source_col), "^/", "")
            )
            
            # 2. Create 'join_key' by prepending the actual input_path
            # Note: str(input_path) needs to be passed safely to Spark
            root_path_str = str(input_path).rstrip("/") 
            
            meta_df = meta_df.withColumn(
                "abs_path_key", 
                F.concat(F.lit(root_path_str), F.lit("/"), F.col("clean_rel_path"))
            )

            # 3. Perform Inner Join to merge Metadata with Content
            # We keep columns from meta_df and the 'content' from binary_df
            df = meta_df.join(
                binary_df, 
                meta_df.abs_path_key == binary_df.abs_path, 
                "inner"
            ).select(
                meta_df["*"],           # All CSV columns (label, split, file_path)
                binary_df["content"]    # The image bytes
            )
            
            # Cleanup temp columns
            df = df.drop("clean_rel_path", "abs_path_key")
            
        else:
            # 2. Fallback to Folder Scan
            logger.info("No metadata.csv found. Inferring labels from folder structure.")
            
            # Use the binary_df directly, but we need to create 'label' and 'file_path'
            
            # Make 'file_path' relative to input_path (for consistency with CSV format)
            root_path_len = len(str(input_path).rstrip("/")) + 1 # +1 for the slash
            
            df = binary_df.withColumn(
                "image_path", 
                F.expr(f"substring(abs_path, {root_path_len + 1}, length(abs_path))")
            )
            
            # Infer label (folder name)
            # /.../images/cat/001.jpg  -> cat
            df = df.withColumn("label", F.element_at(F.split(F.col("abs_path"), "/"), -2))
            
            # Default split
            df = df.withColumn("split", F.lit("train"))

        logger.info(f"Loaded {df.count()} images with binary content.")
        return df

    def _normalize_and_validate(self, df: DataFrame) -> DataFrame:
        """
        Renames columns to standard schema and handles missing splits.
        """
        # 1. Ensure 'split' column
        if "split" not in df.columns:
            df = df.withColumn("split", F.lit("train"))
        else:
            df = df.fillna({"split": "train"})

        # 2. Map Columns (Schema Validation)
        # This uses the method from BaseRestructurer
        renameable_columns = self.check_schema(self.task_type(), df.columns)
        if renameable_columns:
            for original_name, logical_name in renameable_columns:
                df = df.withColumnRenamed(original_name, logical_name)

        # 3. Ensure essential columns exist
        required = ["file_path", "label"]
        for col_name in required:
            if col_name not in df.columns:
                # If we scanned folders, we have them. If we read CSV, we might miss them.
                raise ValueError(f"Dataset is missing required column: '{col_name}'")

        return df

    def _generate_target_paths(self, df: DataFrame) -> DataFrame:
        """
        Constructs the 'new_file_path' where images will be physically stored.
        Standard: images/<label>/<filename>
        """
        # Extract filename: '.../cat/image_01.jpg' -> 'image_01.jpg'
        df = df.withColumn(
            "filename", F.element_at(F.split(F.col("file_path"), "/"), -1)
        )

        # Construct new path: 'images/cat/image_01.jpg'
        # sanitize label slightly to avoid path issues (optional, but good practice)
        df = df.withColumn(
            "new_file_path",
            F.concat_ws("/", F.lit("images"), F.col("label"), F.col("filename")),
        )

        return df
    def _save_images_as_parquet(self, df: DataFrame, output_path: Path) -> None:
        """
        Saving images in parquet based on image split with JPEG compression.
        Format: train/part-00000-of-000N.parquet
        """
        
        def convert_to_jpeg_bytes(raw_data):
            """
            Takes raw binary data (PNG, BMP, etc.), converts to RGB,
            and returns JPEG compressed binary data.
            """
            if raw_data is None:
                return None
            try:
                img = Image.open(io.BytesIO(raw_data))
                img = img.convert("RGB")
                    # Save to bytes buffer as JPEG
                with io.BytesIO() as buffer:
                    img.save(buffer, format="JPEG", quality=95)
                    
                    return buffer.getvalue()
            except Exception:
                # If image is corrupt, return None
                return None

        jpeg_udf = F.udf(convert_to_jpeg_bytes, BinaryType())

        splits = [row.split for row in df.select("split").distinct().collect()]
        logger.info(f"Found splits to process: {splits}")

        for split_name in splits:
            logger.info(f"Processing split: '{split_name}'")
            
            # Filter for specific split
            split_df = df.filter(F.col("split") == split_name)

            row_count = split_df.count()
            if row_count == 0:
                continue

            # Calculate partitions
            num_partitions = max(1, math.ceil(row_count / self.TARGET_ROWS_PER_FILE))
            logger.info(f"Split '{split_name}' has {row_count} rows. Repartitioning into {num_partitions} files.")

            # 1. Prepare the Data
            # We assume 'content' exists (from binaryFile read). 
            # We apply the UDF to convert 'content' -> JPEG bytes.
            final_split_df = split_df.repartition(num_partitions)
            
            final_split_df = final_split_df.withColumn(
                "image",
                jpeg_udf(F.col("content"))
            )
            
            split_dir = output_path / split_name
            
            (
                final_split_df
                .write
                .mode("overwrite")
                .parquet(str(split_dir))
            )

            # 3. Rename and Move (Sharding Naming Logic)
            # Find the parts Spark created
            part_files = sorted(list(split_dir.glob("part-*.parquet")))
            
            # Update partition count in case Spark optimized empty partitions away
            actual_partitions = len(part_files)

            for idx, part_file in enumerate(part_files):
                new_name = (
                    split_dir / f"part-{idx:05d}-of-{len(part_files) - 1:05d}.parquet"
                )
                part_file.rename(new_name)
                logger.info(f"Renamed '{part_file.name}' to '{new_name.name}'")
        
            
            logger.info(f"Finished writing {actual_partitions} shards for {split_name}")

    def _copy_images(
        self, df: DataFrame, input_path: Path, output_path: Path
    ) -> Dict[str, Any]:
        """
        Physically copies images from source to destination.
        Returns statistics about the copy operation.
        """
        # Filter valid rows for copying
        paths_to_move = (
            df.select("file_path", "new_file_path", "label")
            .filter(F.col("label").isNotNull())
            .collect()
        )

        total_files = len(paths_to_move)
        logger.info(f"Starting physical copy of {total_files} image files...")

        copied_count = 0
        failed_count = 0
        total_bytes = 0

        for row in paths_to_move:
            # Handle relative vs absolute paths
            if str(row.file_path).startswith("/"):
                # If it looks absolute, check if it exists, otherwise try appending to input
                source_candidate = Path(row.file_path)
                if not source_candidate.exists():
                    source_candidate = input_path / row.file_path.lstrip("/")
            else:
                source_candidate = input_path / row.file_path

            dest_path = output_path / row.new_file_path

            if not source_candidate.exists():
                logger.warning(f"Source file missing: {source_candidate}")
                failed_count += 1
                continue

            try:
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(source_candidate), str(dest_path))
                copied_count += 1
                total_bytes += dest_path.stat().st_size
            except Exception as e:
                logger.error(f"Failed to copy {source_candidate}: {e}")
                failed_count += 1

        logger.info(f"Copy complete. Success: {copied_count}, Failed: {failed_count}")

        return {
            "copied_files": copied_count,
            "failed_files": failed_count,
            "total_image_bytes": total_bytes,
        }

    def _write_metadata(self, df: DataFrame, output_path: Path) -> List[str]:
        """
        Writes the metadata DataFrame to Parquet, cleans up Spark artifacts,
        and renames files for clarity.
        """
        output_metadata_path = output_path
        logger.info(f"Writing metadata to {output_metadata_path}")

        total_rows = df.count()
        if total_rows == 0:
            return []

        # Determine partition count
        num_partitions = 1

        # Prepare final DF
        final_write_df = df.select(
            F.col("new_file_path").alias("file_path"), "label", "split"
        )

        final_write_df = final_write_df.coalesce(1)
        (final_write_df.write.mode("append").parquet(str(output_metadata_path)))

        generated_files = []

        # 1. Delete _SUCCESS
        success_file = output_metadata_path / "_SUCCESS"
        if success_file.exists():
            success_file.unlink()

        success_crc = output_metadata_path / "._SUCCESS.crc"
        if success_crc.exists():
            success_crc.unlink()

        # 2. Rename Part Files
        parquets = sorted(list(output_metadata_path.glob("part-*.parquet")))
        for idx, part_file in enumerate(parquets):
            new_name = output_metadata_path / "structure.parquet"
            part_file.rename(new_name)
            generated_files.append(new_name.name)
            logger.info(f"Renamed metadata part to: {new_name.name}")

        # 3. Clean CRC
        crc_files = sorted(list(output_metadata_path.glob(".*.parquet.crc")))
        for crc_file in crc_files:
            # logic to match crc to new name or delete
            crc_file.unlink()  # Simplest approach is to delete CRCs for final output

        return generated_files

    def restructure(self, input_path: Path, output_path: Path) -> Dict[str, Any]:
        """
        Executes the restructuring process.
        Returns a summary dictionary.
        """
        logger.info(f"Initiating image classification restructuring from: {input_path}")

        # 1. Load Data
        df = self._load_data(input_path)



        # # 2. Validate & Normalize
        # df = self._normalize_and_validate(df)

        # # 3. Generate Target Paths
        # df = self._generate_target_paths(df)


        df.cache()

        # if df.rdd.isEmpty():
        #     raise ValueError("Dataset is empty after validation.")

        # --- Summary Calculation (Pre-computation) ---
        # Calculate Splits
        split_counts_rows = df.groupBy("split").count().collect()
        splits_stats = {row["split"]: row["count"] for row in split_counts_rows}

        # Calculate Labels Distribution
        label_counts_rows = df.groupBy("label").count().collect()
        label_stats = {str(row["label"]): row["count"] for row in label_counts_rows}

        total_rows = df.count()
        columns = ["file_path", "label", "split"]

        # # 4. Copy Images (Side Effect)
        # copy_stats = self._copy_images(df, input_path, output_path)

        # # 5. Write Metadata
        # metadata_files = self._write_metadata(df, output_path)


        self._save_images_as_parquet(df, output_path)

        df.unpersist()

        # 6. Build Final Summary
        summary = {
            "task_type": self.task_type(),
            "total_rows": total_rows,
            "columns": columns,
            "splits": list(splits_stats.keys()),
            "split_distribution": splits_stats,
            "label_distribution": label_stats,
            "num_classes": len(label_stats)
        }


        logger.info("Restructuring complete.")
        return summary


class TextGenerationRestructurer(BaseRestructurer):
    TARGET_ROWS_PER_FILE = 50000

    def is_structured(self, df: DataFrame) -> bool:
        """
        Checks if the DataFrame is already in ChatML format.
        messages: Array<Struct<role: string, content: string>>
        """
        if "messages" not in df.columns:
            return False

        dtype = df.schema["messages"].dataType
        if not isinstance(dtype, ArrayType):
            return False
        if not isinstance(dtype.elementType, StructType):
            return False

        field_names = df.schema["messages"].dataType.elementType.names
        return "role" in field_names and "content" in field_names

    def _read_from_directory(self, input_path: Path) -> DataFrame:
        """Scenario 1: Scans directory for files, reads, and merges them (Lazy Read)."""

        # Recursive glob to find files anywhere
        files_map = {
            "csv": [
                str(p) for p in input_path.glob("**/*.csv") if p.name != "structure.csv"
            ],
            "parquet": [str(p) for p in input_path.glob("**/*.parquet")],
            "json": [str(p) for p in input_path.glob("**/*.json")],
        }

        all_dfs = []

        # 1. Read CSVs
        if files_map["csv"]:
            logger.info(f"Reading {len(files_map['csv'])} CSV files...")
            # We can read all CSVs at once for better performance
            df = (
                self.spark.read.option("header", "true")
                .option("inferSchema", "true")
                .csv(files_map["csv"])
            )
            all_dfs.append(df)

        # 2. Read Parquets
        if files_map["parquet"]:
            logger.info(f"Reading {len(files_map['parquet'])} Parquet files...")
            df = self.spark.read.parquet(*files_map["parquet"])
            all_dfs.append(df)

        # 3. Read JSONs
        if files_map["json"]:
            logger.info(f"Reading {len(files_map['json'])} JSON files...")
            df = self.spark.read.option("multiline", "true").json(files_map["json"])
            all_dfs.append(df)

        if not all_dfs:
            raise FileNotFoundError(f"No valid data files found in: {input_path}")

        # 4. Merge all into one raw DataFrame
        # allowMissingColumns=True fills missing cols with nulls (crucial for mixed schemas)
        combined_df = reduce(
            lambda df1, df2: df1.unionByName(df2, allowMissingColumns=True), all_dfs
        )
        print(type(combined_df))
        return combined_df

    def _read_from_structure_file(
        self, structure_file: Path, input_path: Path
    ) -> DataFrame:
        """Scenario 2: Reads structure.csv to determine files, reads, and merges them."""
        logger.info("Processing structure.csv...")

        structure_df = self.spark.read.option("header", "true").csv(str(structure_file))

        for c in structure_df.columns:
            structure_df = structure_df.withColumnRenamed(c, c.lower())
        if "file_path" not in structure_df.columns:
            raise ValueError("structure.csv must contain a 'file_path' column.")

        rows = structure_df.collect()
        all_dfs = []

        for row in rows:
            clean_rel_path = row["file_path"].lstrip("/")
            full_path = input_path / clean_rel_path

            if not full_path.exists():
                logger.warning(f"File not found: {full_path}")
                continue

            try:
                # Read specific file type
                if full_path.suffix == ".csv":
                    df = (
                        self.spark.read.option("header", "true")
                        .option("inferSchema", "true")
                        .csv(str(full_path))
                    )
                elif full_path.suffix == ".parquet":
                    df = self.spark.read.parquet(str(full_path))
                elif full_path.suffix == ".json":
                    df = self.spark.read.option("multiline", "true").json(
                        str(full_path)
                    )
                else:
                    continue

                # Add split info immediately if present in structure file
                if "split" in row and row["split"]:
                    df = df.withColumn("split", F.lit(row["split"]))

                all_dfs.append(df)
            except Exception as e:
                logger.error(f"Failed to read {full_path}: {e}")

        if not all_dfs:
            raise ValueError("No valid files loaded from structure.csv")

        combined_df = reduce(
            lambda df1, df2: df1.unionByName(df2, allowMissingColumns=True), all_dfs
        )
        return combined_df

    def _normalize_and_validate(
        self, df: DataFrame, task_type: str = "text_generation"
    ) -> DataFrame:
        """
        Takes the combined DataFrame, performs schema mapping (coalescing),
        checks for structure, and drops nulls.
        """
        # 1. Check if already structured (ChatML)
        if self.is_structured(df):
            logger.info("Dataset is already in ChatML format.")
            # Even if structured, we might want to clean null messages if any
            return df.filter(F.col("messages").isNotNull())

        # 2. Not structured? We need to map columns.
        template = TEMPLATE_COLUMN_MAPPINGS.get(task_type)
        if not template:
            raise ValueError(f"Unknown task type: {task_type}")

        renamable_columns = self.check_schema("text_generation", df.columns)
        for original_name, logical_name in renamable_columns:
            df = df.withColumnRenamed(original_name, logical_name)

        return df

    def _load_data(self, input_path: Path) -> Tuple[DataFrame, Dict[str, Any]]:
        """
        Orchestrator for loading, merging, and normalizing.
        """
        structure_file = input_path / "structure.csv"

        # 1. Read & Merge
        if structure_file.exists():
            raw_df = self._read_from_structure_file(structure_file, input_path)
        else:
            raw_df = self._read_from_directory(input_path)

        logger.info(f"Combined raw columns: {raw_df.columns}")

        # 2. Normalize Schema & Clean Nulls
        final_df = self._normalize_and_validate(raw_df, "text_generation")

        return final_df

    def restructure(self, input_path: Path, output_path: Path) -> None:
        """
        Reads tabular data, validates the schema, and writes to a structured
        Parquet format partitioned by data split.
        """
        dataset_info = {}
        output_path / "dataset_info.json"

        logger.info(f"Initiating restructuring from: {input_path}")

        # --- Load Data & Build Summary ---
        df = self._load_data(input_path)

        # # --- Schema Validation & Renaming ---
        # renamable_columns = self.check_schema("text_generation", df.columns)
        # for original_name, logical_name in renamable_columns:
        #     df = df.withColumnRenamed(original_name, logical_name)

        # --- Filtering & Defaults ---
        # Filter out rows where essential data is missing

        if "split" not in df.columns:
            df = df.withColumn("split", F.lit("train"))
        else:
            df = df.fillna({"split": "train"})

        if df.rdd.isEmpty():
            raise ValueError(
                "The dataset is empty after loading and validation. Please check the input files."
            )

        # --- Transformation ---
        final_df = df.cache()

        if not self.is_structured(final_df):
            df = df.filter(
                F.col("instruction").isNotNull() & F.col("response").isNotNull()
            )
            # Apply ChatML formatting
            final_df = final_df.withColumn(
                "messages",
                F.array(
                    F.struct(
                        F.lit("user").alias("role"),
                        F.col("instruction").alias("content"),
                    ),
                    F.struct(
                        F.lit("assistant").alias("role"),
                        F.col("response").alias("content"),
                    ),
                ),
            )

            final_df = final_df.drop("instruction", "response")

        total_rows = final_df.count()

        # Update dataset info
        # dataset_info["schema"] = final_df.schema.jsonValue()

        # Calculate row count now (efficient since we cached) and add to summary

        splits = [row.split for row in final_df.select("split").distinct().collect()]
        logger.info(f"Found splits to process: {splits}")

        summary = {
            "num_rows": total_rows,
            "columns": final_df.columns,
            "splits": splits,
        }
        output_path.mkdir(parents=True, exist_ok=True)
        split_stats = {}

        # --- Writing Output ---
        for split_name in splits:
            logger.info(f"Processing split: '{split_name}'")
            split_df = final_df.filter(F.col("split") == split_name)

            row_count = split_df.count()
            split_stats[split_name] = {"row_count": row_count}

            if row_count == 0:
                logger.warning(f"Split '{split_name}' is empty. Skipping.")
                continue

            num_partitions = max(1, math.ceil(row_count / self.TARGET_ROWS_PER_FILE))
            logger.info(
                f"Split '{split_name}' has {row_count} rows. Repartitioning into {num_partitions} files."
            )

            if num_partitions == 1:
                # Use coalesce for reducing to 1 (avoids full shuffle)
                final_split_df = split_df.coalesce(1).drop("split")
                target_path = output_path / split_name
            else:
                # Use repartition if increasing partitions or balancing large data
                final_split_df = split_df.repartition(num_partitions).drop("split")
                target_path = output_path / split_name

            final_split_df.write.mode("overwrite").parquet(str(target_path))

            # Rename part-files
            part_files = sorted(list(target_path.glob("part-*.parquet")))
            for idx, part_file in enumerate(part_files):
                new_name = (
                    target_path / f"part-{idx:05d}-of-{len(part_files) - 1:05d}.parquet"
                )
                part_file.rename(new_name)
                logger.info(f"Renamed '{part_file.name}' to '{new_name.name}'")

            # Clean CRC files
            crc_files = sorted(list(target_path.glob(".*.parquet.crc")))
            for crc_file in crc_files:
                original_part_name = crc_file.name[1:-4]
                try:
                    original_part_file = Path(target_path, original_part_name)
                    idx = part_files.index(original_part_file)
                    new_crc_name = (
                        target_path
                        / f".part-{idx:05d}-of-{len(part_files) - 1:05d}.parquet.crc"
                    )
                    crc_file.rename(new_crc_name)
                except (ValueError, IndexError):
                    crc_file.unlink()

        final_df.unpersist()

        # Calculate bytes
        for split_name in splits:
            target_path = output_path / split_name
            if target_path.exists():
                split_size_bytes = sum(
                    f.stat().st_size for f in target_path.glob("*.parquet")
                )
                split_stats[split_name]["num_bytes"] = split_size_bytes

        dataset_info["splits"] = split_stats

        # with open(dataset_info_path, "w") as f:
        #     json.dump(dataset_info, f, indent=4)
        #     logger.info(f"Wrote dataset_info.json to {dataset_info_path}")

        logger.info("Dataset restructuring complete.")

        return summary

    def task_type(self) -> str:
        return "text_generation"



class ImageSegmentationRestructurer(BaseRestructurer):
    """
    Restructures a dataset for Image Segmentation tasks.

    This class reads a directory containing an 'images' folder, a 'masks'
    folder, and a 'metadata.csv' file. It joins the image and mask binary
    data with the metadata, and then writes the result into a partitioned
    Parquet dataset suitable for use with libraries like Hugging Face Datasets.

    The final structure will have columns for 'image' and 'mask', where each
    is a struct containing the file path and binary content.
    """

    TARGET_ROWS_PER_FILE = 2_000

    def restructure(self, input_path: Path, output_path: Path) -> None:
        """
        Reads image/mask data, joins with metadata, and writes to a structured
        Parquet format partitioned by data split (e.g., train/validation/test).
        """
        dataset_info = {}
        dataset_info_path = output_path / "dataset_info.json"
        metadata_path = input_path / "metadata.csv"
        if not metadata_path.exists():
            raise FileNotFoundError(
                f"Required 'metadata.csv' not found in {input_path}"
            )

        logger.info(f"Reading metadata from: {metadata_path}")
        df = (
            self.spark.read.option("header", "true")
            .option("inferSchema", "true")
            .csv(str(metadata_path))
        )

        # Ensure a 'split' column exists, defaulting to 'train'
        if "split" not in df.columns:
            df = df.withColumn("split", F.lit("train"))
        else:
            df = df.fillna({"split": "train"})

        # --- Read Image and Mask Binary Data ---
        logger.info("Reading raw image files...")
        image_binary_df = (
            self.spark.read.format("binaryFile")
            .load(str(input_path / "images" / "*"))
            .filter(F.col("length") > 0)
            .withColumn(
                "image_path", F.regexp_extract(F.col("path"), r"(images/.*$)", 1)
            )
            .withColumnRenamed("content", "image_content")
            .select("image_path", "image_content")
        )

        logger.info("Reading raw mask files...")
        mask_binary_df = (
            self.spark.read.format("binaryFile")
            .load(str(input_path / "masks" / "*"))
            .filter(F.col("length") > 0)
            .withColumn("mask_path", F.regexp_extract(F.col("path"), r"(masks/.*$)", 1))
            .withColumnRenamed("content", "mask_content")
            .select("mask_path", "mask_content")
        )

        # --- Join Metadata with Binary Data ---
        logger.info("Joining metadata with image and mask data...")
        # Inner join for images: an image must exist.
        joined_df = df.join(image_binary_df, "image_path", "inner")
        # Left join for masks: a mask might be null (e.g., for test set).
        joined_df = joined_df.join(mask_binary_df, "mask_path", "left")

        if joined_df.rdd.isEmpty():
            raise ValueError(
                "Join between metadata, images, and masks resulted in an empty dataset. "
                "Check that file paths in metadata.csv match actual files."
            )

        logger.info("Creating nested 'image' and 'mask' structs.")
        final_df = joined_df.select(
            F.col("split"),
            F.struct(
                F.col("image_path").alias("path"), F.col("image_content").alias("bytes")
            ).alias("image"),
            F.struct(
                F.col("mask_path").alias("path"), F.col("mask_content").alias("bytes")
            ).alias("mask"),
        ).cache()  # Cache for efficient access across multiple splits

        dataset_info["schema"] = final_df.schema.jsonValue()

        splits = [row.split for row in final_df.select("split").distinct().collect()]
        logger.info(f"Found splits to process: {splits}")

        output_path.mkdir(parents=True, exist_ok=True)

        split_stats = {}

        for split_name in splits:
            logger.info(f"Processing split: '{split_name}'")
            split_df = final_df.filter(F.col("split") == split_name)

            split_stats[split_name] = {
                "row_count": split_df.count(),
            }

            row_count = split_df.count()

            if row_count == 0:
                logger.warning(f"Split '{split_name}' is empty. Skipping.")
                continue

            num_partitions = max(1, math.ceil(row_count / self.TARGET_ROWS_PER_FILE))

            logger.info(
                f"Split '{split_name}' has {row_count} rows. Repartitioning into {num_partitions} files."
            )
            final_split_df = split_df.repartition(num_partitions).drop("split")

            target_path = output_path / split_name
            final_split_df.write.mode("overwrite").parquet(str(target_path))

            # --- Rename output files for cleaner formatting ---
            part_files = sorted(list(target_path.glob("part-*.parquet")))
            for idx, part_file in enumerate(part_files):
                new_name = (
                    target_path / f"part-{idx:05d}-of-{len(part_files) - 1:05d}.parquet"
                )
                part_file.rename(new_name)
                logger.info(f"Renamed '{part_file.name}' to '{new_name.name}'")

            # This part is optional but cleans up the checksum files too
            crc_files = sorted(list(target_path.glob(".*.parquet.crc")))
            for crc_file in crc_files:
                original_part_name = crc_file.name[
                    1:-4
                ]  # remove leading '.' and trailing '.crc'
                try:
                    # Find the index of the original part file to maintain numbering
                    original_part_file = Path(target_path, original_part_name)
                    idx = part_files.index(original_part_file)
                    new_crc_name = (
                        target_path
                        / f".part-{idx:05d}-of-{len(part_files) - 1:05d}.parquet.crc"
                    )
                    crc_file.rename(new_crc_name)
                except (ValueError, IndexError):
                    logger.warning(
                        f"Could not find matching part file for {crc_file.name}, deleting it."
                    )
                    crc_file.unlink()

        final_df.unpersist()
        for split_name in splits:
            target_path = output_path / split_name
            split_size_bytes = sum(
                f.stat().st_size for f in target_path.glob("*.parquet")
            )
            split_stats[split_name]["num_bytes"] = split_size_bytes

        dataset_info["splits"] = split_stats
        logger.info("Dataset restructuring complete.")

    def task_type(self) -> str:
        return "image_segmentation"