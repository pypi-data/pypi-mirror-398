"""Install command group for zenable-mcp."""

import signal
import sys
import time

import click

from zenable_mcp.commands.install.command_generator import attach_unified_commands
from zenable_mcp.commands.install.hook import all_hooks, hook
from zenable_mcp.commands.install.mcp import all_ides, mcp
from zenable_mcp.exit_codes import ExitCode
from zenable_mcp.ide_config import find_git_root
from zenable_mcp.logging.command_logger import log_command
from zenable_mcp.logging.logged_echo import echo
from zenable_mcp.usage.manager import record_command_usage
from zenable_mcp.utils.cli_validators import handle_exit_code
from zenable_mcp.utils.config_manager import cleanup_temp_files
from zenable_mcp.utils.context_helpers import get_is_global_from_context
from zenable_mcp.utils.install_report import (
    filter_git_repositories,
    get_patterns_from_context,
    show_complete_filtering_information,
    show_filtering_results,
)
from zenable_mcp.utils.install_status import (
    get_exit_code,
    show_installation_summary,
    show_post_install_instructions,
)
from zenable_mcp.utils.recursive_operations import find_git_repositories
from zenable_mcp.utils.repo_selection_handler import handle_repository_selection
from zenable_mcp.utils.repo_selector import prompt_for_repository_selection


def signal_handler(signum, frame):
    """Handle interrupt signals gracefully."""
    echo("\n⚠️  Installation interrupted by user", err=True, log=True)
    cleanup_temp_files()
    sys.exit(ExitCode.USER_INTERRUPT)


