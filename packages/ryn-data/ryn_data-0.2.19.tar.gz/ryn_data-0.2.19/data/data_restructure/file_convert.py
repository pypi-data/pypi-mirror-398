"""
This module provides a FileConverter class responsible for unifying file formats
after the validation stage. It is designed to be easily extensible to support
new conversion types.

Default behavior is to replace the source file with the converted version.
"""

import logging
from pathlib import Path
from typing import Callable, Dict, Tuple

import polars as pl

# Configure a basic logger for the module
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class FileConverter:
    """
    Handles the conversion of files from one format to another.

    The conversion logic is managed through a dispatch pattern:
    1. `CONVERSION_MAP`: Defines the desired target format for a given source format.
       e.g., ".csv" should become ".parquet".
    2. `_conversion_handlers`: A dictionary that maps a (source, target) format
       tuple to the specific function that performs the conversion.

    This design allows for easy addition of new converters without modifying the
    main `convert` method.
    """

    # --- Step 1: Define the conversion policy (Source Suffix -> Target Suffix) ---
    CONVERSION_MAP: Dict[str, str] = {
        ".csv": ".parquet",
        # Future conversions can be added here, e.g.:
        # ".json": ".parquet",
        # ".jpg": ".png",
    }

    def __init__(self):
        # --- Step 2: Register the handler functions for each conversion type ---
        self._conversion_handlers: Dict[
            Tuple[str, str], Callable[[Path, Path], None]
        ] = {
            (".csv", ".parquet"): self._convert_csv_to_parquet,
        }

    def convert(
        self,
        source_path: Path,
        destination_dir: Path | None = None,
        replace_source: bool = True,
    ) -> Path:
        """
        Converts a file to a unified format if a conversion rule exists.

        If no conversion is defined, the original path is returned.

        Args:
            source_path: The path to the file to be converted.
            destination_dir: The directory where the converted file will be
                             saved. If None, it defaults to the source file's
                             parent directory.
            replace_source: If True (default), the original source file will
                            be deleted upon successful conversion.

        Returns:
            The path to the newly converted file, or the original path if no
            conversion was performed.

        Raises:
            FileNotFoundError: If the source_path does not exist.
            NotImplementedError: If a conversion is defined in CONVERSION_MAP
                                 but no handler is registered for it.
            IOError: If the conversion process itself fails.
        """
        if not source_path.is_file():
            raise FileNotFoundError(f"Source file not found: {source_path}")

        source_suffix = source_path.suffix.lower()
        target_suffix = self.CONVERSION_MAP.get(source_suffix)

        if not target_suffix:
            logging.info(f"No conversion required for '{source_path.name}'.")
            return source_path

        dest_dir = destination_dir or source_path.parent
        dest_dir.mkdir(parents=True, exist_ok=True)
        destination_path = dest_dir / (source_path.stem + target_suffix)

        if destination_path.exists():
            logging.warning(
                f"Destination file already exists, skipping conversion: {destination_path}"
            )
            return destination_path

        handler = self._conversion_handlers.get((source_suffix, target_suffix))
        if not handler:
            raise NotImplementedError(
                f"No conversion handler implemented for {source_suffix} -> {target_suffix}"
            )

        logging.info(f"Converting '{source_path.name}' to '{destination_path.name}'...")
        try:
            # Execute the conversion
            handler(source_path, destination_path)
            logging.info(f"Successfully created '{destination_path.name}'.")

            # If successful, handle source file replacement
            if replace_source:
                try:
                    source_path.unlink()
                    logging.info(f"Source file '{source_path.name}' removed.")
                except OSError as e:
                    # Log error if deletion fails, but don't fail the operation
                    logging.error(f"Error removing source file {source_path}: {e}")
                    raise

            return destination_path

        except Exception as e:
            logging.error(f"Failed to convert {source_path}: {e}")
            # Ensure the partially created destination file is cleaned up on failure
            if destination_path.exists():
                destination_path.unlink()
            raise

    # --------------------------------------------------------------------------
    # Private Conversion Handler Methods
    # --------------------------------------------------------------------------

    def _convert_csv_to_parquet(self, source_path: Path, destination_path: Path):
        """
        Converts a CSV file to a Parquet file using Polars in a streaming manner.
        """
        try:
            lazy_df = pl.scan_csv(
                source_path, infer_schema_length=1000, ignore_errors=True
            )
            lazy_df.sink_parquet(destination_path, compression="zstd")
        except Exception as e:
            logging.error(f"Error during CSV to Parquet conversion: {e}")
            raise


class DirectoryConverter:
    """
    Converts all files in a directory according to the FileConverter rules.

    This class leverages the FileConverter to process each file in the
    specified directory, applying conversions as defined in the FileConverter's
    CONVERSION_MAP.
    """

    def __init__(self, directory_path: Path):
        self.file_converter = FileConverter()
        self.directory_path = directory_path

    def convert_directory(
        self,
        destination_dir: Path | None = None,
        replace_source: bool = True,
    ) -> Dict[Path, Path]:
        """
        Converts all files in the given directory according to conversion rules.

        Args:
            directory_path: The path to the directory containing files to convert.
            destination_dir: The directory where converted files will be saved.
                             If None, converted files are saved in their
                             original directories.
            replace_source: If True (default), original source files will be
                            deleted upon successful conversion.

        Returns:
            A dictionary mapping original file paths to their converted paths.
            Files that did not require conversion will map to their original path.

        Raises:
            NotADirectoryError: If the provided directory_path is not a directory.
            IOError: If any file conversion fails.
        """
        if not self.directory_path.is_dir():
            raise NotADirectoryError(f"Not a directory: {self.directory_path}")

        conversion_results = {}
        for file_path in self.directory_path.rglob("*"):
            if file_path.is_file():
                try:
                    if "metadata" not in file_path.name:
                        converted_path = self.file_converter.convert(
                            file_path, destination_dir, replace_source
                        )
                        conversion_results[file_path] = converted_path
                except Exception as e:
                    logging.error(f"Failed to convert file {file_path}: {e}")
                    raise

        return conversion_results
