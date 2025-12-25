"""Utilities for recursive operations across git repositories."""

import os
from pathlib import Path
from typing import Callable, Optional

from git import InvalidGitRepositoryError, NoSuchPathError, Repo

from zenable_mcp.logging.logged_echo import echo
from zenable_mcp.logging.persona import Persona
from zenable_mcp.utils.install_status import InstallResult, InstallStatus


def find_git_repositories(
    start_path: Optional[Path] = None, max_depth: int = 5
) -> list[Path]:
    """Find all git repositories below the given path.

    This function searches for directories containing a .git folder,
    indicating they are git repositories. It does not search within
    nested git repositories (e.g., submodules).

    If the start path itself is within a git repository, that repository will be
    included in the results and the search will continue from there.

    Args:
        start_path: The path to start searching from. Defaults to current directory.
        max_depth: Maximum depth to search for repositories.

    Returns:
        List of paths to git repository roots
    """
    if start_path is None:
        start_path = Path.cwd()

    git_repos = []

    # First, check if we're currently inside a git repository
    try:
        repo = Repo(start_path, search_parent_directories=True)
        repo_root = Path(repo.git.rev_parse("--show-toplevel"))

        # Add the current repository to the list
        echo(
            f"Current directory is within git repository: {repo_root}",
            persona=Persona.POWER_USER,
        )
        git_repos.append(repo_root)

    except (InvalidGitRepositoryError, NoSuchPathError, OSError):
        # Not in a git repository, proceed to search below
        echo(
            "Current directory is not within a git repository",
            persona=Persona.DEVELOPER,
        )

    # Track visited directories to avoid duplicates
    visited_repos = set()
    if git_repos:
        visited_repos.add(str(git_repos[0]))

    # Track if we actually hit the depth limit with potential repositories to explore
    hit_depth_limit = False

    # Walk the directory tree looking for .git directories
    for root, dirs, _ in os.walk(start_path):
        current_path = Path(root)

        # Calculate depth from start_path
        try:
            relative_depth = len(current_path.relative_to(start_path).parts)
        except ValueError:
            # If current_path is not relative to start_path, skip it
            continue

        # Check if we're approaching the depth limit
        if relative_depth == max_depth - 1:
            # We're one level before max_depth, check if we have subdirectories
            # that we won't explore (they would be at max_depth)
            if dirs:
                # Filter out .git since we're already in a repo if it exists
                non_git_dirs = [d for d in dirs if d != ".git"]
                if non_git_dirs:
                    hit_depth_limit = True

        # Stop if we've reached max depth
        if relative_depth >= max_depth:
            dirs.clear()  # Don't recurse deeper
            continue

        # Check if this is a git repository
        if ".git" in dirs:
            # Check if this is a valid git repository using gitpython
            try:
                repo = Repo(current_path)
                repo_root_str = str(current_path.resolve())

                # Only add if we haven't seen this repository before
                if repo_root_str not in visited_repos:
                    git_repos.append(current_path)
                    visited_repos.add(repo_root_str)
                    echo(
                        f"Found git repository: {current_path}",
                        persona=Persona.POWER_USER,
                    )

                # Don't search within this git repository for nested ones
                dirs.clear()
            except (InvalidGitRepositoryError, NoSuchPathError, OSError):
                # Not a valid git repository, continue searching
                pass

    # Only warn if we actually hit the depth limit with subdirectories to explore
    if hit_depth_limit:
        echo(
            f"Directory traversal limited to {max_depth} levels deep. Some repositories may have been skipped.",
            persona=Persona.POWER_USER,
            err=True,
        )

    return git_repos


def execute_in_git_repositories(
    operation_func: Callable[[Path, bool], InstallResult],
    operation_name: str,
    dry_run: bool = False,
    start_path: Optional[Path] = None,
    git_repos: Optional[list[Path]] = None,
) -> list[InstallResult]:
    """Execute an operation in all git repositories below the start path.

    This function handles:
    - Finding git repositories (or using provided list)
    - Changing to each repository directory
    - Executing the operation
    - Restoring the original directory

    Args:
        operation_func: Function to execute in each repository.
                       Takes (repo_path, dry_run) and returns InstallResult
        operation_name: Name of the operation for display purposes
        dry_run: Whether this is a dry run
        start_path: The path to start searching from. Defaults to current directory.
        git_repos: Optional list of already-found git repositories to use instead of searching

    Returns:
        List of InstallResult objects from all repositories
    """
    # Use provided repositories or find them
    if git_repos is None:
        git_repos = find_git_repositories(start_path)

    if not git_repos:
        return []

    all_results = []
    original_cwd = os.getcwd()

    for repo in git_repos:
        # Change to the repository directory and execute operation
        try:
            os.chdir(repo)
            result = operation_func(repo, dry_run)
            all_results.append(result)

        except (OSError, IOError, PermissionError) as e:
            # Handle file system and permission errors
            error_result = InstallResult(
                status=InstallStatus.FAILED,
                component_name=operation_name,
                message=f"Failed: {e}",
            )
            all_results.append(error_result)

        except Exception as e:
            # Handle any other exceptions that may occur
            error_result = InstallResult(
                status=InstallStatus.FAILED,
                component_name=operation_name,
                message=f"{e}",
            )
            all_results.append(error_result)

        finally:
            # Always restore the original directory
            try:
                os.chdir(original_cwd)
            except OSError:
                # If we can't change back, at least log it
                echo(
                    f"Failed to restore working directory to {original_cwd}",
                    persona=Persona.DEVELOPER,
                    err=True,
                )

    return all_results


def execute_for_multiple_components(
    paths: list[Path],
    components: list[str],
    operation_func: Callable[[Path, str, bool], InstallResult],
    dry_run: bool = False,
) -> list[InstallResult]:
    """Execute an operation for multiple components in multiple paths.

    This is a helper for cases where you need to install multiple IDEs
    or run multiple operations per path.

    Args:
        paths: List of paths (typically repository paths)
        components: List of component names (e.g., IDE names)
        operation_func: Function that takes (path, component_name, dry_run)
                       and returns InstallResult
        dry_run: Whether this is a dry run

    Returns:
        List of InstallResult objects from all paths and components
    """
    all_results = []
    original_cwd = os.getcwd()

    for path in paths:
        try:
            os.chdir(path)

            # Execute operation for each component in this path
            for component in components:
                try:
                    result = operation_func(path, component, dry_run)
                    all_results.append(result)
                except (OSError, IOError, PermissionError) as e:
                    # Handle file system and permission errors for individual components
                    error_result = InstallResult(
                        status=InstallStatus.FAILED,
                        component_name=component,
                        message=f"Failed: {e}",
                    )
                    all_results.append(error_result)

        except OSError as e:
            # Handle directory change failures
            # Create error results for all components if we can't change directory
            for component in components:
                error_result = InstallResult(
                    status=InstallStatus.FAILED,
                    component_name=component,
                    message=f"Failed to access path: {e}",
                )
                all_results.append(error_result)

        finally:
            # Always restore the original directory
            try:
                os.chdir(original_cwd)
            except OSError:
                # If we can't change back, at least log it
                echo(
                    f"Failed to restore working directory to {original_cwd}",
                    persona=Persona.DEVELOPER,
                    err=True,
                )

    return all_results
