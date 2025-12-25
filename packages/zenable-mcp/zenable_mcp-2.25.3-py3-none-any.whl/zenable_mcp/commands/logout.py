"""Logout command to clear local OAuth credentials."""

import shutil
import time
import webbrowser

import click

from zenable_mcp.constants import OAUTH_TOKEN_CACHE_DIR
from zenable_mcp.logging.command_logger import log_command
from zenable_mcp.logging.logged_echo import echo
from zenable_mcp.usage.manager import record_command_usage

AUTH0_LOGOUT_URL = "https://zenable.us.auth0.com/v2/logout"


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.option(
    "--all",
    "logout_all",
    is_flag=True,
    help="Also open Auth0 logout in browser to end remote session",
)
@click.pass_context
@log_command
def logout(ctx, logout_all: bool):
    """Clear local OAuth credentials and optionally end Auth0 session."""
    start_time = time.time()
    error = None

    try:
        if OAUTH_TOKEN_CACHE_DIR.exists():
            shutil.rmtree(OAUTH_TOKEN_CACHE_DIR)
            echo("Cleared local OAuth credentials")
        else:
            echo("No local credentials found")

        if logout_all:
            echo(f"Opening Auth0 logout: {AUTH0_LOGOUT_URL}")
            webbrowser.open(AUTH0_LOGOUT_URL)

    except Exception as e:
        error = e
        raise
    finally:
        duration_ms = int((time.time() - start_time) * 1000)
        record_command_usage(ctx=ctx, duration_ms=duration_ms, error=error)
