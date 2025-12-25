"""Usage data management for zenable_mcp commands."""

import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from http.client import HTTPException

import click
import requests

from zenable_mcp import __version__
from zenable_mcp.constants import OAUTH_TOKEN_CACHE_DIR
from zenable_mcp.logging.logged_echo import echo
from zenable_mcp.logging.persona import Persona
from zenable_mcp.usage.fingerprint import get_system_fingerprint
from zenable_mcp.usage.models import (
    UsageEventData,
    ZenableMcpUsagePayload,
)
from zenable_mcp.usage.sender import send_usage_data
from zenable_mcp.utils.install_status import InstallResult

# Base Zenable URL (override with ZENABLE_URL env var)
_zenable_url = os.environ.get("ZENABLE_URL", "https://www.zenable.app").rstrip("/")

# Private usage API endpoint
_usage_api = f"{_zenable_url}/api/data/usage"

# Timeout for authenticated usage requests (in seconds)
AUTH_REQUEST_TIMEOUT = 5


def is_usage_enabled() -> bool:
    """
    Check if usage data collection is enabled.

    Returns:
        True if usage data collection is enabled, False if disabled via environment variable
    """
    return os.environ.get("ZENABLE_DISABLE_USAGE_TRACKING", "").lower() not in (
        "1",
        "true",
        "yes",
    )


def get_jwt_token_from_cache() -> str | None:
    """
    Extract JWT token from OAuth cache if available.

    FastMCP stores tokens in SQLite database (cache.db) with structure:
    - Table: Cache
    - Key format: "mcp-oauth-token::<url>"
    - Value: JSON blob with {"value": {"access_token": "...", ...}}

    Returns:
        JWT token string if available, None otherwise
    """
    try:
        # Check OAuth cache directory
        if not OAUTH_TOKEN_CACHE_DIR.exists():
            return None

        # Try SQLite database (current FastMCP format)
        cache_db = OAUTH_TOKEN_CACHE_DIR / "cache.db"
        if cache_db.exists():
            try:
                with sqlite3.connect(str(cache_db)) as conn:
                    cursor = conn.cursor()

                    # Query for OAuth token entries
                    # FastMCP stores tokens with key pattern "mcp-oauth-token::<url>"
                    cursor.execute(
                        "SELECT value FROM Cache WHERE key LIKE 'mcp-oauth-token::%'"
                    )
                    rows = cursor.fetchall()

                    for (value_blob,) in rows:
                        try:
                            # Value is stored as JSON blob
                            token_data = json.loads(value_blob)

                            # FastMCP structure: {"value": {"access_token": "...", "id_token": "...", ...}}
                            if "value" in token_data:
                                token_value = token_data["value"]
                                token = token_value.get(
                                    "access_token"
                                ) or token_value.get("id_token")
                                if token:
                                    return token

                        except (json.JSONDecodeError, KeyError, TypeError):
                            continue

            except sqlite3.Error:
                echo(
                    "Failed to extract authentication token from cache",
                    persona=Persona.DEVELOPER,
                    err=True,
                )
                return None

        return None

    except Exception:
        return None


def send_authenticated_usage(
    command_name: str,  # "check" or "hook"
    usage_data: dict,
    jwt_token: str | None,
) -> None:
    """
    Send usage data to authenticated data_api endpoint.

    Args:
        command_name: Command name ("check" or "hook")
        usage_data: Usage data dictionary
        jwt_token: JWT token from OAuth flow (if available)
    """
    if not jwt_token:
        return

    try:
        # Determine integration identifier
        integration = f"zenable_mcp/{command_name}"

        # Build request body
        request_body = {
            "integration": integration,
            "usage_data": usage_data,
        }

        # Send with JWT authentication
        response = requests.post(
            _usage_api,
            json=request_body,
            headers={
                "Authorization": f"Bearer {jwt_token}",
                "Content-Type": "application/json",
            },
            timeout=AUTH_REQUEST_TIMEOUT,
        )

        # Log response (2xx = success)
        if 200 <= response.status_code < 300:
            echo(
                f"Authenticated usage data sent successfully (HTTP {response.status_code})",
                persona=Persona.DEVELOPER,
            )
        else:
            echo(
                f"Authenticated usage tracking failed: HTTP {response.status_code}",
                err=True,
                persona=Persona.DEVELOPER,
            )

    except (
        requests.exceptions.Timeout,
        requests.exceptions.ConnectionError,
        HTTPException,
        json.JSONDecodeError,
        Exception,
    ):
        pass


