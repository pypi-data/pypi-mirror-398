"""Utility for selecting a git repository when not in one."""

import os
import sys
from pathlib import Path

import click

from zenable_mcp.logging.logged_echo import echo
from zenable_mcp.logging.persona import Persona
from zenable_mcp.utils.install_report import filter_git_repositories
from zenable_mcp.utils.recursive_operations import find_git_repositories
from zenable_mcp.utils.repo_selector_tui import RepoSelectorApp


def prompt_for_repository_selection(
    start_path: Path | None = None,
    max_repos_to_show: int = 100,
    allow_all: bool = True,
    allow_global: bool = True,
    include_patterns: list[str] | None = None,
    exclude_patterns: list[str] | None = None,
) -> list[Path] | Path | str | None:
    """Prompt user to select git repository/repositories from those found below current directory.

    When the user is not in a git repository but repositories exist below the
    current directory, this function will:
    1. Find all git repositories below the current directory
    2. Apply include/exclude filters if provided
    3. Display them in an interactive TUI (or numbered list as fallback)
    4. Allow the user to select one or more, all, or global installation

    Args:
        start_path: The path to start searching from. Defaults to current directory.
        max_repos_to_show: Maximum number of repositories to show in the selection.
                          If more exist, user will be asked to narrow their search.
        allow_all: Whether to show option to install in all repositories.
        allow_global: Whether to show option to install globally.
        include_patterns: Optional list of glob patterns to include repositories.
        exclude_patterns: Optional list of glob patterns to exclude repositories.

    Returns:
        - list[Path]: Multiple selected repositories (from TUI multi-select)
        - Path: Single selected repository
        - "all": Install in all repositories
        - "global": Global installation
        - None: User cancelled or no repos found
    """
    if start_path is None:
        start_path = Path.cwd()

    # Check for problematic exclude patterns early
    if exclude_patterns and "*" in exclude_patterns:
        echo(
            click.style(
                '\nWarning: You are excluding all repositories with --exclude "*".',
                fg="red",
                bold=True,
            ),
            persona=Persona.USER,
        )
        echo(
            "This will never match any repositories. Consider using a more specific exclude pattern,",
            persona=Persona.USER,
        )
        echo(
            "or install globally with --global instead.",
            persona=Persona.USER,
        )
        if allow_global:
            if click.confirm(
                "\nWould you like to install Zenable globally instead?", default=True
            ):
                echo("\nProceeding with global installation...", persona=Persona.USER)
                return "global"
        return None

    # Find git repositories below current directory
    echo("Searching for git repositories...", persona=Persona.USER)
    git_repos = find_git_repositories(start_path)

    # If no repos found in current directory, try the user's home directory
    if not git_repos and start_path != Path.home():
        echo(
            click.style(
                "No repositories found in current directory. Searching in home directory...",
                fg="yellow",
            ),
            persona=Persona.USER,
        )
        git_repos = find_git_repositories(Path.home())

    # Track whether any repos were found before filtering
    repos_found_before_filtering = len(git_repos) > 0

    # Apply include/exclude filters if provided
    if git_repos and (include_patterns or exclude_patterns):
        filter_result = filter_git_repositories(
            git_repos,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
            handler_name="repository selection",
        )
        git_repos = filter_result.filtered_repos

    if not git_repos:
        # Show different message based on whether filters were applied
        if repos_found_before_filtering and (include_patterns or exclude_patterns):
            echo(
                "\nNo git repositories found that match the provided include/exclude criteria.",
                persona=Persona.USER,
            )
        else:
            echo(
                "\nNo git repositories found in the current directory or below.",
                persona=Persona.USER,
            )

        # Ask if they want to install globally instead
        if allow_global:
            if click.confirm(
                "\nWould you like to install Zenable globally instead?", default=True
            ):
                echo("\nProceeding with global installation...", persona=Persona.USER)
                return "global"

        # Show helpful usage guide
        echo("\nQuick Usage Guide:", persona=Persona.USER)
        echo(
            "- Run this command from your project directory (where your code is)",
            persona=Persona.USER,
        )
        echo(
            "- Use --global to install in your home directory for all projects",
            persona=Persona.USER,
        )
        echo(
            click.style(
                "\nFor more information, visit: https://docs.zenable.io/integrations/mcp/getting-started",
                fg="cyan",
            ),
            persona=Persona.USER,
        )
        return None

    # Remove the current directory if it's in the list (shouldn't be if we're calling this)
    # This handles edge cases where find_git_repositories might include the current dir
    git_repos = [repo for repo in git_repos if repo != start_path]

    if not git_repos:
        echo("\nNo git repositories found after filtering.", persona=Persona.USER)

        # Show helpful usage guide
        echo("\nQuick Usage Guide:", persona=Persona.USER)
        echo(
            "- Run this command from your project directory (where your code is)",
            persona=Persona.USER,
        )
        echo(
            "- Use --global to install in your home directory for all projects",
            persona=Persona.USER,
        )
        echo(
            click.style(
                "\nFor more information, visit: https://docs.zenable.io/integrations/mcp/getting-started",
                fg="cyan",
            ),
            persona=Persona.USER,
        )
        return None

    # If only one repository found, ask for confirmation
    if len(git_repos) == 1:
        repo_path = git_repos[0]
        try:
            relative_path = repo_path.relative_to(start_path)
        except ValueError:
            relative_path = repo_path

        if click.confirm(
            f"\nFound 1 git repository: {relative_path}\n"
            "Would you like to install in this repository?",
            default=True,
        ):
            return repo_path
        else:
            return None

    # Limit repos if too many
    original_repo_count = len(git_repos)
    if original_repo_count > max_repos_to_show:
        git_repos = git_repos[:max_repos_to_show]
        echo(
            click.style(
                f"Many repositories found. Showing the first {max_repos_to_show}.",
                fg="yellow",
            ),
            persona=Persona.USER,
        )
        echo(
            click.style(
                "Tip: Use --include/--exclude filters or navigate to a more specific directory to see fewer options.",
                fg="yellow",
            ),
            persona=Persona.USER,
        )

    # Try to use Textual TUI if TTY is available
    if _can_use_textual_tui():
        try:
            app = RepoSelectorApp(
                repos=git_repos,
                start_path=start_path,
                allow_all=allow_all,
                allow_global=allow_global,
            )
            result = app.run()

            # Print what the user decided
            if result is None:
                echo("User cancelled installation.", persona=Persona.USER)
            elif result == "global":
                echo("User chose global installation.", persona=Persona.USER)
            elif isinstance(result, list):
                echo(
                    f"User selected {len(result)} repositories for installation.",
                    persona=Persona.USER,
                )
            elif isinstance(result, Path):
                echo("User selected 1 repository.", persona=Persona.USER)

            return result
        except Exception as e:
            # Fall back to numbered list if TUI fails
            echo(
                f"\nCould not launch interactive TUI ({e}), using numbered list.",
                persona=Persona.USER,
            )

    # Fallback: Use numbered list selection
    # Show the repo count for numbered list
    if original_repo_count > max_repos_to_show:
        echo(
            click.style(
                f"\nMany repositories found. Showing the first {max_repos_to_show}.",
                fg="yellow",
            ),
            persona=Persona.USER,
        )
        echo(
            click.style(
                "Tip: Use --include/--exclude filters or navigate to a more specific directory to see fewer options.",
                fg="yellow",
            ),
            persona=Persona.USER,
        )
    else:
        echo(f"\nFound {original_repo_count} git repositories:", persona=Persona.USER)

    result = _prompt_numbered_list(git_repos, start_path, allow_all, allow_global)

    # Print what the user decided for numbered list too
    if result is None:
        echo("User cancelled installation.", persona=Persona.USER)
    elif result == "all":
        echo("User chose to install in all repositories.", persona=Persona.USER)
    elif result == "global":
        echo("User chose global installation.", persona=Persona.USER)
    elif isinstance(result, Path):
        echo("User selected 1 repository.", persona=Persona.USER)

    return result