@click.group(
    invoke_without_command=True,
    context_settings=dict(help_option_names=["-h", "--help"]),
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Preview what would be done without actually performing the installation",
)
@click.option(
    "--global",
    "-g",
    "is_global",
    is_flag=True,
    default=False,
    help="Install globally in user's home directory instead of project directory",
)
@click.option(
    "--include",
    multiple=True,
    help="Include only directories matching these glob patterns (e.g., '**/microservice-*')",
)
@click.option(
    "--exclude",
    multiple=True,
    help="Exclude directories matching these glob patterns",
)
@click.option(
    "--all",
    "force_all",
    is_flag=True,
    default=False,
    help="Install for all supported IDEs, even if not currently installed",
)
@click.pass_context
@log_command
def install(ctx, dry_run, is_global, include, exclude, force_all):
    """Install the Zenable integrations"""
    start_time = time.time()
    error = None

    try:
        # Set up signal handler for graceful interruption
        signal.signal(signal.SIGINT, signal_handler)
        # Also handle SIGTERM for completeness
        signal.signal(signal.SIGTERM, signal_handler)

        # Store dry_run, global, and patterns in context for subcommands
        ctx.ensure_object(dict)
        ctx.obj["dry_run"] = dry_run
        ctx.obj["is_global"] = is_global
        # recursive will be determined by repo selection
        recursive = False
        ctx.obj["recursive"] = recursive
        ctx.obj["include_patterns"] = list(include) if include else None
        ctx.obj["exclude_patterns"] = list(exclude) if exclude else None
        ctx.obj["force_all"] = force_all
        # Only skip git check if parent will handle repo selection (no subcommand)
        # When subcommand is present, let the subcommand handle its own repo selection
        if ctx.invoked_subcommand is None:
            ctx.obj["skip_git_check"] = True
        else:
            ctx.obj["skip_git_check"] = False

        # Determine repositories to work with
        git_repos = None

        # Check if we're in a git repo for non-global, non-recursive installs
        # Skip prompt if a subcommand will be invoked (subcommand may handle recursive)
        if not is_global and not recursive and ctx.invoked_subcommand is None:
            git_root = find_git_root()
            if not git_root:
                # Not in a git repo, prompt for repository selection with filters
                include_patterns, exclude_patterns = get_patterns_from_context(
                    include, exclude, ctx
                )

                selected = prompt_for_repository_selection(
                    max_repos_to_show=100,
                    allow_all=True,
                    allow_global=True,
                    include_patterns=include_patterns,
                    exclude_patterns=exclude_patterns,
                )

                recursive, is_global = handle_repository_selection(selected, ctx)
            elif not recursive:
                # We're in a single git repo, treat it as a single-item list for filtering
                git_repos = [git_root]

        # If recursive, find repositories
        if recursive:
            # Only find repos if not already set by multi-select
            if "git_repos" not in ctx.obj:
                git_repos = find_git_repositories()

                # Check if no repositories found
                if not git_repos:
                    echo("No git repositories found in the current directory or below.")
                    return handle_exit_code(ctx, ExitCode.SUCCESS)
            else:
                # Use repos from multi-select
                git_repos = ctx.obj["git_repos"]

        # Apply filtering if we have repos and patterns are provided
        if git_repos and (include or exclude):
            filter_result = filter_git_repositories(
                git_repos,
                include_patterns=list(include) if include else None,
                exclude_patterns=list(exclude) if exclude else None,
                handler_name="install" if len(git_repos) == 1 else "recursive install",
            )

            # Check if all repositories were filtered out
            if len(filter_result.filtered_repos) == 0:
                show_filtering_results(
                    filter_result.original_count,
                    include_patterns=list(include) if include else None,
                    exclude_patterns=list(exclude) if exclude else None,
                )
                return handle_exit_code(ctx, ExitCode.SUCCESS)

            git_repos = filter_result.filtered_repos
            ctx.obj["original_repo_count"] = filter_result.original_count
            ctx.obj["filtered"] = True
        else:
            ctx.obj["filtered"] = False
            if git_repos:
                ctx.obj["original_repo_count"] = len(git_repos)

        # Store the repos in context for subcommands
        if git_repos:
            ctx.obj["git_repos"] = git_repos

        # If no subcommand is provided, run both mcp all and hook all
        if ctx.invoked_subcommand is None:
            if recursive:
                # Handle recursive installation with aggregated output
                git_repos = ctx.obj.get("git_repos", [])
                if git_repos:
                    echo("Installing all of the Zenable integrations...")

                    # Show complete filtering information
                    original_count = ctx.obj.get("original_repo_count", len(git_repos))
                    was_filtered = ctx.obj.get("filtered", False)

                    if not show_complete_filtering_information(
                        git_repos,
                        original_count,
                        was_filtered,
                        include_patterns=ctx.obj.get("include_patterns"),
                        exclude_patterns=ctx.obj.get("exclude_patterns"),
                        dry_run=dry_run,
                    ):
                        return handle_exit_code(ctx, ExitCode.SUCCESS)

                if dry_run:
                    echo(
                        "\n"
                        + click.style("DRY RUN MODE:", fg="yellow", bold=True)
                        + " Showing what would be done\n"
                    )

                # Set flag so subcommands know they're being called from parent
                ctx.obj["from_parent_install"] = True

                # Call subcommands and get results
                mcp_results = ctx.invoke(
                    all_ides,
                    overwrite=False,
                    no_instructions=True,
                    dry_run=dry_run,
                    is_global=is_global,
                    include=include,
                    exclude=exclude,
                    force_all=force_all,
                )
                hook_results = ctx.invoke(
                    all_hooks,
                    is_global=is_global,
                    dry_run=dry_run,
                    include=include,
                    exclude=exclude,
                )

                # Ensure results are lists of InstallResult objects
                if not isinstance(mcp_results, list):
                    mcp_results = []
                if not isinstance(hook_results, list):
                    hook_results = []

                # Show MCP summary if we have MCP results
                if mcp_results:
                    show_installation_summary(
                        mcp_results,
                        dry_run,
                        "MCP Installation",
                        repositories=git_repos,
                    )

                # Show hooks summary if we have hook results
                if hook_results:
                    show_installation_summary(
                        hook_results,
                        dry_run,
                        "Hooks Installation",
                        repositories=git_repos,
                    )

                # Show post-install instructions
                all_results = mcp_results + hook_results
                if all_results:
                    show_post_install_instructions(
                        all_results, no_instructions=False, dry_run=dry_run
                    )

                # Calculate exit code from results
                exit_code = (
                    get_exit_code(all_results) if all_results else ExitCode.SUCCESS
                )

                # Exit with the appropriate code
                return handle_exit_code(ctx, exit_code)
            else:
                # Non-recursive installation
                if not dry_run:
                    # Check if we're being called with --global from parent
                    is_global = get_is_global_from_context(ctx)
                    if is_global:
                        echo("Installing all of the Zenable integrations globally...")
                    else:
                        echo("Installing all of the Zenable integrations...")

                ctx.invoke(
                    mcp,
                    dry_run=dry_run,
                    is_global=is_global,
                    include=include,
                    exclude=exclude,
                    force_all=force_all,
                )
                ctx.invoke(
                    hook,
                    dry_run=dry_run,
                    include=include,
                    exclude=exclude,
                )

    except click.exceptions.ClickException as e:
        # Catch Click exceptions (like invalid options) and log them as failures
        error = e
        raise
    except Exception as e:
        error = e
        raise
    finally:
        # Only record usage if no subcommand was invoked
        # If a subcommand was invoked, it will handle its own usage tracking
        # This prevents double-counting when commands like "install mcp" are run
        if ctx.invoked_subcommand is None:
            duration_ms = round((time.time() - start_time) * 1000)
            record_command_usage(ctx=ctx, duration_ms=duration_ms, error=error)


install.add_command(hook)
install.add_command(mcp)

# Auto-generate and attach unified commands
# This creates commands like `install claude` that run both mcp and hook
attach_unified_commands(install)

# Export signal_handler for testing
__all__ = ["install", "mcp", "signal_handler"]
