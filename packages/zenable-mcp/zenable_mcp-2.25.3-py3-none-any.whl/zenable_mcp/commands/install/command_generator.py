"""Dynamic command generator for unified install commands."""

import sys

import click

from zenable_mcp.exit_codes import ExitCode
from zenable_mcp.ide_config import IDERegistry, find_git_root
from zenable_mcp.logging.command_logger import log_command
from zenable_mcp.logging.logged_echo import echo
from zenable_mcp.utils.cli_validators import (
    handle_exit_code,
)
from zenable_mcp.utils.context_helpers import (
    get_dry_run_from_context,
    get_is_global_from_context,
    get_recursive_from_context,
)
from zenable_mcp.utils.install_report import (
    filter_git_repositories,
    format_installation_location,
    get_patterns_from_context,
    show_filtering_results,
)
from zenable_mcp.utils.install_status import (
    InstallResult,
    InstallStatus,
    get_exit_code,
    show_installation_summary,
    show_post_install_instructions,
)
from zenable_mcp.utils.repo_selection_handler import handle_repository_selection
from zenable_mcp.utils.repo_selector import prompt_for_repository_selection


def _create_unified_command_function(
    tool_name: str, ide_class, mcp_group, hook_group, features: list[str]
):
    """Create a unified command function for a specific tool.

    This function generates a Click command that installs all supported
    features (mcp, hook, etc.) for the given tool.

    Args:
        tool_name: Canonical name of the tool
        ide_class: IDE configuration class for this tool
        mcp_group: MCP command group
        hook_group: Hook command group
        features: List of supported features for this tool

    Returns:
        Click command function
    """
    display_name = ide_class.display_name

    def unified_command(
        ctx,
        dry_run,
        is_global,
        include,
        exclude,
        overwrite=None,
        no_instructions=None,
    ):
        f"""Install all {display_name} integrations.

        This command installs all supported features for {display_name}:
        {", ".join(features)}.
        """
        # Initialize recursive - it will be set by repo selection if needed
        recursive = False

        # Handle repository discovery when not in a git repo
        if not is_global and not recursive:
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
                    return ExitCode.SUCCESS

        # Show installation message for non-recursive, non-dry-run installs
        if not recursive and not dry_run:
            location = format_installation_location(
                is_global=is_global,
                git_root=find_git_root(),
            )
            echo(
                f"Installing the Zenable integrations for {display_name} {location}..."
            )

        # For recursive installs, set flag to get results back
        if recursive:
            ctx.ensure_object(dict)
            ctx.obj["from_parent_install"] = True
            ctx.obj["confirmation_done"] = True  # Skip duplicate confirmations

        # Check filters for non-recursive, non-global installs
        if not recursive and not is_global:
            include_patterns, exclude_patterns = get_patterns_from_context(
                include, exclude, ctx
            )
            if include_patterns or exclude_patterns:
                git_root = find_git_root()
                if git_root:
                    filter_result = filter_git_repositories(
                        [git_root],
                        include_patterns=include_patterns,
                        exclude_patterns=exclude_patterns,
                        handler_name=f"install {tool_name}",
                    )
                    if len(filter_result.filtered_repos) == 0:
                        # Show filtering message once here
                        show_filtering_results(
                            filter_result.original_count,
                            include_patterns=include_patterns,
                            exclude_patterns=exclude_patterns,
                        )
                        return ExitCode.SUCCESS

        # Accumulate results from subcommands
        all_results = []

        # Invoke MCP installation if supported
        if "mcp" in features:
            # Find the command for this tool in the mcp group
            ide_command = mcp_group.commands.get(tool_name)
            if ide_command:
                try:
                    # Set flags to suppress duplicate messages in MCP command
                    ctx.ensure_object(dict)
                    ctx.obj["from_unified_command"] = True
                    ctx.obj["skip_filtering_message"] = True
                    mcp_result = ctx.invoke(
                        ide_command,
                        overwrite=overwrite or False,
                        no_instructions=no_instructions or False,
                        dry_run=dry_run,
                        is_global=is_global,
                        include=include,
                        exclude=exclude,
                    )
                    # Collect results if returned
                    if isinstance(mcp_result, list):
                        all_results.extend(mcp_result)
                except Exception as e:
                    echo(
                        f"Error installing MCP for {display_name}: {e}",
                        err=True,
                    )
                    return handle_exit_code(ctx, ExitCode.INSTALLATION_ERROR)

        # Invoke hook installation if supported
        if "hook" in features:
            # Find the command for this tool in the hook group
            hook_command = hook_group.commands.get(tool_name)
            if hook_command:
                try:
                    # Set flag to suppress duplicate filtering message in hook command
                    ctx.ensure_object(dict)
                    ctx.obj["skip_filtering_message"] = True
                    hook_result = ctx.invoke(
                        hook_command,
                        is_global=is_global,
                        dry_run=dry_run,
                        include=include,
                        exclude=exclude,
                    )
                    # Collect results if returned
                    if isinstance(hook_result, list):
                        all_results.extend(hook_result)
                except Exception as e:
                    echo(
                        f"Error installing hook for {display_name}: {e}",
                        err=True,
                    )
                    return handle_exit_code(ctx, ExitCode.INSTALLATION_ERROR)

        # Show unified summary if we have results (recursive mode)
        if all_results and recursive:
            git_repos = ctx.obj.get("git_repos") if ctx.obj else None
            show_installation_summary(
                all_results,
                dry_run,
                f"{display_name} Installation",
                repositories=git_repos,
            )
            show_post_install_instructions(
                all_results, no_instructions or False, dry_run
            )

        # Calculate exit code from results
        if all_results:
            return get_exit_code(all_results)
        return ExitCode.SUCCESS

    # Set function metadata for Click
    unified_command.__name__ = tool_name.replace("-", "_")
    return unified_command


