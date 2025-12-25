import logging
import sys
from pathlib import Path
from typing import Optional, Union

import click

from zenable_mcp.commands.install.command_generator import attach_mcp_commands
from zenable_mcp.exit_codes import ExitCode
from zenable_mcp.ide_config import create_ide_config, find_git_root
from zenable_mcp.logging.command_logger import log_command
from zenable_mcp.logging.logged_echo import echo
from zenable_mcp.utils.cli_validators import (
    handle_exit_code,
)
from zenable_mcp.utils.context_helpers import (
    get_dry_run_from_context,
    get_flag_from_context,
    get_git_repos_from_context,
    get_is_global_from_context,
    get_recursive_from_context,
)
from zenable_mcp.utils.install_helpers import (
    determine_ides_to_configure,
    install_ide_configuration,
)
from zenable_mcp.utils.install_report import (
    filter_git_repositories,
    format_installation_location,
    get_patterns_from_context,
    show_complete_filtering_information,
    show_filtering_results,
)
from zenable_mcp.utils.install_status import (
    InstallResult,
    get_exit_code,
    show_installation_summary,
    show_post_install_instructions,
)
from zenable_mcp.utils.recursive_operations import (
    execute_for_multiple_components,
    find_git_repositories,
)
from zenable_mcp.utils.repo_selection_handler import handle_repository_selection
from zenable_mcp.utils.repo_selector import prompt_for_repository_selection

log = logging.getLogger(__name__)


def _install_mcp_recursive(
    ctx,
    ides: list[str],
    overwrite: bool,
    no_instructions: bool,
    dry_run: bool,
    include_patterns: Optional[list[str]] = None,
    exclude_patterns: Optional[list[str]] = None,
    silent: bool = False,
    return_results: bool = False,
) -> Union[list, ExitCode]:
    """Install MCP for specified IDEs in all git repositories below current directory.

    Args:
        ctx: Click context
        ides: List of IDE names to configure
        overwrite: Whether to overwrite existing configuration
        no_instructions: Whether to suppress post-install instructions
        dry_run: Whether this is a dry run
        include_patterns: Optional list of glob patterns to include directories
        exclude_patterns: Optional list of glob patterns to exclude directories
        silent: Whether to suppress output
        return_results: Whether to return results instead of exit code
    """
    # Get repos from context using helper
    git_repos = get_git_repos_from_context(ctx)
    if git_repos is None:
        git_repos = find_git_repositories()
        # Store for other commands to use
        if ctx.obj:
            ctx.obj["git_repos"] = git_repos

    # Apply filtering if patterns are provided
    original_count = len(git_repos)
    filter_result = filter_git_repositories(
        git_repos,
        include_patterns=include_patterns,
        exclude_patterns=exclude_patterns,
        handler_name="recursive install",
    )
    git_repos = filter_result.filtered_repos

    if not silent:
        # Check if all repositories were filtered out
        # Skip message if called from unified command (which already showed it)
        skip_message = (
            ctx.obj.get("skip_filtering_message", False) if ctx.obj else False
        )
        if (include_patterns or exclude_patterns) and len(git_repos) == 0:
            if not skip_message:
                show_filtering_results(
                    filter_result.original_count,
                    include_patterns=include_patterns,
                    exclude_patterns=exclude_patterns,
                )
            if return_results:
                return []
            return ExitCode.SUCCESS

        # Check if we should suppress repo list (when called from unified command)
        suppress_repo_list = get_flag_from_context(ctx, "suppress_repo_list")

        # Check if confirmation was already done (by TUI or previous command in unified flow)
        skip_confirmation = get_flag_from_context(ctx, "confirmation_done")

        # Show complete filtering information
        if not show_complete_filtering_information(
            git_repos,
            original_count,
            include_patterns or exclude_patterns,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
            dry_run=dry_run,
            suppress_repo_list=suppress_repo_list,
            skip_confirmation=skip_confirmation,
        ):
            if return_results:
                return []
            return ExitCode.SUCCESS

    if not git_repos:
        if not silent and not (include_patterns or exclude_patterns):
            # Only show message if not filtered (filtering messages shown above)
            echo("No git repositories found in the current directory or below.")
        if return_results:
            return []
        return ExitCode.SUCCESS  # No files is not an error

    if not silent:
        if dry_run:
            echo(
                "\n"
                + click.style("DRY RUN MODE:", fg="yellow", bold=True)
                + " Showing what would be done\n"
            )

    # Define the operation function for each repository/IDE combination
    def install_operation(
        repo_path: Path, ide_name: str, dry_run: bool
    ) -> InstallResult:
        # Always suppress inline capability errors; summary will show them
        return install_ide_configuration(
            ide_name,
            overwrite,
            dry_run,
            no_instructions,
            is_global=False,
            silent_capability_errors=True,
        )

    # Execute the operation across all repos and IDEs
    all_results = execute_for_multiple_components(
        paths=git_repos,
        components=ides,
        operation_func=install_operation,
        dry_run=dry_run,
    )

    # If asked to return results (for parent aggregation), return them
    if return_results:
        return all_results

    # Show summary if not silent
    if not silent:
        show_installation_summary(
            all_results, dry_run, "MCP Installation", repositories=git_repos
        )
        show_post_install_instructions(all_results, no_instructions, dry_run)

    # Return appropriate exit code
    return get_exit_code(all_results)


