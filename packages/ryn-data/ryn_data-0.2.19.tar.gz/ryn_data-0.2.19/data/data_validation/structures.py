from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List


@dataclass
class ValidationResult:
    """Holds the outcome of validating a single file."""

    file_path: Path
    is_valid: bool
    validator_used: str
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)
    duration_seconds: float | None = None

    def __repr__(self):
        status = "PASSED" if self.is_valid else "FAILED"
        duration_str = (
            f", duration={self.duration_seconds:.4f}s"
            if self.duration_seconds is not None
            else ""
        )
        return f"ValidationResult(file='{self.file_path}', status='{status}', errors={len(self.errors)}, warnings= {len(self.warnings)} {duration_str})"


@dataclass
class ValidationReport:
    """Aggregates results from all files validated in a directory run."""

    directory_path: Path
    results: List[ValidationResult] = field(default_factory=list)

    @property
    def overall_status(self) -> str:
        if not self.results:
            return "NO_FILES_VALIDATED"
        if all(r.is_valid for r in self.results):
            return "SUCCESS"
        if any(r.is_valid for r in self.results):
            return "PARTIAL_FAILURE"
        return "COMPLETE_FAILURE"

    def add_result(self, result: ValidationResult):
        self.results.append(result)

    def has_failures(self) -> bool:
        return any(not r.is_valid for r in self.results)

   
    @property
    def total_files(self) -> int:
        """Returns the total number of files validated."""
        return len(self.results)

    @property
    def passed_count(self) -> int:
        """Returns the number of files that passed validation."""
        return sum(1 for r in self.results if r.is_valid)

    @property
    def failed_count(self) -> int:
        """Returns the number of files that failed validation."""
        return self.total_files - self.passed_count

    # --- UPDATED: The __repr__ method ---
    def __repr__(self):
        """Provides a comprehensive, human-readable summary of the report."""
        summary_str = (
            f"{self.total_files} validated, "
            f"{self.passed_count} passed, "
            f"{self.failed_count} failed"
        )

        return (
            f"directory='{self.directory_path}'\n "
            f"status='{self.overall_status}'\n "
            f"summary='{summary_str}'"
        )
