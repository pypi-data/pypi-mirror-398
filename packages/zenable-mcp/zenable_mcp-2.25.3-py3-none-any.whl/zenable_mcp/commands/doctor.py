"""Doctor command for diagnosing and troubleshooting issues."""

import json
import os
import platform
import shutil
import subprocess
import time
from pathlib import Path

import click

from zenable_mcp import __version__
from zenable_mcp.exceptions import AuthenticationError
from zenable_mcp.logging.command_logger import log_command
from zenable_mcp.logging.local_logger import get_local_logger
from zenable_mcp.logging.logged_echo import echo
from zenable_mcp.logging.persona import Persona
from zenable_mcp.usage.manager import record_command_usage
from zenable_mcp.user_config.config_handler_factory import get_config_handler
from zenable_mcp.utils.log_parser import parse_log_line


def get_os_details() -> dict[str, str]:
    """Get operating system details."""
    return {
        "System": platform.system(),
        "Release": platform.release(),
        "Version": platform.version(),
        "Machine": platform.machine(),
        "Processor": platform.processor() or "N/A",
        "Python Version": platform.python_version(),
    }


def get_terminal_details() -> dict[str, str]:
    """Get terminal and shell details."""
    details = {}

    # Get shell
    shell = os.environ.get("SHELL", "N/A")
    details["Shell"] = shell

    # Get terminal type
    term = os.environ.get("TERM", "N/A")
    details["Terminal Type"] = term

    # Get terminal program (if available)
    term_program = os.environ.get("TERM_PROGRAM", "N/A")
    details["Terminal Program"] = term_program

    return details


def get_zenable_env_vars() -> dict[str, str]:
    """Get environment variables that start with ZENABLE_."""
    return {
        key: value for key, value in os.environ.items() if key.startswith("ZENABLE_")
    }


def get_uv_env_vars() -> dict[str, str]:
    """Get environment variables that start with UV_.

    Sanitizes sensitive values like tokens and passwords.
    Ref: https://docs.astral.sh/uv/reference/environment/
    """
    # List of sensitive UV env vars that should be redacted
    sensitive_vars = {
        "UV_PUBLISH_TOKEN",
        "UV_PUBLISH_PASSWORD",
        "UV_PYPI_TOKEN",
        "UV_INDEX_TOKEN",
        "UV_HTTP_BASIC_AUTH",
    }

    result = {}
    for key, value in os.environ.items():
        if key.startswith("UV_"):
            # Redact sensitive values
            if (
                key.upper() in sensitive_vars
                or "TOKEN" in key.upper()
                or "PASSWORD" in key.upper()
                or "AUTH" in key.upper()
            ):
                result[key] = "***REDACTED***"
            else:
                result[key] = value

    return result