def _install_mcp_for_ides(
    ctx,
    ides: list[str],
    overwrite: bool,
    no_instructions: bool,
    dry_run: bool,
    is_global: bool,
    force_all: bool = False,
) -> ExitCode:
    """Common function to install MCP for specified IDEs."""
    if not dry_run and len(ides) > 1:
        # Get display names for the IDEs that support the requested mode
        ide_display_names = []
        for ide in ides:
            try:
                config = create_ide_config(ide, is_global=is_global)
                # Only include IDEs that support the requested installation mode
                if (is_global and config.supports_mcp_global_config) or (
                    not is_global and config.supports_mcp_project_config
                ):
                    ide_display_names.append(config.name)
            except (ValueError, KeyError, Exception):
                # If we can't determine support, include it and let later validation handle it
                echo(
                    f"Failed to get display name for IDE {ide}; falling back to {ide}...",
                    err=True,
                )
                ide_display_names.append(ide)

        if ide_display_names:
            ides_list = ", ".join(ide_display_names)
            if force_all:
                echo(f"Installing the MCP server for ALL supported IDEs: {ides_list}")
            else:
                echo(
                    f"Installing the MCP server for the following auto-detected IDEs: {ides_list}"
                )

    # Track results
    results: list[InstallResult] = []

    # Install for each IDE
    for ide_name in ides:
        result = install_ide_configuration(
            ide_name,
            overwrite,
            dry_run,
            no_instructions,
            is_global,
            silent_capability_errors=True,  # Summary will show capability mismatches
        )
        results.append(result)

    # Always show summary (for both single and multiple IDEs)
    show_installation_summary(results, dry_run, "MCP Installation")
    show_post_install_instructions(results, no_instructions, dry_run)

    # Get the exit code
    return get_exit_code(results)


# Create options that will be shared by all subcommands
def common_options(f):
    """Decorator to add common options to all MCP subcommands."""
    f = click.option(
        "--overwrite",
        is_flag=True,
        default=False,
        help="Overwrite existing Zenable configuration if it exists",
    )(f)
    f = click.option(
        "--no-instructions",
        is_flag=True,
        default=False,
        help="Don't show post-installation instructions",
    )(f)
    f = click.option(
        "--dry-run",
        is_flag=True,
        default=False,
        help="Show what would be done without actually performing the installation",
    )(f)
    f = click.option(
        "--global",
        "-g",
        "is_global",
        is_flag=True,
        default=False,
        help="Install globally in user's home directory instead of project directory",
    )(f)
    f = click.option(
        "--include",
        multiple=True,
        help="Include only directories matching these glob patterns (e.g., '**/microservice-*')",
    )(f)
    f = click.option(
        "--exclude",
        multiple=True,
        help="Exclude directories matching these glob patterns",
    )(f)
    return f


