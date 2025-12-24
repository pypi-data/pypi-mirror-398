import json
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List

import cv2
import librosa
import nibabel as nib
import numpy as np
import polars as pl
import pydicom
from polars import LazyFrame
from pydicom.errors import InvalidDicomError

from data.data_validation.structures import ValidationResult
from data.data_validation.utils import time_validator


class BaseValidator(ABC):
    """
    Abstract base class for specialized validators.

    All validators must implement:
      - __init__(rules)
      - validate(file_path) -> ValidationResult
    """

    def __init__(self, rules: Dict[str, Any] | None = None):
        self.rules = rules or {}

    @abstractmethod
    def validate(self, file_path: Path) -> ValidationResult:
        """Run validation on the given file path."""
        ...






class TabularValidator(BaseValidator):
    """Validates and processes tabular datasets using Polars for performance."""

    def __init__(self, rules: Dict[str, Any]):
        super().__init__(rules)
        self.link_pattern = r"((?:https?://|ftp://|www\.)\S+)"

    @time_validator
    def validate(self, file_path: Path) -> ValidationResult:
        errors: List[Dict] = []
        warnings: List[Dict] = []

        try:
            lazy_df = self._scan_data(file_path)
            columns = lazy_df.columns
        except Exception as e:
            errors.append({"check": "file_read_process", "error": str(e)})
            return ValidationResult(file_path, False, "tabular", errors)
        errors.extend(self._check_required_columns(columns))

        # --- Perform fast, full-table aggregation checks ---
        agg_exprs = self._build_aggregation_expressions(columns)
        if agg_exprs:
            agg_results = self._execute_aggregation_checks(lazy_df, agg_exprs)
            errors.extend(self._process_aggregation_errors(agg_results))
            warnings.extend(self._process_aggregation_warnings(agg_results))

        # --- Perform detailed, row-level checks (like finding links) ---
        # This still reports warnings on the ORIGINAL data
        if file_path.suffix.lower()==".parquet":
            print("hello parquet")


        warnings.extend(self._find_and_report_links(lazy_df))
        

        self.process_data(file_path)
        

        print("hello parquet 2")
        return ValidationResult(
            file_path,
            is_valid=not errors,
            validator_used="tabular",
            errors=errors,
            warnings=warnings,
        )

    # --- NEW PUBLIC METHOD FOR TRANSFORMATION ---
    def process_data(self, file_path: Path, output_path: Path | None = None):
        """
        Scans a data file, replaces links with '[link]', and saves the result.
        
        Args:
            file_path: The path to the source file.
            output_path: The path to save the processed file. If None,
                         overwrites the original file (destructive).
        """
        # Default to overwriting if no output_path is given
        target_path = output_path if output_path is not None else file_path
        print(f"Processing {file_path} and writing to {target_path}")

        try:
            lazy_df = self._scan_data(file_path)
            string_cols = [
                col_name for col_name, col_type in lazy_df.schema.items() if col_type == pl.Utf8
            ]

            if not string_cols:
                print("No string columns found to process. File remains unchanged.")
                return

            replacement_exprs = [
                pl.col(c).str.replace_all(self.link_pattern, "[link]") for c in string_cols
            ]
            
            processed_df = lazy_df.with_columns(replacement_exprs).collect()

            ext = target_path.suffix.lower()
            if ext == ".csv":
                processed_df.write_csv(target_path)
            elif ext == ".parquet":
                # When writing, you can choose the compression. Snappy is a good default.
                processed_df.write_parquet(target_path, compression='snappy')
            else:
                raise ValueError(f"Writing to file type {ext} is not supported.")

            print(f"Successfully wrote processed file to: {target_path}")

        except Exception as e:
            print(f"Failed to process {file_path}: {e}")
            raise

    def _scan_data(self, file_path: Path) -> pl.LazyFrame:
        """Return a Polars LazyFrame from supported file types."""
        ext = Path(file_path).suffix.lower()
        if ext == ".csv":
            return pl.scan_csv(file_path, infer_schema_length=0, ignore_errors=True)
        if ext == ".parquet":
            return pl.scan_parquet(file_path)
        raise ValueError(f"Unsupported file type: {ext}")

    def _check_required_columns(self, actual_cols: List[str]) -> List[Dict]:
        """Verify required columns exist in schema."""
        required = self.rules.get("dataset", {}).get("required_columns", [])
        if not required:
            return []
        missing = sorted(set(required) - set(actual_cols))
        if missing:
            return [{"check": "required_columns", "error": f"Missing: {missing}"}]
        return []

    def _build_aggregation_expressions(self, columns: List[str]) -> List[pl.Expr]:
        exprs = []
        column_rules = self.rules.get("columns", {})
        for col in columns:
            if column_rules.get(col, {}).get("not_null"):
                exprs.append(pl.col(col).is_null().sum().alias(f"not_null_{col}"))
            exprs.append(pl.col(col).is_null().all().alias(f"fully_null_{col}"))
        exprs.append(
            pl.all_horizontal(pl.all().is_null()).sum().alias("fully_null_row_count")
        )
        return exprs

    def _execute_aggregation_checks(
        self, lazy_df: pl.LazyFrame, exprs: List[pl.Expr]
    ) -> pl.DataFrame:
        return lazy_df.select(exprs).collect()

    def _process_aggregation_errors(self, results: pl.DataFrame) -> List[Dict]:
        errors = []
        row = results.row(0, named=True)
        for name, val in row.items():
            if name.startswith("not_null_") and val > 0:
                col = name.replace("not_null_", "")
                errors.append(
                    {"check": "not_null", "column": col, "error": f"{val} nulls found"}
                )
        return errors

    def _process_aggregation_warnings(self, results: pl.DataFrame) -> List[Dict]:
        warnings = []
        row = results.row(0, named=True)
        for name, val in row.items():
            if name.startswith("fully_null_") and val:
                col = name.replace("fully_null_", "")
                warnings.append(
                    {
                        "check": "fully_null_column",
                        "column": col,
                        "warning": "Column contains only null values",
                    }
                )
        if row.get("fully_null_row_count", 0) > 0:
            warnings.append(
                {
                    "check": "fully_null_row",
                    "warning": f"{row['fully_null_row_count']} fully null row(s) found",
                }
            )
        return warnings

    def _find_and_report_links(self, lazy_df: LazyFrame) -> List[Dict]:
        """
        Finds web links in string columns and returns them as warnings.
        This method is for reporting purposes only.
        """
        warnings = []
        df_with_index = lazy_df.with_row_index()
        string_columns = [
    col_name for col_name, col_type in lazy_df.schema.items() if col_type == pl.Utf8]

        for col_name in string_columns:
            links_found = (
                df_with_index.filter(pl.col(col_name).str.contains(self.link_pattern))
                .select(
                    pl.col("index").alias("row_number"),
                    pl.col(col_name)
                    .str.extract(self.link_pattern, 1)
                    .alias("link_found"),
                )
                .collect()
            )
            for row in links_found.iter_rows(named=True):
                user_friendly_row = row["row_number"] + 2
                warnings.append(
                    {
                        "check": "contains_links",
                        "column": col_name,
                        "row": user_friendly_row,
                        "warning": f"Link '{row['link_found']}' found. replaced with [link]",
                    }
                )
                break
        return warnings