def add_unified_options(func):
    """Add standard options to unified install commands."""
    # MCP-specific options (only if tool supports MCP)
    func = click.option(
        "--no-instructions",
        is_flag=True,
        default=False,
        help="Skip post-installation instructions",
    )(func)
    func = click.option(
        "--overwrite",
        is_flag=True,
        default=False,
        help="Overwrite existing configuration",
    )(func)

    # Common options for all commands
    func = click.option(
        "--exclude",
        multiple=True,
        help="Exclude dirs matching glob patterns",
    )(func)
    func = click.option(
        "--include",
        multiple=True,
        help="Include only dirs matching glob patterns",
    )(func)
    func = click.option(
        "--global",
        "-g",
        "is_global",
        is_flag=True,
        default=False,
        help="Install globally",
    )(func)
    func = click.option(
        "--dry-run",
        is_flag=True,
        default=False,
        help="Preview without installing",
    )(func)

    return func


def attach_mcp_commands(mcp_group, install_single_ide, common_options):
    """Attach MCP commands for all tools that support MCP.

    Args:
        mcp_group: Click Group (mcp subgroup) to attach commands to
        install_single_ide: Function to install IDE configuration
        common_options: Decorator for common MCP options
    """
    registry = IDERegistry()

    for tool_name, ide_class in registry.ide_configs.items():
        # Check if IDE supports MCP using class method
        try:
            capabilities = ide_class.get_capabilities()
            if not (
                capabilities.get("supports_mcp_global_config")
                or capabilities.get("supports_mcp_project_config")
            ):
                continue
        except Exception:
            # If we can't get capabilities, skip this IDE
            continue

        # Create command function for this tool
        def make_mcp_command(tool_name=tool_name, ide_class=ide_class):
            @common_options
            @click.pass_context
            @log_command
            def mcp_command(
                ctx,
                overwrite,
                no_instructions,
                dry_run,
                is_global,
                include,
                exclude,
            ):
                f"""Install MCP for {ide_class.display_name}."""
                return install_single_ide(
                    ctx,
                    tool_name,
                    overwrite,
                    no_instructions,
                    dry_run,
                    is_global,
                    include,
                    exclude,
                )

            mcp_command.__name__ = tool_name.replace("-", "_")
            return mcp_command

        # Get aliases for this tool
        aliases = registry.get_aliases(tool_name)
        help_text = f"Install MCP for {ide_class.display_name}"

        # If aliases exist, show all aliases as visible and hide canonical
        if aliases:
            # Register all aliases as visible
            for alias in aliases:
                alias_cmd = make_mcp_command()
                mcp_group.add_command(
                    click.command(
                        name=alias,
                        help=help_text,
                        hidden=False,
                    )(alias_cmd)
                )

            # Register canonical name as hidden
            canonical_cmd = make_mcp_command()
            mcp_group.add_command(
                click.command(
                    name=tool_name,
                    help=help_text,
                    hidden=True,
                )(canonical_cmd)
            )
        else:
            # No aliases, register canonical name as visible
            cmd = make_mcp_command()
            mcp_group.add_command(
                click.command(
                    name=tool_name,
                    help=help_text,
                    hidden=False,
                )(cmd)
            )


