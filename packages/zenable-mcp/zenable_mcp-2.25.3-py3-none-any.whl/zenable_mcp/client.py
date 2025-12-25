import logging
import os
import sys

import click

from zenable_mcp import __version__
from zenable_mcp.commands import check, doctor, hook, install, logout, logs, version
from zenable_mcp.logging.command_logger import log_command
from zenable_mcp.logging.local_logger import get_local_logger
from zenable_mcp.logging.logged_echo import echo
from zenable_mcp.logging.logging_config import configure_logging
from zenable_mcp.logging.persona import Persona
from zenable_mcp.usage.manager import record_command_usage
from zenable_mcp.version_check import check_for_updates


@click.group(context_settings=dict(help_option_names=["-h", "--help"]))
@click.option("--verbose", is_flag=True, help="Enable verbose output")
@click.option("--debug", is_flag=True, help="Enable debug output")
@click.pass_context
@log_command
def cli(ctx, verbose, debug):
    """Zenable - Clean Up Sloppy AI Code and Prevent AI-Created Security Vulnerabilities"""
    # Ensure that ctx.obj exists
    ctx.ensure_object(dict)

    # Check for ZENABLE_LOG_LEVEL environment variable
    env_log_level = os.environ.get("ZENABLE_LOG_LEVEL", "").upper()

    # Configure logging based on environment variable or flags
    if env_log_level == "DEBUG" or debug:
        log_level = logging.DEBUG
    elif env_log_level == "INFO" or verbose:
        log_level = logging.INFO
    else:
        log_level = logging.WARNING

    # Configure logging (both console and file)
    configure_logging(log_level)

    # Log where the local logs are being stored
    local_logger = get_local_logger()
    log_path = local_logger.strategy.get_log_file_path()
    echo(f"Local logs are being stored at: {log_path}", persona=Persona.POWER_USER)


# Add commands to the CLI group
cli.add_command(version)
cli.add_command(check)
cli.add_command(doctor)
cli.add_command(hook)
cli.add_command(install)
cli.add_command(logs)
cli.add_command(logout)


def main():
    """Main entry point"""
    # Check for updates before running the CLI
    check_for_updates(__version__)

    try:
        # Use standalone_mode=False to get exceptions instead of sys.exit
        cli(standalone_mode=False)
    except click.exceptions.ClickException as e:
        # Click exception (like invalid options) occurred during argument parsing
        # Record usage before letting Click handle it
        ctx = click.get_current_context(silent=True)

        # If no context from Click, try to get it from the exception's context attribute
        if not ctx and hasattr(e, "ctx"):
            ctx = e.ctx

        if ctx:
            # Record the failure with the exception
            record_command_usage(ctx=ctx, duration_ms=0, error=e)

        # Show the error and exit with proper code
        e.show()
        sys.exit(e.exit_code)


if __name__ == "__main__":
    main()