class ImageValidator(BaseValidator):
    @time_validator
    def validate(self, file_path: Path) -> ValidationResult:
        errors: List[Dict] = []
        warnings: List[Dict] = []
        try:
            image = cv2.imread(str(file_path))
            if image is None:
                errors.append(
                    {
                        "check": "file_read_exception",
                        "error": "File not loadable (may be corrupt or unsupported).",
                    }
                )
            else:
                warnings.extend(self._check_solid_color(image))
        except Exception as e:
            errors.append({"check": "file_read_exception", "error": str(e)})
        return ValidationResult(
            file_path, is_valid=not errors, validator_used="image", errors=errors,warnings=warnings
        )

    def _check_solid_color(self, image: np.ndarray) -> List[Dict]:
        if not self.rules.get("disallow_solid_color", True):
            return []
        min_val, max_val = np.min(image), np.max(image)
        if min_val != max_val:
            return []
        if min_val == 0:
            msg = "Image is completely black."
        elif min_val == 255:
            msg = "Image is completely white."
        else:
            msg = f"Image is solid color (value {min_val})."
        return [{"check": "solid_color", "warning": msg}]


class JsonValidator(BaseValidator):
    """
    Validates both standard JSON and JSON Lines (.jsonl) files.

    - For .json, it checks if the entire file is one valid JSON object.
    - For .jsonl, it checks if every line is an independent, valid JSON object.
    """

    def validate(self, file_path: Path) -> ValidationResult:
        """
        Dispatches validation based on the file extension. Defaults to standard
        JSON validation if the extension is not '.jsonl'.
        """
        if file_path.suffix.lower() == ".jsonl":
            return self._validate_jsonl(file_path)
        return self._validate_json(file_path)

    def _validate_json(self, file_path: Path) -> ValidationResult:
        """Validates a standard JSON file."""
        errors: List[Dict] = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                json.load(f)
        except Exception as e:
            errors.append({"check": "json_parse", "error": str(e)})

        return ValidationResult(
            file_path, is_valid=not errors, validator_used="json", errors=errors
        )

    def _validate_jsonl(self, file_path: Path) -> ValidationResult:
        """Validates a JSON Lines file line by line."""
        errors: List[Dict] = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                is_empty = True
                for line_num, line in enumerate(f, 1):
                    is_empty = False
                    # Skip empty lines, which can be valid in some contexts
                    if not line.strip():
                        continue
                    try:
                        json.loads(line)
                    except json.JSONDecodeError as e:
                        errors.append(
                            {
                                "check": "jsonl_line_parse",
                                "row": line_num,
                                "error": str(e),
                            }
                        )
                if is_empty:
                    # Optional: Add a check for empty files if that's considered invalid.
                    errors.append(
                        {"check": "empty_file", "error": "JSONL file is empty."}
                    )

        except FileNotFoundError:
            errors.append({"check": "file_read", "error": "File not found."})
        except Exception as e:
            # Catches other read errors, e.g., permission denied
            errors.append({"check": "file_read_process", "error": str(e)})

        return ValidationResult(
            file_path, is_valid=not errors, validator_used="jsonl", errors=errors
        )


