import glob
import logging
from pathlib import Path
from typing import Any, Dict, List, Type, Union

from data.data_validation.structures import ValidationReport, ValidationResult
from data.data_validation.utils import ArchiveHandler
from data.data_validation.validators import (
    AudioValidator,
    BaseValidator,
    ImageValidator,
    JsonValidator,
    TabularValidator,
    TextValidator,
    NumpyValidator,
    MarkdownValidator,
    DicomValidator,
    NiftiValidator, 
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


class DirectoryValidator:
    """
    Orchestrates the validation of an entire directory containing mixed file types.
    """

    def __init__(self, config: List[Dict[str, Any]], unzip_first: bool = True):
        self.config = config
        self.unzip_first = unzip_first
        self._validator_registry: Dict[str, Type[BaseValidator]] = {}
        self._register_default_validators()

    def _register_default_validators(self):
        """Registers built-in validators."""
        self._validator_registry = {
            "tabular": TabularValidator,
            "image": ImageValidator,
            "json": JsonValidator,
            "audio": AudioValidator,
            "text": TextValidator,
            "numpy": NumpyValidator,
            "markdown": MarkdownValidator,
            "dicom": DicomValidator,
            "nifti": NiftiValidator,

        }
        logger.info("Registered validators: %s", list(self._validator_registry.keys()))

    def register_validator(self, name: str, validator_cls: Type[BaseValidator]):
        """Allows external code to register new validators dynamically."""
        if not issubclass(validator_cls, BaseValidator):
            raise TypeError("Validator must subclass BaseValidator")
        self._validator_registry[name] = validator_cls
        logger.info("Registered custom validator: %s", name)

    def validate(
        self, directory_path: Path
    ) -> Union[ValidationReport, ValidationResult]:
        """
        Top-level validation method. Manages unzipping, validation, and cleanup.
        """
        # checking if input is a file or directory
        if directory_path.is_file():
            if directory_path.suffix in [
                ".zip",
                ".tar",
                ".tar.gz",
                ".tgz",
                ".tar.bz2",
                ".tbz2",
            ]:
                # If a single archive file is provided, extract it to a temp directory
                temp_dir = directory_path.parent / f"{directory_path.stem}_extracted"
                temp_dir.mkdir(exist_ok=True)
                logger.info(
                    "Single archive file detected. Extracting to temporary directory: %s",
                    temp_dir,
                )
                directory_path = temp_dir
            elif directory_path.suffix in [".csv", ".parquet"]:
                # If a single data file is provided, validate it directly
                logger.info(
                    "Single data file detected. Validating file: %s", directory_path
                )
                # Assuming tabular validator for single data files; could be enhanced to detect type
                return self._validate_single_file(directory_path, "tabular", {})
            elif directory_path.suffix in [".jpg", ".jpeg", ".png"]:
                logger.info(
                    "Single image file detected. Validating file: %s", directory_path
                )
                return self._validate_single_file(directory_path, "image", {})
            elif directory_path.suffix in [".json"]:
                logger.info(
                    "Single JSON file detected. Validating file: %s", directory_path
                )
                return self._validate_single_file(directory_path, "json", {})

        archives_to_cleanup: List[Path] = []

        # Step 1: Unzip archives if configured to do so
        if self.unzip_first:
            archive_handler = ArchiveHandler(directory_path)
            archives_to_cleanup = archive_handler.extract_all()

        report = self._validate_directory(directory_path)

        # Step 3: Cleanup extracted archives
        if archives_to_cleanup:
            ArchiveHandler(directory_path).cleanup(archives_to_cleanup)

        return report

    def _validate_directory(self, directory_path: Path) -> ValidationReport:
        report = ValidationReport(directory_path=directory_path)
        logger.info("Starting validation in directory: %s", directory_path)

        for task in self.config:
            path_pattern = task.get("path_pattern")
            validator_name = task.get("validator")
            rules = task.get("rules", {})
            task_name = task.get("name", "Unnamed Task")

            if not path_pattern or not validator_name:
                logger.warning("Skipping invalid task config: %s", task)
                continue

            validator_cls = self._validator_registry.get(validator_name)
            if not validator_cls:
                logger.warning(
                    "Unknown validator '%s' in task '%s'. Skipping.",
                    validator_name,
                    task_name,
                )
                continue

            
            full_pattern = str(Path(directory_path) / path_pattern)

            matched_files = glob.glob(full_pattern, recursive=True)
            if not matched_files:
                logger.info(
                    "No files matched pattern '%s' in '%s'",
                    path_pattern,
                    directory_path,
                )
                continue

            validator = validator_cls(rules=rules)
            for file_path in matched_files:
                try:
                    result: ValidationResult = validator.validate(Path(file_path))
                    report.add_result(result)
                except Exception as e:
                    logger.error("Validation failed for %s: %s", file_path, e)

        return report

    def _validate_single_file(
        self, file_path: Path, validator_name: str, rules: Dict[str, Any]
    ) -> ValidationResult:
        validator_cls = self._validator_registry.get(validator_name)
        if not validator_cls:
            raise ValueError(f"Unknown validator: {validator_name}")

        validator = validator_cls(rules=rules)
        return validator.validate(file_path)

    def __call__(
        self, directory_path: Path
    ) -> Union[ValidationReport, ValidationResult]:
        return self.validate(directory_path)
