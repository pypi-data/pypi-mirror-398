"""Experimental mode utilities."""

import os
from pathlib import Path
from typing import Optional

import git
from git import Repo

from zenable_mcp.logging.logged_echo import echo
from zenable_mcp.logging.persona import Persona


def is_experimental_mode() -> bool:
    """Check if experimental mode is enabled via ZENABLE_EXPERIMENTAL environment variable."""
    env_value = os.environ.get("ZENABLE_EXPERIMENTAL", "").lower().strip()
    return env_value in ("true", "yes", "y", "1")


def log_experimental_mode_warning() -> None:
    """Log warning message when experimental mode is active."""
    if is_experimental_mode():
        echo(
            "⚠️  EXPERIMENTAL MODE ENABLED: Features may be unstable or break without warning",
            persona=Persona.POWER_USER,
            log=True,
        )


def get_git_diff_for_file(file_path: Path) -> Optional[str]:
    """Get git diff for a file using GitPython.

    Returns:
        Git diff content as string, or None if diff cannot be generated
    """
    try:
        repo = Repo(file_path, search_parent_directories=True)
        git_root = Path(repo.working_tree_dir)
        relative_path = file_path.relative_to(git_root)

        # Get diff for the file
        diff = repo.git.diff(str(relative_path))
        return diff if diff else None

    except (git.InvalidGitRepositoryError, git.GitCommandError, ValueError, OSError):
        return None