class AudioValidator(BaseValidator):
    """
    Validates audio files using librosa.

    Checks for:
    - Loadability: If the file can be read as audio.
    - Silence: If the audio is completely or nearly silent.
    - Minimum Duration: If the audio is shorter than a specified threshold.
    """

    @time_validator
    def validate(self, file_path: Path) -> ValidationResult:
        errors: List[Dict] = []
        try:
            # sr=None preserves the native sample rate
            audio_data, sample_rate = librosa.load(str(file_path), sr=None)

            # Perform checks on the loaded audio data
            errors.extend(self._check_silence(audio_data))
            errors.extend(self._check_duration(audio_data, sample_rate))

        except Exception as e:
            # This will catch errors from librosa if the file is corrupt/unsupported
            errors.append({"check": "audio_loadable", "error": str(e)})

        return ValidationResult(
            file_path, is_valid=not errors, validator_used="audio", errors=errors
        )

    def _check_silence(self, audio_data: np.ndarray) -> List[Dict]:
        """Check if the audio is effectively silent."""
        if not self.rules.get("disallow_silence", True):
            return []

        # A small threshold to account for floating point inaccuracies or faint noise
        silence_threshold = self.rules.get("silence_threshold", 1e-6)

        if np.max(np.abs(audio_data)) < silence_threshold:
            return [{"check": "silent_audio", "error": "Audio is effectively silent."}]
        return []

    def _check_duration(
        self, audio_data: np.ndarray, sample_rate: int | float
    ) -> List[Dict]:
        """Check if the audio meets a minimum duration."""
        min_duration_sec = 0.5
        if not min_duration_sec:
            return []

        duration = librosa.get_duration(y=audio_data, sr=sample_rate)
        if duration < min_duration_sec:
            return [
                {
                    "check": "minimum_duration",
                    "error": f"Duration is {duration:.2f}s, less than required {min_duration_sec}s.",
                }
            ]
        return []


