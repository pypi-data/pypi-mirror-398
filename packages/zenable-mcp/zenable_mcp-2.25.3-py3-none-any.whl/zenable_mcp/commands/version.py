import time

import click

from zenable_mcp import __version__
from zenable_mcp.logging.command_logger import log_command
from zenable_mcp.logging.logged_echo import echo
from zenable_mcp.usage.manager import record_command_usage


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.pass_context
@log_command
def version(ctx):
    """Show the zenable-mcp version"""
    start_time = time.time()
    error = None

    try:
        echo(__version__)

    except Exception as e:
        error = e
        raise
    finally:
        duration_ms = int((time.time() - start_time) * 1000)
        record_command_usage(ctx=ctx, duration_ms=duration_ms, error=error)