def attach_hook_commands(
    hook_group, hook_implementations, common_hook_options, all_hooks
):
    """Attach hook commands for all tools that support hooks.

    Args:
        hook_group: Click Group (hook subgroup) to attach commands to
        hook_implementations: Dict mapping tool names to their implementation functions
        common_hook_options: Decorator for common hook options
        all_hooks: all_hooks command for recursive installation
    """
    registry = IDERegistry()

    for tool_name, ide_class in registry.ide_configs.items():
        # Check if IDE supports hooks using class method
        try:
            capabilities = ide_class.get_capabilities()
            if not capabilities.get("supports_hooks"):
                continue
        except Exception:
            # If we can't get capabilities, skip this IDE
            continue

        # Create command function for this tool
        def make_hook_command(tool_name=tool_name, ide_class=ide_class):
            @common_hook_options
            @click.pass_context
            @log_command
            def hook_command(ctx, is_global, dry_run, include, exclude):
                f"""Install {ide_class.display_name} hooks."""

                # Get flags from context hierarchy if not explicitly set
                if not dry_run:
                    dry_run = get_dry_run_from_context(ctx)
                # Get recursive from context (set by parent or repo selection)
                recursive = get_recursive_from_context(ctx)
                if not is_global:
                    is_global = get_is_global_from_context(ctx)

                # Check if we're in a git repo for non-global, non-recursive installs
                # This handles repo selection when not in a git repo
                if not is_global and not recursive:
                    git_root = find_git_root()
                    if not git_root:
                        # Not in a git repo, prompt for repository selection
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
                            sys.exit(ExitCode.SUCCESS)

                if recursive:
                    # Ensure context is set up for pattern passing
                    ctx.ensure_object(dict)
                    ctx.obj["include_patterns"] = list(include) if include else None
                    ctx.obj["exclude_patterns"] = list(exclude) if exclude else None

                    # Delegate to all_hooks for recursive installation
                    return ctx.invoke(
                        all_hooks,
                        is_global=False,
                        dry_run=dry_run,
                        include=include,
                        exclude=exclude,
                    )

                # Get patterns from context
                include_patterns, exclude_patterns = get_patterns_from_context(
                    include, exclude, ctx
                )

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
                            handler_name=f"install hook {tool_name}",
                        )

                        if len(filter_result.filtered_repos) == 0:
                            # Current repo doesn't match filters, skip installation
                            # Skip message if called from unified command (which already showed it)
                            skip_message = (
                                ctx.obj.get("skip_filtering_message", False)
                                if ctx.obj
                                else False
                            )
                            if not skip_message:
                                show_filtering_results(
                                    filter_result.original_count,
                                    include_patterns=include_patterns,
                                    exclude_patterns=exclude_patterns,
                                )
                            return ExitCode.SUCCESS

                results = []

                # Get the implementation for this tool
                impl = hook_implementations.get(tool_name)
                if not impl:
                    echo(
                        f"No hook implementation found for {tool_name}",
                        err=True,
                    )
                    return handle_exit_code(ctx, ExitCode.INSTALLATION_ERROR)

                try:
                    result = impl(is_global, dry_run)
                    results.append(result)
                except SystemExit as e:
                    # Error has already been printed by the implementation
                    # Extract exit code to include in result
                    exit_code = (
                        e.code if hasattr(e, "code") else ExitCode.INSTALLATION_ERROR
                    )
                    try:
                        exit_code_name = ExitCode(exit_code).name
                        error_msg = f"Installation failed: {exit_code_name}"
                    except ValueError:
                        error_msg = "Installation failed"

                    results.append(
                        InstallResult(
                            InstallStatus.FAILED,
                            f"{ide_class.display_name} hook",
                            error_msg,
                        )
                    )

                # Show installation summary
                show_installation_summary(results, dry_run, "Hooks Installation")

                # In dry-run mode, show preview message
                if dry_run and any(r.is_success for r in results):
                    echo(
                        "\nTo actually perform the installation, run the command without --dry-run"
                    )

                # Return appropriate exit code
                if results and any(r.is_error for r in results):
                    return handle_exit_code(ctx, ExitCode.INSTALLATION_ERROR)
                else:
                    return ExitCode.SUCCESS

            hook_command.__name__ = tool_name.replace("-", "_") + "_hook"
            return hook_command

        # Get aliases for this tool
        aliases = registry.get_aliases(tool_name)
        help_text = f"Install {ide_class.display_name} hooks"

        # If aliases exist, show all aliases as visible and hide canonical
        if aliases:
            # Register all aliases as visible
            for alias in aliases:
                alias_cmd = make_hook_command()
                hook_group.add_command(
                    click.command(
                        name=alias,
                        help=help_text,
                        hidden=False,
                    )(alias_cmd)
                )

            # Register canonical name as hidden
            canonical_cmd = make_hook_command()
            hook_group.add_command(
                click.command(
                    name=tool_name,
                    help=help_text,
                    hidden=True,
                )(canonical_cmd)
            )
        else:
            # No aliases, register canonical name as visible
            cmd = make_hook_command()
            hook_group.add_command(
                click.command(
                    name=tool_name,
                    help=help_text,
                    hidden=False,
                )(cmd)
            )