class TextValidator(BaseValidator):
    """
    Validates text-based files with built-in, sensible defaults.
    This version is designed to run without an external configuration.

    It checks for common issues like secrets, overly long lines, and bad encoding.
    """

    def __init__(self, rules: Dict[str, Any] | None = None):
        """Initializes the validator. The 'rules' are ignored in this implementation."""
        # We explicitly do not use the rules dictionary to rely on built-in logic.
        super().__init__({})

        # --- Define Hardcoded, "No-Config" Rules ---
        self.MAX_FILE_SIZE_MB = 2000  # Prevent validating huge binary files
        self.MAX_LINE_LENGTH = 10000  # Flag unnaturally long lines
        self.ENCODING = "utf-8"

        self.FORBIDDEN_PATTERNS = [
            re.compile(r"(?i)-----BEGIN (RSA|OPENSSH|EC) PRIVATE KEY-----"),
            re.compile(r"(?i)api_key\s*[:=]\s*['\"]?([a-zA-Z0-9_.-]{16,})['\"]?"),
            re.compile(r"(?i)secret_key\s*[:=]\s*['\"]?([a-zA-Z0-9_.-]{16,})['\"]?"),
            re.compile(r"(?i)password\s*[:=]\s*['\"]?(.{8,})['\"]?"),
            re.compile(r"sk_live_[0-9a-zA-Z]{24}"),  # Stripe LIive API Key
            re.compile(r"AKIA[0-9A-Z]{16}"),  # AWS Access Key D
            re.compile(r"xoxp-[0-9a-zA-Z-]{20,}"),  # Slack Token
            re.compile(
                r"\b[a-fA-F0-9]{40,}\b"
            ),  # Generic long hex string (e.g., SHA1/256)
        ]

    @time_validator
    def validate(self, file_path: Path) -> ValidationResult:
        errors: List[Dict] = []
        warnings: List[Dict] = []

        # 1. File-level checks (size, emptiness)
        try:
            errors.extend(self._check_file_size(file_path))
            if errors:
                return ValidationResult(
                    file_path, is_valid=False, validator_used="text", errors=errors
                )
        except Exception as e:
            errors.append({"check": "file_metadata_read", "error": str(e)})
            return ValidationResult(
                file_path, is_valid=False, validator_used="text", errors=errors
            )

        # 2. Line-by-line checks for memory efficiency
        failed_checks = set()
        try:
            with open(file_path, "r", encoding=self.ENCODING) as f:
                for line_num, line in enumerate(f, 1):
                    # Check for long lines
                    if "line_length" not in failed_checks:
                        err = self._check_line_length(line, line_num)
                        if err:
                            errors.append(err)
                            failed_checks.add("line_length")

                    # Check for forbidden patterns
                    if "forbidden_content" not in failed_checks:
                        err = self._check_forbidden_patterns(line, line_num)
                        if err:
                            errors.extend(err)
                            failed_checks.add("forbidden_content")
                    if "contains_links" not in failed_checks:
                        war = self.check_line_link(line, line_num)
                        if war:
                            warnings.append(war)
                            failed_checks.add("contains_links")
        except UnicodeDecodeError:
            errors.append(
                {
                    "check": "file_encoding",
                    "error": f"File is not valid {self.ENCODING}. Check file encoding.",
                }
            )
        except Exception as e:
            errors.append({"check": "file_read_process", "error": str(e)})

        return ValidationResult(
            file_path,
            is_valid=not errors,
            validator_used="text",
            errors=errors,
            warnings=warnings,
        )

    def _check_file_size(self, file_path: Path) -> List[Dict]:
        file_size_bytes = file_path.stat().st_size
        if file_size_bytes == 0:
            return [{"check": "empty_file", "error": "File is empty."}]

        file_size_mb = file_size_bytes / (1024 * 1024)
        if file_size_mb > self.MAX_FILE_SIZE_MB:
            return [
                {
                    "check": "file_size",
                    "error": f"File size {file_size_mb:.2f}MB exceeds maximum {self.MAX_FILE_SIZE_MB}MB.",
                }
            ]
        return []

    def check_line_link(self, line: str, line_num: int) -> Dict | None:
        link_pattern = r"((?:https?://|ftp://|www\.)\S+)"

        for match in re.finditer(link_pattern, line):
            return {
                "check": "contains_links",
                "row": line_num,
                "error": f"Line contains link matching: '{match.group(0)}'",
            }
        return None

    def _check_line_length(self, line: str, line_num: int) -> Dict | None:
        if len(line) > self.MAX_LINE_LENGTH:
            return {
                "check": "line_length",
                "row": line_num,
                "error": f"Line is too long ({len(line)} chars, max is {self.MAX_LINE_LENGTH}).",
            }
        return None

    def _check_forbidden_patterns(self, line: str, line_num: int) -> List[Dict] | None:
        errors: List[Dict] = []

        for pattern in self.FORBIDDEN_PATTERNS:
            for match in re.finditer(pattern, line):
                errors.append(
                    {
                        "check": "forbidden_content",
                        "row": line_num,
                        "error": f"Line contains sensitive pattern matching: '{match.group(0)}'",
                    }
                )
                break

        return errors if errors else None


