"""Data models for conformance check results."""

from enum import Enum
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class CheckStatus(Enum):
    """Status of a single conformance check."""

    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    ERROR = "error"


class CheckResult(BaseModel):
    """Result of a single conformance check on a file."""

    model_config = ConfigDict(strict=True)

    check_name: str
    status: CheckStatus
    findings: list[str] = Field(default_factory=list)
    file_path: Optional[Path] = None

    @property
    def has_issues(self) -> bool:
        """Check if this result has any issues."""
        return self.status != CheckStatus.PASS


class FileCheckResult(BaseModel):
    """Aggregated results for all checks on a single file."""

    model_config = ConfigDict(strict=True, arbitrary_types_allowed=True)

    file_path: Path
    checks: list[CheckResult]

    @property
    def has_failures(self) -> bool:
        """Check if any check failed on this file."""
        return any(c.status == CheckStatus.FAIL for c in self.checks)

    @property
    def has_warnings(self) -> bool:
        """Check if any check has warnings on this file."""
        return any(c.status == CheckStatus.WARNING for c in self.checks)

    @property
    def has_errors(self) -> bool:
        """Check if any check had errors on this file."""
        return any(c.status == CheckStatus.ERROR for c in self.checks)

    @property
    def all_passed(self) -> bool:
        """Check if all checks passed on this file."""
        return all(c.status == CheckStatus.PASS for c in self.checks)


class BatchCheckResult(BaseModel):
    """Results from a single batch of conformance checks."""

    model_config = ConfigDict(strict=True, arbitrary_types_allowed=True)

    batch_number: int
    file_results: list[FileCheckResult]
    error_message: Optional[str] = None
    checks_run_count: Optional[int] = None  # Actual count from MCP server

    @property
    def checks_run(self) -> int:
        """Total number of checks run in this batch."""
        # Use explicit count from MCP server if available, otherwise calculate from file_results
        if self.checks_run_count is not None:
            return self.checks_run_count
        return sum(len(fr.checks) for fr in self.file_results)

    @property
    def has_error(self) -> bool:
        """Check if this batch encountered a system error."""
        return self.error_message is not None or any(
            fr.has_errors for fr in self.file_results
        )

    @property
    def has_failures(self) -> bool:
        """Check if any file in this batch failed checks."""
        return any(fr.has_failures for fr in self.file_results)


class ConformanceReport(BaseModel):
    """Aggregated conformance check report across all batches."""

    model_config = ConfigDict(strict=True, arbitrary_types_allowed=True)

    batches: list[BatchCheckResult]
    file_metadata: dict[str, dict[str, Any]] = Field(default_factory=dict)

    @property
    def total_checks_run(self) -> int:
        """Total number of checks run across all batches."""
        return sum(b.checks_run for b in self.batches)

    @property
    def total_files_checked(self) -> int:
        """Total number of files checked."""
        return sum(len(b.file_results) for b in self.batches)

    @property
    def passed_checks(self) -> int:
        """Number of checks that passed."""
        count = 0
        for batch in self.batches:
            for file_result in batch.file_results:
                count += sum(
                    1 for c in file_result.checks if c.status == CheckStatus.PASS
                )
        return count

    @property
    def failed_checks(self) -> int:
        """Number of checks that failed."""
        count = 0
        for batch in self.batches:
            for file_result in batch.file_results:
                count += sum(
                    1 for c in file_result.checks if c.status == CheckStatus.FAIL
                )
        return count

    @property
    def warning_checks(self) -> int:
        """Number of checks with warnings."""
        count = 0
        for batch in self.batches:
            for file_result in batch.file_results:
                count += sum(
                    1 for c in file_result.checks if c.status == CheckStatus.WARNING
                )
        return count

    @property
    def overall_status(self) -> CheckStatus:
        """Determine overall status across all batches."""
        if any(b.has_error for b in self.batches):
            return CheckStatus.ERROR
        if any(b.has_failures for b in self.batches):
            return CheckStatus.FAIL
        if self.warning_checks > 0:
            return CheckStatus.WARNING
        return CheckStatus.PASS

    @property
    def has_findings(self) -> bool:
        """Check if there are any findings (failures, warnings, or errors)."""
        return self.overall_status != CheckStatus.PASS

    def get_all_file_results(self) -> list[FileCheckResult]:
        """Get all file results across all batches."""
        results = []
        for batch in self.batches:
            results.extend(batch.file_results)
        return results

    def get_failed_file_results(self) -> list[FileCheckResult]:
        """Get only file results with failures."""
        return [fr for fr in self.get_all_file_results() if fr.has_failures]

    def get_error_messages(self) -> list[str]:
        """Get all error messages from batches."""
        return [b.error_message for b in self.batches if b.error_message]

    @property
    def total_loc(self) -> int:
        """
        Total lines of code checked across all files.

        Returns:
            Sum of LOC from file_metadata
        """
        return sum(metadata.get("loc", 0) for metadata in self.file_metadata.values())

    @property
    def total_findings(self) -> int:
        """
        Total number of findings across all files.

        A finding is a specific issue identified within a check. A single failed
        check can have multiple findings.

        Returns:
            Sum of all findings from non-PASS checks
        """
        count = 0
        for batch in self.batches:
            for file_result in batch.file_results:
                for check in file_result.checks:
                    if check.status != CheckStatus.PASS:
                        # Count the findings within this check
                        count += len(check.findings)
        return count