def attach_unified_commands(install_group):
    """Attach all unified commands to the install group.

    This function generates and attaches unified commands for all tools.
    For tools with multiple features (e.g., both mcp and hook), it installs all features.
    For tools with a single feature (e.g., only mcp), it installs that feature.

    Args:
        install_group: Click Group to attach commands to
    """
    # Get the mcp and hook groups from the install group
    mcp_group = install_group.commands.get("mcp")
    hook_group = install_group.commands.get("hook")

    registry = IDERegistry()

    for tool_name, ide_class in registry.ide_configs.items():
        # Check features using class method
        try:
            capabilities = ide_class.get_capabilities()
            supports_mcp = capabilities.get(
                "supports_mcp_global_config"
            ) or capabilities.get("supports_mcp_project_config")
            supports_hooks = capabilities.get("supports_hooks")

            # Skip tools that don't support any features
            if not supports_mcp and not supports_hooks:
                continue

            # Build features list
            features = []
            if supports_mcp:
                features.append("mcp")
            if supports_hooks:
                features.append("hook")

        except Exception:
            # If we can't get capabilities, skip this IDE
            continue

        # Create a factory function to generate fresh decorated functions
        def make_unified_command(
            tool_name=tool_name, ide_class=ide_class, features=features
        ):
            # Generate command function
            cmd_func = _create_unified_command_function(
                tool_name, ide_class, mcp_group, hook_group, features
            )

            # Add Click decorators in the correct order
            # Options must be applied BEFORE pass_context (innermost first)
            cmd_func = add_unified_options(cmd_func)
            cmd_func = log_command(cmd_func)
            cmd_func = click.pass_context(cmd_func)

            return cmd_func

        # Customize help text
        help_text = f"Install Zenable for {ide_class.display_name}"

        # Get aliases for this tool
        aliases = registry.get_aliases(tool_name)

        # If aliases exist, show all aliases as visible and hide canonical
        if aliases:
            # Register all aliases as visible
            for alias in aliases:
                alias_cmd = click.command(
                    name=alias,
                    help=help_text,
                    hidden=False,
                )(make_unified_command())
                install_group.add_command(alias_cmd)

            # Register canonical name as hidden
            canonical_cmd = click.command(
                name=tool_name,
                help=help_text,
                hidden=True,
            )(make_unified_command())
            install_group.add_command(canonical_cmd)
        else:
            # No aliases, register canonical name as visible
            cmd = click.command(
                name=tool_name,
                help=help_text,
                hidden=False,
            )(make_unified_command())
            install_group.add_command(cmd)