class NumpyValidator(BaseValidator):
    """
    Validates NumPy files (.npy and .npz).

    Checks for:
    - Loadability: If the file can be read by np.load().
    - Dtype: Ensures array data types match an allowed list.
    - Finiteness: Checks for NaN or infinity values.
    - Shape/Dimensions: Validates against min/max dimensions and specific
      shape constraints.
    """

    @time_validator
    def validate(self, file_path: Path) -> ValidationResult:
        errors: List[Dict] = []
        try:
            # Use allow_pickle=False for security by default. Can be overridden in rules.
            allow_pickle = self.rules.get("allow_pickle", False)
            data = np.load(str(file_path), allow_pickle=allow_pickle)

            if isinstance(data, np.ndarray):
                # This is a .npy file containing a single array
                errors.extend(self._validate_array(data, "root_array"))
            elif hasattr(data, "files") and isinstance(data.files, list):
                # This is a .npz file (NpzFile object)
                if not data.files:
                    errors.append(
                        {
                            "check": "empty_npz",
                            "error": "NPZ archive contains no arrays.",
                        }
                    )
                for array_name in data.files:
                    errors.extend(self._validate_array(data[array_name], array_name))
                data.close()  # Important: close the file handle for .npz files
            else:
                errors.append(
                    {
                        "check": "unsupported_numpy_format",
                        "error": f"Loaded data is of an unexpected type: {type(data).__name__}",
                    }
                )

        except Exception as e:
            errors.append({"check": "file_read_or_parse", "error": str(e)})

        return ValidationResult(
            file_path, is_valid=not errors, validator_used="numpy", errors=errors
        )

    def _validate_array(self, array: np.ndarray, array_name: str) -> List[Dict]:
        """Runs a series of checks on a single numpy array."""
        array_errors: List[Dict] = []
        array_errors.extend(self._check_dtype(array, array_name))
        array_errors.extend(self._check_finiteness(array, array_name))
        return array_errors

    def _check_dtype(self, array: np.ndarray, array_name: str) -> List[Dict]:
        """Check if the array's dtype is in the allowed list from rules."""
        allowed_dtypes = self.rules.get("allowed_dtypes")
        if not allowed_dtypes:
            return []

        if str(array.dtype) not in allowed_dtypes:
            return [
                {
                    "check": "invalid_dtype",
                    "array": array_name,
                    "error": f"Dtype '{array.dtype}' is not in allowed list: {allowed_dtypes}",
                }
            ]
        return []

    def _check_finiteness(self, array: np.ndarray, array_name: str) -> List[Dict]:
        """Check for NaN or infinity values if disallowed by rules."""
        errors: List[Dict] = []
        # Optimization: only check for floats/complex where nan/inf are possible
        if not np.issubdtype(array.dtype, np.number) or np.issubdtype(
            array.dtype, np.integer
        ):
            return []

        if self.rules.get("disallow_nan", True) and np.isnan(array).any():
            errors.append(
                {
                    "check": "contains_nan",
                    "array": array_name,
                    "error": "Array contains NaN (Not a Number) values.",
                }
            )

        if self.rules.get("disallow_inf", True) and np.isinf(array).any():
            errors.append(
                {
                    "check": "contains_inf",
                    "array": array_name,
                    "error": "Array contains infinity values.",
                }
            )
        return errors


class MarkdownValidator(BaseValidator):
    @time_validator
    def validate(self, file_path: Path) -> ValidationResult:
        errors: List[Dict] = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                if not content.strip():
                    errors.append(
                        {"check": "empty_file", "error": "Markdown file is empty."}
                    )
                # Additional markdown-specific checks can be added here
        except Exception as e:
            errors.append({"check": "file_read_exception", "error": str(e)})
        return ValidationResult(
            file_path, is_valid=not errors, validator_used="markdown", errors=errors
        )


