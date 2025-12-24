import time
from functools import wraps

import glob
import logging
import os
import tarfile
import zipfile
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)

def time_validator(func):
    """
    A decorator that times the execution of a validator's `validate` method.
    It captures the result of the validation, adds a 'duration_seconds'
    attribute to it, and then returns the modified result.
    """
    @wraps(func)  # Preserves the original function's metadata (name, docstring, etc.)
    def wrapper(*args, **kwargs):
        # 1. Record the start time
        start_time = time.perf_counter()
        
        # 2. Call the original validate method (e.g., TabularValidator.validate)
        #    This will return a ValidationResult object.
        validation_result = func(*args, **kwargs)
        
        # 3. Record the end time and calculate the duration
        end_time = time.perf_counter()
        duration = end_time - start_time
        
        # 4. Add the duration to the result object
        #    We will add this field to the ValidationResult dataclass next.
        validation_result.duration_seconds = duration
        
        # 5. Return the modified result object
        return validation_result
        
    return wrapper
class ArchiveHandler:
    """
    Handles extraction and cleanup of archive files in a directory.
    Supports .zip, .tar, .tar.gz, .tgz, .tar.bz2 formats.
    Includes protection against Zip Slip vulnerabilities.
    """

    def __init__(self, source_dir: Path):
        self.source_dir = Path(source_dir)

    def _is_safe_path(self, base_dir: Path, path: str, follow_symlinks: bool = True) -> bool:
        """
        Prevents Zip Slip vulnerability by ensuring the intended extraction path
        is within the base_dir.
        """
        # Resolve the base directory to its absolute path
        match_path = base_dir.resolve()
        
        # specific logic to join and resolve the target path
        target_path = (base_dir / path).resolve()
        
        # If we want to prevent symlinks pointing outside, check resolved path.
        # Otherwise, basic Zip Slip is prevented by checking the prefix.
        return str(target_path).startswith(str(match_path))

    def extract_all(self) -> List[Path]:
        """
        Extracts all supported archive files into their respective containing directories.
        
        Returns:
            List[Path]: Absolute paths of all successfully processed archive files.
        """
        patterns = [
            "**/*.zip",
            "**/*.tar",
            "**/*.tar.gz",
            "**/*.tgz",
            "**/*.tar.bz2",
            "**/*.tbz2",
        ]

        all_archive_files = []
        for pattern in patterns:
            all_archive_files.extend(
                glob.glob(str(self.source_dir / Path(pattern)), recursive=True)
            )

        if not all_archive_files:
            logger.info("No supported archive files found in %s", self.source_dir)
            return []

        logger.info(
            "Found %d archive file(s) in %s", len(all_archive_files), self.source_dir
        )

        processed_archives: List[Path] = []
        
        for archive_path_str in all_archive_files:
            try:
                archive_path = Path(archive_path_str)
                extract_destination = archive_path.parent
                
                # Ensure destination exists
                extract_destination.mkdir(parents=True, exist_ok=True)

                # --- Logic to handle different archive types ---
                if archive_path.suffix == ".zip":
                    with zipfile.ZipFile(archive_path, "r") as archive_ref:
                        # 1. Validate all members before extracting
                        for member_name in archive_ref.namelist():
                            if not self._is_safe_path(extract_destination, member_name):
                                raise Exception(f"Zip Slip detected: {member_name} points outside target.")

                        logger.info("Extracting ZIP %s to %s", archive_path, extract_destination)
                        archive_ref.extractall(extract_destination)

                # Check for tar extensions (adjusted to catch .tar.gz properly)
                elif archive_path.name.endswith((".tar", ".tar.gz", ".tgz", ".tar.bz2", ".tbz2")):
                    with tarfile.open(archive_path, "r:*") as archive_ref:
                        # 1. Validate all members before extracting
                        # Note: getmembers() reads the whole archive, which prevents streaming 
                        # but is required to validate before writing files to disk.
                        members = archive_ref.getmembers()
                        for member in members:
                            if not self._is_safe_path(extract_destination, member.name):
                                raise Exception(f"Zip Slip detected: {member.name} points outside target.")
                        
                        logger.info("Extracting TAR %s to %s", archive_path, extract_destination)
                        
                        # Python 3.12+ has a 'filter' argument for added safety, 
                        # but the manual check above works on all versions.
                        archive_ref.extractall(path=extract_destination)

                else:
                    logger.warning("Skipping unrecognized archive format: %s", archive_path)
                    continue

                processed_archives.append(archive_path)

            except zipfile.BadZipFile:
                logger.warning("Skipping corrupt zip file: %s", archive_path_str)
            except tarfile.TarError as e:
                logger.warning("Skipping corrupt or invalid tar file %s: %s", archive_path_str, e)
            except Exception as e:
                logger.error(
                    "Failed to extract %s: %s. It will not be queued for cleanup.",
                    archive_path_str,
                    e,
                )

        return processed_archives

    def cleanup(self, archive_paths: List[Path]):
        """
        Deletes a list of archive files.
        """
        if not archive_paths:
            return

        logger.info("Cleaning up %d source archive(s)", len(archive_paths))
        for file_path in archive_paths:
            try:
                os.remove(file_path)
                logger.debug("Deleted archive %s", file_path)
            except FileNotFoundError:
                logger.warning("Archive not found for cleanup: %s", file_path)
            except Exception as e:
                logger.error("Failed to delete archive %s: %s", file_path, e)


