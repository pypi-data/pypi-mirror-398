"""Shared handler for processing repository selection results."""

from pathlib import Path

import click

from zenable_mcp.exit_codes import ExitCode
from zenable_mcp.utils.cli_validators import handle_exit_code
from zenable_mcp.utils.repo_selector import change_to_selected_repository


def handle_repository_selection(
    selected: list[Path] | Path | str | None,
    ctx: click.Context,
    exit_on_cancel: bool = True,
) -> tuple[bool, bool]:
    """Handle the result from prompt_for_repository_selection.

    Args:
        selected: Result from prompt_for_repository_selection
        ctx: Click context
        exit_on_cancel: Whether to exit if user cancels (default True)

    Returns:
        Tuple of (recursive, is_global) flags
    """
    recursive = ctx.obj.get("recursive", False)
    is_global = ctx.obj.get("is_global", False)

    if selected == "all":
        # User wants to install in all repos - set recursive flag
        # Note: This is for numbered list "all" option, not TUI
        recursive = True
        ctx.obj["recursive"] = True
    elif selected == "global":
        # User wants global installation
        is_global = True
        ctx.obj["is_global"] = True
    elif isinstance(selected, list):
        # User selected one or more repositories from TUI
        # Mark that confirmation was done via TUI selection
        ctx.obj["confirmation_done"] = True

        if len(selected) == 1:
            # Single repository - change to it
            change_to_selected_repository(selected[0])
        else:
            # Multiple repositories - use recursive machinery
            ctx.obj["git_repos"] = selected
            ctx.obj["original_repo_count"] = len(selected)
            ctx.obj["filtered"] = False
            recursive = True  # Use recursive machinery for multi-repo
            ctx.obj["recursive"] = True
    elif selected and isinstance(selected, Path):
        # User selected a single specific repository (from numbered list)
        change_to_selected_repository(selected)
    elif exit_on_cancel:
        # User cancelled or no repos found
        handle_exit_code(ctx, ExitCode.SUCCESS)
        # Note: handle_exit_code will exit, this is just for type checker
        return recursive, is_global

    return recursive, is_global