class DicomValidator(BaseValidator):
    """
    Validates DICOM (Digital Imaging and Communications in Medicine) files.

    This basic validator focuses on fundamental readability and structural checks.
    """

    @time_validator
    def validate(self, file_path: Path) -> ValidationResult:
        """
        Runs validation checks on a single DICOM file.
        """
        errors: List[Dict] = []
        try:
            # defer_size is a performance optimization for large files.
            dcm = pydicom.dcmread(
                str(file_path), defer_size="1 MB", stop_before_pixels=True
            )

            # If parsing succeeds, run more detailed structural checks.
            errors.extend(self._check_dicom_format(dcm))
            errors.extend(self._check_essential_uids(dcm))

        except InvalidDicomError as e:
            # This error is specific to pydicom and means the file is not a
            # valid DICOM object or is severely corrupted.
            errors.append(
                {
                    "check": "dicom_parse",
                    "error": f"File is not a valid DICOM format or is corrupt. Details: {e}",
                }
            )
        except Exception as e:
            # Catches other issues like file not found, permission errors, etc.
            errors.append({"check": "file_read_exception", "error": str(e)})

        return ValidationResult(
            file_path, is_valid=not errors, validator_used="dicom", errors=errors
        )

    def _check_dicom_format(self, dcm: pydicom.Dataset) -> List[Dict]:
        """
        Checks if the file follows the standard DICOM Part 10 format.
        A standard file must have a 128-byte preamble and a 'DICM' prefix.
        """
        # pydicom stores this information in the 'preamble' attribute.
        # If it's missing, dcmread would likely have read it as a non-standard file.
        if not hasattr(dcm, "preamble") or dcm.preamble is None:
            return [
                {
                    "check": "dicom_part10_format",
                    "error": "File is not a standard Part 10 DICOM file (missing 128-byte preamble and 'DICM' prefix).",
                }
            ]
        return []

    def _check_essential_uids(self, dcm: pydicom.Dataset) -> List[Dict]:
        """
        Checks for the presence of the most critical UIDs in the file meta information.
        Without these, a DICOM file is fundamentally uninterpretable.
        """
        errors = []
        # The File Meta Information group (0002) is essential.
        if not dcm.file_meta:
            return [
                {
                    "check": "file_meta_information",
                    "error": "File is missing the File Meta Information header (Group 0002).",
                }
            ]

        # SOPClassUID defines WHAT the object is (e.g., CT Image, MR Image).
        if "MediaStorageSOPClassUID" not in dcm.file_meta:
            errors.append(
                {
                    "check": "missing_sop_class_uid",
                    "error": "File Meta is missing MediaStorageSOPClassUID, so its type is unknown.",
                }
            )

        # TransferSyntaxUID defines HOW the pixel data is encoded (e.g., uncompressed, JPEG).
        if "TransferSyntaxUID" not in dcm.file_meta:
            errors.append(
                {
                    "check": "missing_transfer_syntax_uid",
                    "error": "File Meta is missing TransferSyntaxUID, so pixel data cannot be interpreted.",
                }
            )

        return errors


class NiftiValidator(BaseValidator):
    """
    Validates NIfTI files (.nii and .nii.gz).

    Checks for:
    - Loadability: If the file can be read by nibabel.
    - Header Integrity: Ensures essential header fields are present.
    - Data Integrity: Checks for NaN or infinity values in the image data.
    """

    @time_validator
    def validate(self, file_path: Path) -> ValidationResult:
        errors: List[Dict] = []
        try:
            img = nib.load(str(file_path))
            header = img.header
            data = img.get_fdata()

            errors.extend(self._check_header_integrity(header))
            errors.extend(self._check_data_integrity(data))

        except ImportError:
            errors.append(
                {
                    "check": "nibabel_not_installed",
                    "error": "nibabel library is not installed.",
                }
            )
        except Exception as e:
            errors.append({"check": "file_read_or_parse", "error": str(e)})

        return ValidationResult(
            file_path, is_valid=not errors, validator_used="nifti", errors=errors
        )

    def _check_header_integrity(self, header) -> List[Dict]:
        """Check for essential header fields."""
        errors: List[Dict] = []
        essential_fields = ["dim", "datatype", "pixdim"]

        for field in essential_fields:
            if field not in header:
                errors.append(
                    {
                        "check": "missing_header_field",
                        "field": field,
                        "error": f"Header is missing essential field: {field}",
                    }
                )
        return errors

    def _check_data_integrity(self, data: np.ndarray) -> List[Dict]:
        """Check for NaN or infinity values in the image data."""
        errors: List[Dict] = []

        if self.rules.get("disallow_nan", True) and np.isnan(data).any():
            errors.append(
                {
                    "check": "contains_nan",
                    "error": "Image data contains NaN (Not a Number) values.",
                }
            )

        if self.rules.get("disallow_inf", True) and np.isinf(data).any():
            errors.append(
                {
                    "check": "contains_inf",
                    "error": "Image data contains infinity values.",
                }
            )
        return errors