@click.group(
    invoke_without_command=True,
    context_settings=dict(help_option_names=["-h", "--help"]),
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Show what would be done without actually performing the installation",
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
def mcp(ctx, dry_run, is_global, include, exclude, force_all):
    """Install Zenable MCP server configuration.

    **Uses OAuth for secure authentication.**

    \b
    Examples:
      # Install MCP for all supported IDEs (default)
      zenable-mcp install mcp
      zenable-mcp install mcp all
    \b
      # Install MCP globally for all supported IDEs
      zenable-mcp install mcp --global
      zenable-mcp install mcp all --global
    \b
      # Install MCP for a specific IDE
      zenable-mcp install mcp cursor
      zenable-mcp install mcp claude
    \b
      # Preview what would be done without installing
      zenable-mcp install mcp --dry-run
      zenable-mcp install mcp cursor --dry-run

    \b
    For more information, visit:
    https://docs.zenable.io/integrations/mcp
    """
    # Initialize recursive - it will be set by repo selection if needed
    recursive = get_recursive_from_context(ctx) if ctx.parent else False

    # Store dry_run, is_global, and patterns in context for subcommands
    ctx.ensure_object(dict)

    # Inherit from parent context if not explicitly set
    if not dry_run and ctx.parent and ctx.parent.obj:
        dry_run = ctx.parent.obj.get("dry_run", False)
    if not is_global:
        is_global = get_is_global_from_context(ctx)

    ctx.obj["dry_run"] = dry_run
    ctx.obj["is_global"] = is_global
    ctx.obj["recursive"] = recursive
    ctx.obj["include_patterns"] = list(include) if include else None
    ctx.obj["exclude_patterns"] = list(exclude) if exclude else None
    ctx.obj["force_all"] = force_all

    # Pass through git_repos from parent context if available
    if ctx.parent and ctx.parent.obj and "git_repos" in ctx.parent.obj:
        ctx.obj["git_repos"] = ctx.parent.obj["git_repos"]

    # Check if we're in a git repo for non-global, non-recursive installs
    # Only check if not called from parent install command
    # Skip if a subcommand is being invoked (subcommand will handle repo selection with its own flags)
    skip_git_check = (
        ctx.parent and ctx.parent.obj and ctx.parent.obj.get("skip_git_check", False)
    )
    if (
        not is_global
        and not recursive
        and not skip_git_check
        and ctx.invoked_subcommand is None
    ):
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

            recursive, is_global = handle_repository_selection(
                selected, ctx, exit_on_cancel=False
            )
            if selected is None:
                # User cancelled
                sys.exit(ExitCode.SUCCESS)

    # If no subcommand is provided, default to 'all'
    if ctx.invoked_subcommand is None:
        # Get parent's recursive flag if available
        if not recursive and ctx.parent and ctx.parent.obj:
            recursive = ctx.parent.obj.get("recursive", False)

        ctx.invoke(
            all_ides,
            overwrite=False,
            no_instructions=False,
            dry_run=dry_run,
            is_global=is_global,
            include=include,
            exclude=exclude,
            force_all=force_all,
        )


@mcp.command(name="all")
@click.option(
    "--all",
    "force_all",
    is_flag=True,
    default=False,
    help="Install for all supported IDEs, even if not currently installed",
)
@common_options
@click.pass_context
@log_command
def all_ides(
    ctx,
    overwrite,
    no_instructions,
    dry_run,
    is_global,
    include,
    exclude,
    force_all,
):
    """Install MCP for all supported IDEs."""

    # Get flags from context hierarchy if not explicitly set
    if not dry_run:
        dry_run = get_dry_run_from_context(ctx)
    if not is_global:
        is_global = get_is_global_from_context(ctx)
    # Get recursive from context (set by parent or repo selection)
    recursive = get_recursive_from_context(ctx)

    # Check if we're being called from parent install command
    from_parent_install = ctx.obj and ctx.obj.get("from_parent_install", False)

    # Get force_all from context if not explicitly set
    if not force_all and ctx.obj:
        force_all = ctx.obj.get("force_all", False)

    ides = determine_ides_to_configure("all", is_global, force_all=force_all)

    # Get patterns from context if not explicitly provided
    include_patterns, exclude_patterns = get_patterns_from_context(
        include, exclude, ctx
    )

    if recursive:
        result = _install_mcp_recursive(
            ctx,
            ides,
            overwrite,
            no_instructions,
            dry_run,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
            silent=from_parent_install,
            return_results=from_parent_install,
        )
        # If called from parent, return results for aggregation
        if from_parent_install:
            return result
        exit_code = result
    else:
        # Check if we have filters and we're in a single repo
        if (include_patterns or exclude_patterns) and not is_global:
            # Get the current git repo if we're in one
            git_root = find_git_root()
            if git_root:
                # Apply filters to the single repo
                filter_result = filter_git_repositories(
                    [git_root],
                    include_patterns=include_patterns,
                    exclude_patterns=exclude_patterns,
                    handler_name="install mcp",
                )

                if len(filter_result.filtered_repos) == 0:
                    # Current repo doesn't match filters, skip installation
                    show_filtering_results(
                        filter_result.original_count,
                        include_patterns=include_patterns,
                        exclude_patterns=exclude_patterns,
                    )
                    return handle_exit_code(ctx, ExitCode.SUCCESS)

        exit_code = _install_mcp_for_ides(
            ctx,
            ides,
            overwrite,
            no_instructions,
            dry_run,
            is_global,
            force_all=force_all,
        )

    return handle_exit_code(ctx, exit_code)


def _install_single_ide(
    ctx,
    ide_name: str,
    overwrite: bool,
    no_instructions: bool,
    dry_run: bool,
    is_global: bool,
    include: tuple,
    exclude: tuple,
    custom_message: str = None,
) -> ExitCode:
    """Helper function to install MCP for a single IDE, reducing code duplication."""

    # Get flags from context hierarchy if not explicitly set
    if not is_global:
        is_global = get_is_global_from_context(ctx)
    if not dry_run:
        dry_run = get_dry_run_from_context(ctx)
    # Get recursive from context (set by parent or repo selection)
    recursive = get_recursive_from_context(ctx)

    # Check if we're in a git repo for non-global, non-recursive installs
    # This handles repo selection with subcommand's include/exclude flags
    if not is_global and not recursive:
        git_root = find_git_root()
        if not git_root:
            # Not in a git repo, prompt for repository selection with subcommand's filters
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

            recursive, is_global = handle_repository_selection(
                selected, ctx, exit_on_cancel=False
            )
            if selected is None:
                # User cancelled
                sys.exit(ExitCode.SUCCESS)

    # Display custom message or default message
    # Skip if called from unified command (which already showed a message)
    from_unified = ctx.obj.get("from_unified_command", False) if ctx.obj else False
    if not dry_run and not recursive and not from_unified:
        if custom_message:
            echo(custom_message)
        else:
            # Get display name for the IDE
            try:
                config = create_ide_config(ide_name, is_global=is_global)
                display_name = config.name
            except (ValueError, KeyError):
                echo(
                    f"Warning: Failed to get display name for IDE {ide_name}", err=True
                )
                display_name = ide_name.title()
            except Exception:
                # Don't fail here, let the actual installation handle the error
                display_name = ide_name.title()

            location = format_installation_location(
                is_global=is_global,
                git_root=find_git_root(),
            )
            echo(
                f"Installing Zenable MCP configuration for {display_name} {location}..."
            )

    # Get patterns from context if not explicitly provided
    include_patterns, exclude_patterns = get_patterns_from_context(
        include, exclude, ctx
    )

    if recursive:
        exit_code = _install_mcp_recursive(
            ctx,
            [ide_name],
            overwrite,
            no_instructions,
            dry_run,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
        )
    else:
        # Check if we have filters and we're in a single repo
        if (include_patterns or exclude_patterns) and not is_global:
            # Get the current git repo if we're in one
            git_root = find_git_root()
            if git_root:
                # Apply filters to the single repo
                filter_result = filter_git_repositories(
                    [git_root],
                    include_patterns=include_patterns,
                    exclude_patterns=exclude_patterns,
                    handler_name=f"install mcp {ide_name}",
                )

                if len(filter_result.filtered_repos) == 0:
                    # Current repo doesn't match filters, skip installation
                    show_filtering_results(
                        filter_result.original_count,
                        include_patterns=include_patterns,
                        exclude_patterns=exclude_patterns,
                    )
                    return handle_exit_code(ctx, ExitCode.SUCCESS)

        exit_code = _install_mcp_for_ides(
            ctx, [ide_name], overwrite, no_instructions, dry_run, is_global
        )

    return handle_exit_code(ctx, exit_code)


# Auto-generate MCP commands for all tools
# This replaces manual command definitions with dynamic generation
attach_mcp_commands(mcp, _install_single_ide, common_options)