def _check_command_version(command: str, env: dict[str, str]) -> str:
    """Check if a command is available and get its version.

    Args:
        command: Name of the command to check
        env: Environment variables to use for subprocess

    Returns:
        Version string or status message
    """
    try:
        cmd_path = shutil.which(command)
        if not cmd_path:
            return "NOT FOUND"

        cmd_path_obj = Path(cmd_path)
        if not cmd_path_obj.is_absolute():
            raise ValueError(f"{command} path is not absolute: {cmd_path}")

        result = subprocess.run(
            [cmd_path_obj, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            env=env,
        )
        return (
            result.stdout.strip()
            if result.returncode == 0
            else "Available but version check failed"
        )
    except Exception as e:
        return f"Available but error: {e}"


def check_dependencies() -> dict[str, str]:
    """Check if required dependencies are available."""
    # Create environment with empty PATH for security
    env = os.environ.copy()
    env["PATH"] = ""

    return {
        "git": _check_command_version("git", env),
        "uv": _check_command_version("uv", env),
    }


def check_config_files() -> dict[str, str]:
    """Check configuration source (API-based, not file-based)."""
    result = {}

    try:
        # Run this to check if the config handler can be initialized
        get_config_handler()
        result["Config Source"] = "API (tenant configuration from database)"
    except AuthenticationError:
        result["Config Source"] = "Not authenticated"
        result["Status"] = "⚠️  Authentication required to load configuration"
    except Exception as e:
        result["Config Source"] = "Error"
        result["Status"] = f"Error: {e}"

    return result


def get_loaded_config() -> dict[str, str]:
    """Get the loaded user configuration."""
    result = {}

    try:
        config_handler = get_config_handler()
        user_config, error_message = config_handler.load_config()

        if error_message:
            result["Status"] = f"Warning: {error_message}"
        else:
            result["Status"] = "Loaded successfully from API"
    except AuthenticationError:
        result["Status"] = "Not authenticated - cannot load configuration"
        return result
    except Exception as e:
        result["Status"] = f"Error loading config: {e}"
        return result

    # Convert the pydantic model to a dict for display
    config_dict = user_config.model_dump()

    # Format the config in a readable way
    result["Config"] = json.dumps(config_dict, indent=2, default=str)

    return result


def get_recent_logs(num_lines: int = 15, raw: bool = False) -> list[str]:
    """Get the last N lines from the zenable-mcp log file.

    Args:
        num_lines: Number of lines to retrieve from the end of the log file (default: 15)
        raw: If True, return raw log lines; if False, parse and format them

    Returns:
        List of formatted log lines (filtered to remove command completion logs)
    """
    try:
        logger = get_local_logger()
        log_file = logger.strategy.get_log_file_path()

        if not log_file.exists():
            return []

        # Read all lines and parse them, filtering out command logs
        with open(log_file, "r", encoding="utf-8") as f:
            all_lines = f.readlines()

            # Parse all lines to extract meaningful content (hide command logs for doctor)
            parsed_lines = []
            for line in reversed(all_lines):
                if line.strip():
                    # Hide command completion logs for cleaner doctor output
                    parsed = parse_log_line(
                        line, raw=raw, command_completion_logs=False
                    )
                    if parsed:
                        parsed_lines.append(parsed)
                        # Stop once we have enough useful logs
                        if len(parsed_lines) >= num_lines:
                            break

            # Reverse to show oldest first
            return list(reversed(parsed_lines))

    except Exception as e:
        return [f"Error reading log file: {e}"]


def run_diagnostics() -> dict[str, dict[str, str] | list[str]]:
    """Run all diagnostic checks."""
    return {
        "OS Details": get_os_details(),
        "Terminal Details": get_terminal_details(),
        "ZENABLE Environment Variables": get_zenable_env_vars(),
        "UV Environment Variables": get_uv_env_vars(),
        "Dependencies": check_dependencies(),
        "Configuration Files": check_config_files(),
        "Loaded Configuration": get_loaded_config(),
        "Recent Log Entries (last 15)": get_recent_logs(15),
    }


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.pass_context
@log_command
def doctor(ctx):
    """Diagnose and troubleshoot installation and client issues"""
    start_time = time.time()
    error = None

    try:
        echo("🔍 Running zenable-mcp diagnostics...\n", persona=Persona.USER)
        echo(f"zenable-mcp version: {__version__}\n", persona=Persona.USER)

        diagnostics = run_diagnostics()

        for section, details in diagnostics.items():
            echo(f"{'=' * 60}", persona=Persona.USER)
            echo(f"{section}", persona=Persona.USER)
            echo(f"{'=' * 60}", persona=Persona.USER)

            if not details:
                echo("  (none found)", persona=Persona.USER)
            elif isinstance(details, list):
                # Handle list-based sections (like logs)
                for line in details:
                    echo(f"  {line.rstrip()}", persona=Persona.USER)
            else:
                # Handle dict-based sections
                for key, value in details.items():
                    echo(f"  {key}: {value}", persona=Persona.USER)

            echo("", persona=Persona.USER)

        # Provide troubleshooting recommendations
        echo(f"{'=' * 60}", persona=Persona.USER)
        echo("Troubleshooting Recommendations", persona=Persona.USER)
        echo(f"{'=' * 60}", persona=Persona.USER)

        dependencies = diagnostics["Dependencies"]
        config_files = diagnostics["Configuration Files"]

        issues_found = False

        if dependencies.get("git") == "NOT FOUND":
            echo("  ⚠️  Git is not installed or not in PATH", persona=Persona.USER)
            echo(
                "     → Install git: https://git-scm.com/downloads",
                persona=Persona.USER,
            )
            issues_found = True

        if dependencies.get("uv") == "NOT FOUND":
            echo("  ⚠️  uv is not installed or not in PATH", persona=Persona.USER)
            echo("     → Install uv: https://docs.astral.sh/uv/", persona=Persona.USER)
            issues_found = True

        config_file_status = config_files.get("Config File", "")
        if "Not found" in config_file_status:
            echo(
                "  ⚠️  No configuration file found in current directory",
                persona=Persona.USER,
            )
            echo(
                "     → Run 'zenable-mcp install' to set up configuration",
                persona=Persona.USER,
            )
            issues_found = True
        elif "MULTIPLE FILES FOUND" in config_file_status:
            echo(
                "  ⚠️  Multiple configuration files found",
                persona=Persona.USER,
            )
            echo(
                "     → Remove duplicate config files to avoid confusion",
                persona=Persona.USER,
            )
            echo(
                "     → Keep only one: zenable_config.toml or zenable_config.yaml",
                persona=Persona.USER,
            )
            issues_found = True

        if not issues_found:
            echo("  ✓ No obvious issues detected", persona=Persona.USER)

        echo("", persona=Persona.USER)
        echo("For more help, visit: https://docs.zenable.io/", persona=Persona.USER)

    except Exception as e:
        error = e
        raise
    finally:
        duration_ms = int((time.time() - start_time) * 1000)
        record_command_usage(ctx=ctx, duration_ms=duration_ms, error=error)
