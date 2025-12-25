"""Logs command for viewing zenable_mcp logs."""

import os
import platform
import shutil
import subprocess
import time
from pathlib import Path

import click

from zenable_mcp.logging.command_logger import log_command
from zenable_mcp.logging.local_logger import get_local_logger
from zenable_mcp.logging.logged_echo import echo
from zenable_mcp.logging.persona import Persona
from zenable_mcp.usage.manager import record_command_usage
from zenable_mcp.utils.log_parser import parse_log_line


def tail_file(file_path: Path, follow: bool = False, raw: bool = False) -> None:
    """Tail a log file, optionally following new entries.

    Args:
        file_path: Path to the log file
        follow: If True, follow the file like tail -f
        raw: If True, show raw logs; if False, show message field only
    """
    system = platform.system().lower()

    if follow:
        # Use native tail -f command for following
        if system == "windows":
            # On Windows, use PowerShell Get-Content -Wait
            powershell_path = shutil.which("powershell")
            if not powershell_path:
                echo("PowerShell not found in PATH", err=True)
                return

            cmd = [
                powershell_path,
                "-Command",
                f"Get-Content -Path '{file_path}' -Wait -Tail 10",
            ]

            # Create environment with empty PATH for security
            env = os.environ.copy()
            env["PATH"] = ""

            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env
            )

            try:
                for line in process.stdout:
                    if line.strip():
                        parsed = parse_log_line(line, raw)
                        if parsed:
                            echo(parsed)
            except KeyboardInterrupt:
                process.terminate()
                echo("\nStopped following logs", persona=Persona.POWER_USER)
        else:
            # On Unix-like systems, use tail -f
            tail_path = shutil.which("tail")
            if not tail_path:
                echo("tail command not found in PATH", err=True)
                return

            cmd = [tail_path, "-f", str(file_path)]

            # Create environment with empty PATH for security
            env = os.environ.copy()
            env["PATH"] = ""

            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env
            )

            try:
                for line in process.stdout:
                    if line.strip():
                        parsed = parse_log_line(line, raw)
                        if parsed:
                            echo(parsed)
            except KeyboardInterrupt:
                process.terminate()
                echo("\nStopped following logs", persona=Persona.POWER_USER)
    else:
        # Just cat the file
        if not file_path.exists():
            echo(f"Log file not found: {file_path}", err=True)
            return

        with open(file_path, "r") as f:
            for line in f:
                if line.strip():
                    parsed = parse_log_line(line, raw)
                    if parsed:
                        echo(parsed)


@click.command("logs", help="View zenable-mcp logs")
@click.option("-f", "--follow", is_flag=True, help="Follow log output (like tail -f)")
@click.option(
    "-r", "--raw", is_flag=True, help="Show raw log entries instead of just messages"
)
@click.option(
    "-n",
    "--lines",
    type=int,
    default=50,
    help="Number of lines to show (from end of file, default: 50)",
)
@click.option(
    "--clear",
    is_flag=True,
    help="Clear the log file (cannot be used with other options)",
)
@click.pass_context
@log_command
def logs(ctx, follow: bool, raw: bool, lines: int, clear: bool):
    """View zenable-mcp logs

    By default, shows the last 50 lines with only the message field from log entries.
    Use -n to specify a different number of lines to show.
    Use --raw to see the complete log entries.
    Use --follow to continuously monitor new log entries.
    Use --clear to delete the log file.
    """
    start_time = time.time()
    error = None

    try:
        # Check if --clear is used with other options
        if clear:
            if follow or raw or lines != 50:
                echo("Error: --clear cannot be used with other options", err=True)
                ctx.exit(1)

        # Get the log file path
        local_logger = get_local_logger()
        log_file_path = local_logger.strategy.get_log_file_path()

        # Handle --clear option
        if clear:
            if log_file_path.exists():
                try:
                    log_file_path.unlink()
                    echo(f"Log file cleared: {log_file_path}")
                except Exception as e:
                    echo(f"Error clearing log file: {e}", err=True)
                    ctx.exit(1)
            else:
                echo(f"No log file to clear at: {log_file_path}")
            return

        if not log_file_path.exists():
            echo(f"No log file found at: {log_file_path}", err=True)
            echo(
                "Run some zenable_mcp commands first to generate logs.",
                persona=Persona.POWER_USER,
            )
            return

        echo(f"Reading logs from: {log_file_path}", persona=Persona.POWER_USER)

        if follow:
            # When following, ignore the lines parameter and tail continuously
            tail_file(log_file_path, follow=True, raw=raw)
        else:
            # Show only last N lines (default 50)
            with open(log_file_path, "r") as f:
                all_lines = f.readlines()
                selected_lines = (
                    all_lines[-lines:] if len(all_lines) > lines else all_lines
                )
                for line in selected_lines:
                    if line.strip():
                        parsed = parse_log_line(line, raw)
                        if parsed:
                            echo(parsed)

    except Exception as e:
        error = e
        raise
    finally:
        duration_ms = int((time.time() - start_time) * 1000)
        record_command_usage(ctx=ctx, duration_ms=duration_ms, error=error)
