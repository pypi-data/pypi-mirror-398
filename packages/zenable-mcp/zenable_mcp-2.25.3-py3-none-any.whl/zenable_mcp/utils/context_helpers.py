"""Utility functions for working with Click context objects."""

from typing import Optional

import click


def get_recursive_from_context(ctx: click.Context) -> bool:
    """Get recursive flag from context hierarchy.

    Walks up the context hierarchy looking for the recursive flag.

    Args:
        ctx: Click context object

    Returns:
        True if recursive flag is set anywhere in the hierarchy, False otherwise
    """
    # Walk up context hierarchy
    current_ctx = ctx
    while current_ctx:
        if current_ctx.obj and "recursive" in current_ctx.obj:
            recursive = current_ctx.obj.get("recursive", False)
            if recursive:
                return True
        current_ctx = current_ctx.parent

    return False


def get_dry_run_from_context(ctx: click.Context) -> bool:
    """Get dry_run flag from context hierarchy.

    Walks up the context hierarchy looking for the dry_run flag.

    Args:
        ctx: Click context object

    Returns:
        True if dry_run flag is set anywhere in the hierarchy, False otherwise
    """
    # Walk up context hierarchy
    current_ctx = ctx
    while current_ctx:
        if current_ctx.obj and "dry_run" in current_ctx.obj:
            dry_run = current_ctx.obj.get("dry_run", False)
            if dry_run:
                return True
        current_ctx = current_ctx.parent

    return False


def get_is_global_from_context(ctx: click.Context) -> bool:
    """Get is_global flag from context hierarchy.

    Walks up the context hierarchy looking for the is_global flag.

    Args:
        ctx: Click context object

    Returns:
        True if is_global flag is set anywhere in the hierarchy, False otherwise
    """
    # Walk up context hierarchy
    current_ctx = ctx
    while current_ctx:
        if current_ctx.obj and "is_global" in current_ctx.obj:
            is_global = current_ctx.obj.get("is_global", False)
            if is_global:
                return True
        current_ctx = current_ctx.parent

    return False


def get_git_repos_from_context(ctx: click.Context) -> Optional[list]:
    """Get git_repos list from context hierarchy.

    Walks up the context hierarchy looking for the git_repos list.

    Args:
        ctx: Click context object

    Returns:
        List of git repositories if found, None otherwise
    """
    # Walk up context hierarchy
    current_ctx = ctx
    while current_ctx:
        if current_ctx.obj and "git_repos" in current_ctx.obj:
            repos = current_ctx.obj.get("git_repos")
            if repos is not None:
                return repos
        current_ctx = current_ctx.parent

    return None


def get_flag_from_context(
    ctx: Optional[click.Context], flag_name: str, default: bool = False
) -> bool:
    """Get a boolean flag from context object.

    This is a helper to safely get flags from context.obj with a consistent pattern.

    Args:
        ctx: Click context object (can be None)
        flag_name: Name of the flag to retrieve
        default: Default value if flag not found (default: False)

    Returns:
        The flag value if found in context, otherwise the default value

    Examples:
        >>> get_flag_from_context(ctx, "suppress_repo_list")
        False
        >>> get_flag_from_context(ctx, "confirmation_done", default=False)
        True
        >>> get_flag_from_context(None, "some_flag")
        False
    """
    if ctx and ctx.obj:
        return ctx.obj.get(flag_name, default)
    return default
