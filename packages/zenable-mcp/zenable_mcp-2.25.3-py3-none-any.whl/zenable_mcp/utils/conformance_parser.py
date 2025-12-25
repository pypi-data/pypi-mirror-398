"""Parser for converting MCP conformance responses to structured data models."""

import json
import logging
import re
from pathlib import Path
from typing import Any

from zenable_mcp.utils.conformance_status import (
    BatchCheckResult,
    CheckResult,
    CheckStatus,
    ConformanceReport,
    FileCheckResult,
)

LOG = logging.getLogger(__name__)


class ConformanceParser:
    """Parse MCP conformance check responses into structured data models."""

    @staticmethod
    def parse_check_status(status_str: str) -> CheckStatus:
        """Parse check status string to enum."""
        status_lower = status_str.lower().strip("`").strip()
        try:
            return CheckStatus(status_lower)
        except ValueError:
            # Default to ERROR for unknown statuses
            return CheckStatus.ERROR

    @staticmethod
    def parse_text_format(content_text: str) -> list[FileCheckResult]:
        """
        Parse text-formatted conformance results.

        Expected format:
        Overall Result: PASS/FAIL/WARNING/ERROR
        Checks Run: N

        File: `/path/to/file.py`
        - Check `check-name`: `pass`/`fail`
          - Finding: Details...
        """
        file_results = []

        # Split by "File:" to get individual file sections
        file_sections = re.split(r"\n(?=File:)", content_text)

        for section in file_sections:
            section = section.strip()
            if not section.startswith("File:"):
                continue

            # Extract file path
            file_match = re.match(r"File:\s*`?([^`\n]+)`?", section)
            if not file_match:
                continue

            file_path = Path(file_match.group(1).strip())
            checks = []

            # Extract check results for this file
            # Pattern: - Check `check-name`: `status`
            check_pattern = r"-\s*Check\s+`([^`]+)`:\s*`(pass|fail|warning|error)`"
            for check_match in re.finditer(check_pattern, section, re.IGNORECASE):
                check_name = check_match.group(1)
                status = ConformanceParser.parse_check_status(check_match.group(2))

                # Extract findings for this check (lines starting with "- Finding:")
                findings = []
                # Get the section after this check and before the next check or end
                check_end = check_match.end()
                next_check = re.search(r"-\s*Check\s+`", section[check_end:])
                if next_check:
                    check_section = section[check_end : check_end + next_check.start()]
                else:
                    check_section = section[check_end:]

                # Extract findings
                finding_pattern = r"-\s*Finding:\s*(.+?)(?=\n\s*-|\Z)"
                for finding_match in re.finditer(
                    finding_pattern, check_section, re.DOTALL
                ):
                    finding = finding_match.group(1).strip()
                    findings.append(finding)

                checks.append(
                    CheckResult(
                        check_name=check_name,
                        status=status,
                        findings=findings,
                        file_path=file_path,
                    )
                )

            if checks:
                file_results.append(FileCheckResult(file_path=file_path, checks=checks))

        return file_results

    @staticmethod
    def parse_json_format(content_text: str) -> list[FileCheckResult]:
        """
        Parse JSON-formatted conformance results.

        Note: MCP server currently returns markdown only, but this is kept
        as a fallback parser in case JSON format is added in the future.

        Expected format:
        {
            "file.py": {
                "status": "PASS",
                "checks": [...],
                "issues": [...]
            }
        }
        """
        try:
            data = json.loads(content_text)
        except json.JSONDecodeError:
            return []

        if not isinstance(data, dict):
            return []

        file_results = []

        for file_path_str, file_data in data.items():
            if not isinstance(file_data, dict):
                continue

            file_path = Path(file_path_str)
            checks = []

            # Handle simple status-only format
            if "status" in file_data and "checks" not in file_data:
                status = ConformanceParser.parse_check_status(file_data["status"])
                findings = file_data.get("issues", []) or file_data.get("findings", [])
                checks.append(
                    CheckResult(
                        check_name="conformance_check",
                        status=status,
                        findings=findings if isinstance(findings, list) else [],
                        file_path=file_path,
                    )
                )
            # Handle detailed format with multiple checks
            elif "checks" in file_data:
                for check_data in file_data["checks"]:
                    if not isinstance(check_data, dict):
                        continue
                    checks.append(
                        CheckResult(
                            check_name=check_data.get("name", "unknown"),
                            status=ConformanceParser.parse_check_status(
                                check_data.get("status", "error")
                            ),
                            findings=check_data.get("findings", []),
                            file_path=file_path,
                        )
                    )

            if checks:
                file_results.append(FileCheckResult(file_path=file_path, checks=checks))

        return file_results

    @staticmethod
    def parse_batch_result(
        batch_num: int, result_data: dict[str, Any]
    ) -> BatchCheckResult:
        """
        Parse a single batch result from MCP client.

        Args:
            batch_num: Batch number
            result_data: Dictionary with 'result', 'error', 'files' keys

        Returns:
            BatchCheckResult with parsed data
        """
        error_message = result_data.get("error")
        if error_message:
            return BatchCheckResult(
                batch_number=batch_num,
                file_results=[],
                error_message=error_message,
            )

        # Extract content text from result
        result = result_data.get("result")
        if not result:
            return BatchCheckResult(
                batch_number=batch_num,
                file_results=[],
                error_message="No results returned",
            )

        # Get text content
        content_text = ""
        if hasattr(result, "content") and result.content and len(result.content) > 0:
            content_text = (
                result.content[0].text
                if hasattr(result.content[0], "text")
                else str(result.content[0])
            ) or ""

        # Empty response is treated as PASS (no findings) rather than ERROR
        # This handles cases where text is None or empty string
        if not content_text:
            return BatchCheckResult(
                batch_number=batch_num,
                file_results=[],
                error_message=None,
            )

        # Extract checks_run count from header if present
        checks_run_count = None
        checks_run_match = re.search(r"Checks Run:\s*(\d+)", content_text)
        if checks_run_match:
            checks_run_count = int(checks_run_match.group(1))
            LOG.debug(
                f"Extracted checks_run_count={checks_run_count} from batch {batch_num}"
            )

        # Try markdown/text format first (MCP server's current format), then JSON as fallback
        file_results = ConformanceParser.parse_text_format(content_text)
        if not file_results:
            file_results = ConformanceParser.parse_json_format(content_text)

        return BatchCheckResult(
            batch_number=batch_num,
            file_results=file_results,
            error_message=None,
            checks_run_count=checks_run_count,
        )

    @staticmethod
    def parse_all_batches(
        batch_results: list[dict[str, Any]],
        file_metadata: dict[str, dict[str, Any]] | None = None,
    ) -> ConformanceReport:
        """
        Parse all batch results into a ConformanceReport.

        Args:
            batch_results: List of batch result dictionaries from MCP client
            file_metadata: Optional dict mapping file paths to metadata (e.g., {"path": {"loc": 123}})

        Returns:
            ConformanceReport with all parsed data and file metadata
        """
        batches = []
        for idx, batch_data in enumerate(batch_results, start=1):
            batch_num = batch_data.get("batch", idx)
            parsed_batch = ConformanceParser.parse_batch_result(batch_num, batch_data)
            batches.append(parsed_batch)

        return ConformanceReport(batches=batches, file_metadata=file_metadata or {})