def extract_command_info(ctx: click.Context) -> tuple[str, list[str]]:
    """
    Extract command name and arguments from click context.

    Args:
        ctx: Click context from command execution

    Returns:
        Tuple of (command_string, command_args_list)
        command_args_list is CLI-style args like ["--dry-run", "--global"]
    """
    # Build command string from context
    command_parts = []
    current_ctx = ctx

    # Walk up the context chain to build full command
    while current_ctx:
        if current_ctx.info_name:
            command_parts.insert(0, current_ctx.info_name)
        current_ctx = current_ctx.parent

    command_string = " ".join(command_parts)

    # Extract command arguments from sys.argv
    # Parse sys.argv directly to capture all flags regardless of position
    # This is more reliable than Click context after subcommands finish
    command_args = []

    # Build set of command names we know about
    command_names = set(command_parts)
    if ctx.invoked_subcommand:
        command_names.add(ctx.invoked_subcommand)

    # Parse all of sys.argv, collecting flags and their values
    # Skip: program name (index 0) and command names
    skip_next = False

    for i, arg in enumerate(sys.argv):
        # Skip program name
        if i == 0:
            continue

        # Skip if this arg is a value we already processed
        if skip_next:
            skip_next = False
            continue

        # Check if this is a flag
        if arg.startswith("-"):
            # This is a flag - add it
            command_args.append(arg)

            # Check if next arg is a value (not a flag and not a command)
            if i + 1 < len(sys.argv):
                next_arg = sys.argv[i + 1]
                # Normalize next_arg to check if it's a command
                normalized_next = next_arg.split("/")[-1]

                # If next is not a flag and not a command name, it's a value
                if (
                    not next_arg.startswith("-")
                    and normalized_next not in command_names
                ):
                    command_args.append(next_arg)
                    skip_next = True

    return command_string, command_args


def _map_command_to_activity_type(command_name: str) -> str:
    """Map command name to activity_type."""
    mapping = {
        "check": "check",
        "hook": "hook",
        "install": "install_mcp",  # will be more specific in the future
        "zenable-mcp": "help",  # Root command shows help
        "cli": "help",  # Alternative root command name
    }
    return mapping.get(command_name, command_name)


def _build_cli_parsing_error_data(
    error: click.exceptions.ClickException, activity_type: str
) -> dict | None:
    """Build minimal failure data for CLI parsing errors.

    Args:
        error: The Click exception that occurred
        activity_type: The activity type (install_mcp, check, hook, etc.)

    Returns:
        Dict with error data matching the schema, or None if not applicable
    """
    # Commands like doctor, version, logs don't require a data field
    # so we return None and let the schema validation handle it
    if activity_type in ["doctor", "version", "logs"]:
        return None

    # Determine specific error type from Click exception class
    error_type_name = type(error).__name__

    # Build error data based on activity type
    if activity_type == "install_mcp":
        return {
            "outcome": "failed",
            "results_by_ide": {},  # No IDEs attempted
            "stats": {
                "total_attempts": 0,
                "successful": 0,
                "already_installed": 0,
                "upgraded": 0,
                "failed": 1,  # One failure: the CLI parsing
                "capability_mismatch": 0,
            },
            "error_info": {
                "error_types": [
                    "cli_parsing_error",
                    error_type_name,
                ],  # Generic + specific
                "error_count": 1,
            },
        }
    elif activity_type == "check":
        return {
            "outcome": "failed",
            "zenable_mcp_version": __version__,
            # error_info omitted - CLI parsing errors don't fit the schema's error_type enum
            # The outcome="failed" and command_args are sufficient signal
        }
    elif activity_type == "hook":
        return {
            "outcome": "failed",
            "decision": "no_files",  # Closest semantic match - no files were processed
            "filtering_stats": {
                "total_files": 0,
                "filtered_files": 0,
                "processed_files": 0,
            },
            # error_info omitted - CLI parsing errors don't fit the schema's error_type enum
        }
    elif activity_type == "install_hook":
        return {
            "outcome": "failed",
            "hook_action": "no_change",  # Closest semantic match - nothing was changed
            # error_info omitted - CLI parsing errors don't fit the schema's error_type enum
        }

    # Unknown activity type - return None
    return None


