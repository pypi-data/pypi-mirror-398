"""Output formatters for conformance check results."""

import json
from enum import Enum
from typing import Protocol

import click

from zenable_mcp.logging.logged_echo import echo
from zenable_mcp.utils.conformance_status import ConformanceReport


class OutputFormat(Enum):
    """Supported output formats for conformance results."""

    TEXT = "text"
    JSON = "json"


class ConformanceFormatter(Protocol):
    """Protocol for conformance result formatters."""

    def format(self, report: ConformanceReport) -> str:
        """Format a conformance report."""
        ...


class TextFormatter:
    """Format conformance results as human-readable text."""

    def format(self, report: ConformanceReport) -> str:
        """Format conformance report as text."""
        lines = []

        # Overall summary
        status_str = report.overall_status.value.upper()
        lines.append(f"\nOverall Result: {status_str}")
        lines.append(f"Checks Run: {report.total_checks_run}")

        # Add pass/fail breakdown if there are failures or warnings
        if report.failed_checks > 0 or report.warning_checks > 0:
            lines.append(f"Passed: {report.passed_checks}")
            if report.failed_checks > 0:
                lines.append(f"Failed: {report.failed_checks}")
            if report.warning_checks > 0:
                lines.append(f"Warnings: {report.warning_checks}")

        # Add file-level details
        all_file_results = report.get_all_file_results()
        if all_file_results:
            lines.append("")  # Empty line before file results

            for file_result in all_file_results:
                lines.append(f"File: `{file_result.file_path}`")

                for check in file_result.checks:
                    status_display = check.status.value
                    lines.append(f"- Check `{check.check_name}`: `{status_display}`")

                    # Add findings if any
                    for finding in check.findings:
                        lines.append(f"  - Finding: {finding}")

        # Add error messages if any
        error_messages = report.get_error_messages()
        if error_messages:
            lines.append("")  # Empty line before errors
            for error in error_messages:
                lines.append(f"Error: {error}")

        return "\n".join(lines)


class JsonFormatter:
    """Format conformance results as JSON."""

    def format(self, report: ConformanceReport) -> str:
        """Format conformance report as JSON."""
        data = {
            "overall_result": report.overall_status.value.upper(),
            "summary": {
                "total_checks_run": report.total_checks_run,
                "total_files_checked": report.total_files_checked,
                "passed": report.passed_checks,
                "failed": report.failed_checks,
                "warnings": report.warning_checks,
            },
            "files": [],
        }

        # Add file results
        for file_result in report.get_all_file_results():
            file_data = {
                "path": str(file_result.file_path),
                "status": (
                    "FAIL"
                    if file_result.has_failures
                    else "WARNING"
                    if file_result.has_warnings
                    else "PASS"
                ),
                "checks": [],
            }

            for check in file_result.checks:
                check_data = {
                    "name": check.check_name,
                    "status": check.status.value,
                    "findings": check.findings,
                }
                file_data["checks"].append(check_data)

            data["files"].append(file_data)

        # Add errors if any
        error_messages = report.get_error_messages()
        if error_messages:
            data["errors"] = error_messages

        return json.dumps(data, indent=2)


class ConformanceOutputBuilder:
    """Builder for creating conformance check output in various formats."""

    def __init__(self, output_format: OutputFormat = OutputFormat.TEXT):
        """Initialize the output builder with a specific format."""
        self.output_format = output_format
        self._formatter = self._get_formatter()

    def _get_formatter(self) -> ConformanceFormatter:
        """Get the appropriate formatter for the output format."""
        if self.output_format == OutputFormat.JSON:
            return JsonFormatter()
        elif self.output_format == OutputFormat.TEXT:
            return TextFormatter()
        else:
            # Default to text format
            return TextFormatter()

    def build(self, report: ConformanceReport) -> str:
        """Build formatted output from conformance report."""
        return self._formatter.format(report)

    def display(self, report: ConformanceReport) -> None:
        """Display formatted output to console."""
        output = self.build(report)
        echo(output, log=False)


def show_conformance_summary(
    report: ConformanceReport, output_format: OutputFormat = OutputFormat.TEXT
) -> None:
    """
    Display conformance check summary using specified format.

    Args:
        report: ConformanceReport with check results
        output_format: Output format to use
    """
    # Display completion header
    echo("\n" + "=" * 50)
    echo(click.style("CONFORMANCE CHECK COMPLETE", bold=True))
    echo("=" * 50)

    # Build and display the report
    builder = ConformanceOutputBuilder(output_format)
    builder.display(report)