def _can_use_textual_tui() -> bool:
    """Check if Textual TUI can be used in this environment."""
    # Check for TTY (textual is always available via uvx)
    return sys.stdin.isatty() and sys.stdout.isatty()


def _prompt_numbered_list(
    git_repos: list[Path],
    start_path: Path,
    allow_all: bool,
    allow_global: bool,
) -> Path | str | None:
    """Fallback numbered list selection (for non-TTY environments)."""
    # Display repositories with numbers
    echo("\nSelect where to install:", persona=Persona.USER)

    # Show individual repositories
    for i, repo in enumerate(git_repos, 1):
        try:
            relative_path = repo.relative_to(start_path)
        except ValueError:
            relative_path = repo
        echo(f"  {i}. {relative_path}")

    # Calculate next option numbers
    next_num = len(git_repos) + 1
    all_num = None
    global_num = None

    # Add special options
    if allow_all and len(git_repos) > 1:
        all_num = next_num
        echo(f"  {all_num}. Install in all {len(git_repos)} repositories")
        next_num += 1

    if allow_global:
        global_num = next_num
        echo(f"  {global_num}. Install globally (in home directory)")

    # Add option to cancel
    echo("  0. Cancel installation")

    # Get user selection
    while True:
        try:
            choice = click.prompt("\nEnter the number of your choice", type=int)

            if choice == 0:
                echo("Installation cancelled.", persona=Persona.USER)
                return None
            elif 1 <= choice <= len(git_repos):
                selected_repo = git_repos[choice - 1]
                echo(f"\nSelected: {selected_repo}", persona=Persona.USER)
                return selected_repo
            elif all_num and choice == all_num:
                echo(
                    f"\nSelected: Install in all {len(git_repos)} repositories",
                    persona=Persona.USER,
                )
                return "all"
            elif global_num and choice == global_num:
                echo("\nSelected: Install globally", persona=Persona.USER)
                return "global"
            else:
                max_choice = max(filter(None, [len(git_repos), all_num, global_num]))
                echo(
                    f"Invalid choice. Please enter a number between 0 and {max_choice}.",
                    err=True,
                )
        except (ValueError, click.exceptions.Abort):
            echo("\nInstallation cancelled.", persona=Persona.USER)
            return None


def change_to_selected_repository(selected_repo: Path) -> Path:
    """Change the current working directory to the selected repository.

    Args:
        selected_repo: Path to the repository to change to

    Returns:
        The previous working directory (for restoration if needed)
    """
    previous_dir = Path.cwd()
    os.chdir(selected_repo)
    echo(f"Changed to directory: {selected_repo}", persona=Persona.DEVELOPER)
    return previous_dir