def record_command_usage(
    ctx: click.Context,
    results: list[InstallResult] | None = None,
    duration_ms: int | None = None,
    error: Exception | None = None,
    **kwargs,
) -> None:
    """
    Record usage data for a zenable_mcp command.

    Sends usage data to the appropriate API endpoint:
    - check/hook commands WITH JWT → /api/data/usage (authenticated, includes detailed metrics)
    - check/hook commands WITHOUT JWT → /api/public/usage (anonymous tracking)
    - all other commands → /api/public/usage (anonymous: install, doctor, version, logs)

    Args:
        ctx: Click context from command execution
        results: Optional list of InstallResult objects from IDE operations
        duration_ms: Command execution duration in milliseconds
        error: Optional exception if command failed
        **kwargs: Additional data to include (e.g., loc, finding_suggestion, conformance metrics)
    """
    # Check if usage data collection is disabled
    if not is_usage_enabled():
        return

    try:
        # Get system fingerprint
        system_info, system_hash = get_system_fingerprint()

        # Extract command info
        command_string, command_args = extract_command_info(ctx)

        # Determine command name and activity type
        # Walk up context chain to find the top-level command (install, check, hook, etc.)
        # For subcommands like "install mcp", we want "install_mcp" not just "mcp" or "install"
        command_name = ctx.info_name  # Start with current command

        # If this is a subcommand (has a parent that's not the root), build the full command path
        # Top-level commands have the root "zenable-mcp" as their parent
        if ctx.parent and ctx.parent.parent and ctx.parent.info_name:
            # This is a subcommand (like "mcp" under "install" or "hook" under "install")
            # Build the full command name: "install_mcp" or "install_hook"
            parent_name = ctx.parent.info_name
            current_name = ctx.info_name
            # For install subcommands, create the full activity type
            if parent_name == "install":
                command_name = f"{parent_name}_{current_name}"
            else:
                command_name = parent_name

        activity_type = _map_command_to_activity_type(command_name)

        # Determine event type and outcome
        if error:
            event = "completed"  # still completed, just with error
            error_message = str(error)
        else:
            event = "completed"
            error_message = None

        # Default duration if not provided
        if duration_ms is None:
            duration_ms = 0

        # Determine which endpoint to use based on command type
        is_check_or_hook = command_name in ["check", "hook"]

        # Get JWT token for authenticated endpoints
        jwt_token = get_jwt_token_from_cache()

        # 1. Send to authenticated data_api endpoint (for check/hook WITH JWT only)
        if is_check_or_hook and jwt_token:
            # Build legacy format for authenticated endpoint
            usage_data = {
                "command": command_string,
                "command_args": command_args,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "success": error is None,
                "error_message": error_message,
                "zenable_mcp_version": __version__,
                "duration_ms": duration_ms,
                "loc": kwargs.get("loc", 0),
                "finding_suggestion": kwargs.get("finding_suggestion", 0),
            }

            # Add metrics
            for metric in [
                "passed_checks",
                "failed_checks",
                "warning_checks",
                "total_checks_run",
                "total_files_checked",
            ]:
                if metric in kwargs:
                    usage_data[metric] = kwargs[metric]

            send_authenticated_usage(command_name, usage_data, jwt_token)

        # 2. Send to public API for all other cases:
        #    - check/hook WITHOUT JWT (anonymous usage tracking)
        #    - install, doctor, version, logs (always anonymous)
        else:
            # For Click exceptions (CLI parsing errors), build minimal error data
            # This tracks UX issues like typos in flags (e.g., --helpo instead of --help)
            event_data = None
            if error and isinstance(error, click.exceptions.ClickException):
                event_data = _build_cli_parsing_error_data(error, activity_type)
                echo(
                    f"Tracking CLI parsing error: {type(error).__name__}",
                    persona=Persona.DEVELOPER,
                )

            # All commands can be tracked anonymously via public API
            # Server has specific models for each activity type:
            # - InstallMcpEvent (install command)
            # - CheckEvent, HookEvent (check/hook without auth)
            # - DoctorEvent, VersionEvent, LogsEvent (simple commands)
            usage_event = UsageEventData(
                activity_type=activity_type,
                event=event,
                timestamp=datetime.now(timezone.utc),
                duration_ms=duration_ms,
                command_args=command_args,
                zenable_mcp_version=__version__,
                data=event_data,
            )

            payload = ZenableMcpUsagePayload(
                system_info=system_info,
                system_hash=system_hash,
                usage_data=usage_event,
            )

            send_usage_data(payload)

    except Exception as e:
        # Never fail the main command due to usage data errors
        echo(
            f"Failed to record usage data: {type(e).__name__}: {e}",
            err=True,
            persona=Persona.DEVELOPER,
        )
