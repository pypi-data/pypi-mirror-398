"""
Consolidated file utilities for pattern matching, filtering, and file operations.
"""

import fnmatch
import glob as stdlib_glob
import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import Optional, Union

from zenable_mcp.exit_codes import ExitCode
from zenable_mcp.logging.logged_echo import echo
from zenable_mcp.logging.persona import Persona
from zenable_mcp.utils.experimental import (
    get_git_diff_for_file,
    is_experimental_mode,
)

# Common directories that should typically be ignored for performance
DEFAULT_IGNORE_DIRS = {
    "node_modules",
    ".venv",
    "venv",
    "env",
    ".env",
    "__pycache__",
    ".git",
    ".svn",
    ".hg",
    ".tox",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".coverage",
    "htmlcov",
    "dist",
    "build",
    ".eggs",
    "*.egg-info",
    ".idea",
    ".vscode",
    ".DS_Store",
}


def _is_escaped(pattern: str, pos: int) -> bool:
    """Check if a character at position pos is escaped with a backslash."""
    return pos > 0 and pattern[pos - 1] == "\\"


def _validate_braces(pattern: str) -> None:
    """
    Validate that braces in the pattern are properly matched and not nested.

    Args:
        pattern: The pattern to validate

    Raises:
        ValueError: If braces are unmatched, nested, or empty
    """
    # Check for unmatched closing braces
    i = 0
    while i < len(pattern):
        if pattern[i] == "}" and not _is_escaped(pattern, i):
            # Check if there's a preceding unescaped opening brace
            j = i - 1
            depth = 1
            found_open = False
            while j >= 0 and depth > 0:
                if pattern[j] == "}" and not _is_escaped(pattern, j):
                    depth += 1
                elif pattern[j] == "{" and not _is_escaped(pattern, j):
                    depth -= 1
                    if depth == 0:
                        found_open = True
                        break
                j -= 1
            if not found_open:
                raise ValueError(
                    f"Detected unsupported brace expansion: {pattern} (unmatched braces)"
                )
        i += 1


def _find_first_brace_group(pattern: str) -> tuple[int, int, str] | None:
    """
    Find the first unescaped brace group in the pattern.

    Args:
        pattern: The pattern to search

    Returns:
        A tuple of (start_pos, end_pos, content) or None if no braces found

    Raises:
        ValueError: If braces are nested, unmatched, or empty
    """
    i = 0
    while i < len(pattern):
        if pattern[i] == "{" and not _is_escaped(pattern, i):
            # Found an unescaped opening brace
            # Now find its matching closing brace
            depth = 1
            j = i + 1
            while j < len(pattern) and depth > 0:
                if pattern[j] == "{" and not _is_escaped(pattern, j):
                    # Found nested unescaped opening brace - not supported
                    raise ValueError(
                        f"Detected unsupported brace expansion: {pattern} (nested braces)"
                    )
                elif pattern[j] == "}" and not _is_escaped(pattern, j):
                    depth -= 1
                j += 1

            if depth != 0:
                raise ValueError(
                    f"Detected unsupported brace expansion: {pattern} (unmatched braces)"
                )

            # Extract the content between braces
            brace_content = pattern[i + 1 : j - 1]
            if not brace_content:
                raise ValueError(
                    f"Detected unsupported brace expansion: {pattern} (empty braces)"
                )

            return (i, j, brace_content)
        i += 1

    return None


@lru_cache(maxsize=1024)
def _expand_braces(pattern: str) -> tuple[str, ...]:
    """
    Expand brace patterns like '*.{log,tmp,bak}' into multiple patterns.

    Supports escaped braces using backslash (\\{ and \\}) which are treated as literal characters.

    Args:
        pattern: A pattern potentially containing braces

    Returns:
        Tuple of expanded patterns (tuple for hashability with lru_cache)

    Raises:
        ValueError: If unsupported brace expansions are detected (nested braces or empty braces)
    """
    # First validate that all braces are properly matched
    _validate_braces(pattern)

    # Find the first brace group to expand
    brace_match = _find_first_brace_group(pattern)

    if not brace_match:
        # No unescaped braces found, just unescape any escaped braces
        return (pattern.replace("\\{", "{").replace("\\}", "}"),)

    # Extract positions and content
    start, end, content = brace_match
    prefix = pattern[:start]
    suffix = pattern[end:]

    # Split the content by commas and expand
    options = content.split(",")
    expanded = []

    for option in options:
        # Build new pattern with this option
        new_pattern = prefix + option + suffix
        # Recursively expand in case there are more braces
        expanded_suffix = _expand_braces(new_pattern)
        expanded.extend(expanded_suffix)

    return tuple(expanded)


def _match_glob_pattern(
    filename: str, pattern: str, file_parts: tuple[str, ...], file_basename: str
) -> bool:
    """Helper function to handle glob pattern matching."""
    if "**" in pattern:
        return _match_double_star_pattern(filename, pattern, file_parts)
    else:
        return fnmatch.fnmatch(filename, pattern) or fnmatch.fnmatch(
            file_basename, pattern
        )


def _match_double_star_pattern(
    filename: str, pattern: str, file_parts: tuple[str, ...]
) -> bool:
    """Helper function to handle ** patterns."""
    # Special case: pattern is exactly "**" - matches everything
    if pattern == "**":
        return True

    if pattern.startswith("**/"):
        simple_pattern = pattern[3:]

        # Check if filename matches the pattern
        if fnmatch.fnmatch(filename, simple_pattern):
            return True

        # Check last part of path if file_parts is not empty
        if file_parts and fnmatch.fnmatch(file_parts[-1], simple_pattern):
            return True

        for i in range(len(file_parts)):
            partial_path = "/".join(file_parts[i:])
            if fnmatch.fnmatch(partial_path, simple_pattern):
                return True

    if "/**/" in pattern:
        parts = pattern.split("/**/", 1)
        if len(parts) == 2:
            prefix, suffix = parts
            if filename.startswith(prefix + "/"):
                remaining = filename[len(prefix) + 1 :]
                return _match_suffix_pattern(remaining, suffix)

    # Always check the normalized pattern as a fallback
    pattern_normalized = pattern.replace("**", "*")
    return fnmatch.fnmatch(filename, pattern_normalized)


def _match_suffix_pattern(remaining_path: str, suffix: str) -> bool:
    """Helper function to match suffix patterns in ** expressions."""
    if "*" in suffix or "?" in suffix:
        remaining_parts = Path(remaining_path).parts
        for i in range(len(remaining_parts)):
            subpath = "/".join(remaining_parts[i:])
            if Path(subpath).match(suffix):
                return True
    else:
        return remaining_path.endswith(suffix)

    return False


def _match_exact_pattern(filename: str, pattern: str, file_basename: str) -> bool:
    """Helper function to handle exact pattern matching."""
    if pattern.startswith("/"):
        return filename == pattern[1:]
    elif pattern.startswith("./"):
        return filename == pattern[2:]
    elif "/" in pattern:
        if filename == pattern:
            return True
        return (
            filename.endswith("/" + pattern)
            and len(filename) > len(pattern) + 1
            and filename[-(len(pattern) + 1)] == "/"
        )
    else:
        return file_basename == pattern


@lru_cache(maxsize=10240)
def _get_relative_path_cached(
    file_path: Path, base_path: Path
) -> tuple[str, tuple[str, ...], str]:
    """
    Get relative path components with caching.

    Returns:
        Tuple of (path_string, path_parts, basename)
    """
    try:
        rel_path = file_path.relative_to(base_path)
        return (str(rel_path), rel_path.parts, file_path.name)
    except ValueError:
        # If can't get relative path, use absolute
        return (str(file_path), file_path.parts, file_path.name)


def _matches_any_pattern(
    file_path: Path,
    patterns: list[str],
    base_path: Optional[Path] = None,
    _expanded_patterns_cache: Optional[dict[str, tuple[str, ...]]] = None,
) -> bool:
    """
    Check if a file matches any of the given patterns.

    Args:
        file_path: File path to check
        patterns: List of patterns to match against
        base_path: Base path for relative matching (defaults to cwd)
        _expanded_patterns_cache: Optional cache for expanded patterns

    Returns:
        True if file matches any pattern, False otherwise
    """
    # Try to get relative path for matching
    if base_path is None:
        base_path = Path.cwd()

    # Use cached relative path computation
    file_str, file_parts, file_basename = _get_relative_path_cached(
        file_path, base_path
    )

    # Use cache if provided, otherwise create local cache
    if _expanded_patterns_cache is None:
        _expanded_patterns_cache = {}

    for pattern in patterns:
        # Use cached expansion if available
        if pattern not in _expanded_patterns_cache:
            _expanded_patterns_cache[pattern] = _expand_braces(pattern)
        expanded_patterns = _expanded_patterns_cache[pattern]

        for expanded_pattern in expanded_patterns:
            if "*" in expanded_pattern or "?" in expanded_pattern:
                if _match_glob_pattern(
                    file_str, expanded_pattern, file_parts, file_basename
                ):
                    return True
            else:
                if _match_exact_pattern(file_str, expanded_pattern, file_basename):
                    return True
    return False


def filter_files_by_patterns(
    files: list[Path],
    patterns: Optional[list[str]] = None,
    exclude_patterns: Optional[list[str]] = None,
    handler_name: Optional[str] = None,
    directory_only: bool = False,
) -> list[Path]:
    """
    Filter files based on include and exclude patterns.

    Args:
        files: List of file paths to filter
        patterns: Include patterns (if None, all files are included)
        exclude_patterns: Exclude patterns (if None, no files are excluded)
        handler_name: Name of the handler for logging purposes
        directory_only: If True, only include directories in the results

    Returns:
        Filtered list of file paths
    """
    # Early return if no patterns to filter
    if not patterns and not exclude_patterns and not directory_only:
        return files

    filtered_files = []
    base_path = Path.cwd()

    # Special case: if we're filtering a single directory and CWD is that directory,
    # use the parent as base so the relative path is the directory name, not "."
    if (
        len(files) == 1
        and files[0].is_dir()
        and files[0].resolve() == base_path.resolve()
    ):
        base_path = base_path.parent

    # Pre-expand patterns for all files to avoid repeated expansion
    include_cache = {} if patterns else None
    exclude_cache = {} if exclude_patterns else None

    # Pre-compute relative paths once if needed for logging
    rel_paths = {}
    if handler_name:
        for file_path in files:
            try:
                rel_paths[file_path] = file_path.relative_to(base_path)
            except ValueError:
                rel_paths[file_path] = file_path

    for file_path in files:
        # If directory_only is True, skip non-directories
        if directory_only and not file_path.is_dir():
            if handler_name:
                rel_path = rel_paths.get(file_path, file_path)
                echo(
                    f"{handler_name} passed in file ./{rel_path}, but directory_only filter excluded it",
                    persona=Persona.POWER_USER,
                )
            continue

        # Check include patterns (if specified)
        if patterns and not _matches_any_pattern(
            file_path, patterns, base_path, include_cache
        ):
            if handler_name:
                rel_path = rel_paths.get(file_path, file_path)
                echo(
                    f"{handler_name} passed in file ./{rel_path}, but it was filtered out by the include pattern",
                    persona=Persona.POWER_USER,
                )
            continue

        # Check exclude patterns
        if exclude_patterns and _matches_any_pattern(
            file_path, exclude_patterns, base_path, exclude_cache
        ):
            if handler_name:
                rel_path = rel_paths.get(file_path, file_path)
                echo(
                    f"{handler_name} passed in file ./{rel_path}, but it was filtered out by the exclude pattern",
                    persona=Persona.POWER_USER,
                )
            continue

        filtered_files.append(file_path)

    return filtered_files


def expand_file_patterns(
    patterns: list[str],
    base_path: Optional[Path] = None,
    exclude_patterns: Optional[list[str]] = None,
    max_files: Optional[int] = None,
    directory_only: bool = False,
    skip_ignored_dirs: bool = True,
) -> list[Path]:
    """
    Expand file patterns (including globs) into a list of file paths.

    Args:
        patterns: List of file patterns (can be paths or glob patterns like '**/*.py')
        base_path: Base directory to search from (defaults to your current directory)
        exclude_patterns: Optional list of patterns to exclude
        max_files: Optional maximum number of files to return (for safety)
        directory_only: If True, only include directories in the results
        skip_ignored_dirs: If True, skip commonly ignored directories like node_modules, .venv

    Returns:
        List of resolved file paths

    Raises:
        ValueError: If dangerous patterns are detected
    """
    # Validate patterns for dangerous operations
    for pattern in patterns:
        _validate_pattern(pattern)

    if base_path is None:
        base_path = Path.cwd()
    else:
        base_path = Path(base_path).resolve()

    exclude_patterns = exclude_patterns or []
    exclude_paths = _expand_patterns(
        exclude_patterns, base_path, directory_only, skip_ignored_dirs
    )

    all_files = []
    for pattern in patterns:
        files = _expand_pattern(pattern, base_path, directory_only, skip_ignored_dirs)
        # Filter out excluded files
        files = [f for f in files if f not in exclude_paths]
        all_files.extend(files)

    # Remove duplicates while preserving order
    seen = set()
    unique_files = []
    for f in all_files:
        if f not in seen:
            seen.add(f)
            unique_files.append(f)

    # Warn if we found a large number of files
    if len(unique_files) >= 250:
        echo(
            f"Warning: Found {len(unique_files)} files matching the specified patterns. "
            "Processing may take longer than usual. "
            "Consider using more specific patterns if this was not intended.",
            persona=Persona.POWER_USER,
        )

    # Apply max_files limit if specified
    if max_files is not None and len(unique_files) > max_files:
        echo(
            f"Found {len(unique_files)} files, limiting to {max_files}. "
            "Consider using more specific patterns.",
            persona=Persona.POWER_USER,
            err=True,
        )
        unique_files = unique_files[:max_files]

    return unique_files


def _should_skip_dir(dir_path: Path, skip_ignored: bool = True) -> bool:
    """
    Check if a directory should be skipped based on common ignore patterns.

    Args:
        dir_path: Directory path to check
        skip_ignored: Whether to skip commonly ignored directories

    Returns:
        True if directory should be skipped
    """
    if not skip_ignored:
        return False

    dir_name = dir_path.name
    return dir_name in DEFAULT_IGNORE_DIRS or dir_name.endswith(".egg-info")


def _expand_pattern(
    pattern: str,
    base_path: Path,
    directory_only: bool = False,
    skip_ignored_dirs: bool = True,
) -> list[Path]:
    """
    Expand a single pattern into file paths.

    Args:
        pattern: A file pattern (path or glob)
        base_path: Base directory to search from
        directory_only: If True, only include directories in the results
        skip_ignored_dirs: If True, skip commonly ignored directories like node_modules, .venv

    Returns:
        List of matching file paths
    """
    # Expand braces first (now cached with lru_cache)
    expanded_patterns = _expand_braces(pattern)
    all_paths = []
    skipped_dirs = set()

    for expanded_pattern in expanded_patterns:
        # Check if pattern contains glob characters
        has_glob = (
            "**" in expanded_pattern
            or "*" in expanded_pattern
            or "?" in expanded_pattern
        )

        # First check if it's an absolute path
        path = Path(expanded_pattern)

        # If it's an absolute path
        if path.is_absolute():
            if has_glob:
                # Use stdlib glob for absolute paths with globs
                # This handles patterns like /Users/foo/**/*.py correctly
                matches = stdlib_glob.glob(expanded_pattern, recursive=True)

                for match_str in matches:
                    match_path = Path(match_str)
                    if directory_only:
                        if match_path.is_dir():
                            all_paths.append(match_path)
                    else:
                        if match_path.is_file():
                            all_paths.append(match_path)
                continue
            else:
                # Absolute path without glob - check if it exists
                if directory_only:
                    if path.exists() and path.is_dir():
                        # For directory_only, return the directory itself
                        all_paths.append(path)
                        continue
                else:
                    if path.exists() and path.is_file():
                        all_paths.append(path)
                        continue
                    elif path.exists() and path.is_dir():
                        # Only get files directly in this directory, not recursively
                        all_paths.extend([f for f in path.iterdir() if f.is_file()])
                        continue

                # If absolute path doesn't exist, don't process further
                # (no files found, will be reported later)
                continue

        # Handle relative paths
        # Try relative to base_path
        full_path = base_path / path
        if full_path.exists() and not has_glob:
            # Non-glob relative path that exists
            if directory_only:
                if full_path.is_dir():
                    # Return the directory itself and all subdirectories recursively
                    all_paths.append(full_path)
                    all_paths.extend([d for d in full_path.rglob("*") if d.is_dir()])
            else:
                if full_path.is_file():
                    all_paths.append(full_path)
                elif full_path.is_dir():
                    # If it's a directory, get all files in it recursively
                    all_paths.extend([f for f in full_path.rglob("*") if f.is_file()])
        elif has_glob:
            # Treat as glob pattern relative to base_path
            # Use optimized glob that can skip ignored directories
            if skip_ignored_dirs:
                # Use custom implementation for all glob patterns when skipping
                all_paths.extend(
                    _glob_with_ignore(
                        base_path, expanded_pattern, directory_only, skipped_dirs
                    )
                )
            else:
                # Use standard glob when not skipping
                if directory_only:
                    all_paths.extend(
                        m for m in base_path.glob(expanded_pattern) if m.is_dir()
                    )
                else:
                    all_paths.extend(
                        m for m in base_path.glob(expanded_pattern) if m.is_file()
                    )

    # If no matches found and no paths added
    if not all_paths:
        entity_type = "directories" if directory_only else "files"
        echo(
            f"Pattern '{pattern}' did not match any {entity_type}",
            persona=Persona.POWER_USER,
            err=True,
        )

    # Report skipped directories if any
    if skipped_dirs:
        echo(
            f"Warning: Skipped {len(skipped_dirs)} ignored directories: {', '.join(sorted(skipped_dirs))}",
        )

    # Remove duplicates while preserving order
    seen = set()
    unique_paths = []
    for p in all_paths:
        if p not in seen:
            seen.add(p)
            unique_paths.append(p)

    return unique_paths


def _glob_with_ignore(
    base_path: Path, pattern: str, directory_only: bool, skipped_dirs: set
) -> list[Path]:
    """
    Custom glob that skips ignored directories for better performance.

    This implementation walks the directory tree manually and prunes ignored
    directories early, avoiding the need to process files within them.

    Args:
        base_path: Base directory to search from
        pattern: Glob pattern to match
        directory_only: If True, only return directories
        skipped_dirs: Set to track skipped directories for reporting

    Returns:
        List of matching paths
    """
    results = []

    # For simple patterns without **, we can still use glob efficiently
    if "**" not in pattern:
        for match in base_path.glob(pattern):
            # Quick check: if any part of the path is an ignored dir name
            path_parts = set(match.parts)
            ignored_found = path_parts & DEFAULT_IGNORE_DIRS

            if not ignored_found:
                for part in path_parts:
                    if part.endswith(".egg-info"):
                        ignored_found = {part}
                        break

            if ignored_found:
                skipped_dirs.update(ignored_found)
                continue

            if directory_only:
                if match.is_dir():
                    results.append(match)
            else:
                if match.is_file():
                    results.append(match)
        return results

    # For ** patterns, we need to walk the tree manually to prune early
    # Convert ** pattern to a matcher function
    if pattern == "**":
        # Match everything
        file_pattern = "*"
        match_anywhere = True
    elif pattern.startswith("**/"):
        file_pattern = pattern[3:]  # Remove **/
        match_anywhere = True
    else:
        file_pattern = pattern
        match_anywhere = False

    # Walk the directory tree, pruning ignored directories
    for root, dirs, files in os.walk(base_path):
        root_path = Path(root)

        # Prune ignored directories from dirs list (modifies in-place to skip them)
        dirs_to_remove = []
        for d in dirs:
            if d in DEFAULT_IGNORE_DIRS or d.endswith(".egg-info"):
                dirs_to_remove.append(d)
                skipped_dirs.add(d)

        for d in dirs_to_remove:
            dirs.remove(d)

        # Now check files/dirs in this directory
        if directory_only:
            # For directories, check both the current directory and subdirectories
            if root != str(base_path):
                # Check if the current directory matches pattern
                rel_path = root_path.relative_to(base_path)
                rel_path_str = str(rel_path).replace(os.sep, "/")
                dir_name = root_path.name

                if pattern == "**":
                    # ** matches all directories
                    if root_path not in results:
                        results.append(root_path)
                elif match_anywhere:
                    # For **/pattern, only match the directory name itself, not the full path
                    if fnmatch.fnmatch(dir_name, file_pattern):
                        if root_path not in results:  # Avoid duplicates
                            results.append(root_path)
                else:
                    if fnmatch.fnmatch(rel_path_str, file_pattern):
                        if root_path not in results:
                            results.append(root_path)
        else:
            for f in files:
                file_path = root_path / f
                rel_path = file_path.relative_to(base_path)
                rel_path_str = str(rel_path).replace(os.sep, "/")
                if match_anywhere:
                    # Match against filename or full relative path
                    if fnmatch.fnmatch(f, file_pattern) or fnmatch.fnmatch(
                        rel_path_str, file_pattern
                    ):
                        results.append(file_path)
                else:
                    if fnmatch.fnmatch(rel_path_str, file_pattern):
                        results.append(file_path)

    return results


def _expand_patterns(
    patterns: list[str],
    base_path: Path,
    directory_only: bool = False,
    skip_ignored_dirs: bool = True,
) -> set[Path]:
    """
    Expand multiple patterns into a set of file paths.

    Args:
        patterns: List of file patterns
        base_path: Base directory to search from
        directory_only: If True, only include directories in the results
        skip_ignored_dirs: If True, skip commonly ignored directories

    Returns:
        Set of matching file paths
    """
    all_files = set()
    for pattern in patterns:
        all_files.update(
            _expand_pattern(pattern, base_path, directory_only, skip_ignored_dirs)
        )
    return all_files


def filter_by_extensions(
    files: list[Path],
    extensions: Optional[list[str]] = None,
) -> list[Path]:
    """
    Filter files by their extensions.

    Args:
        files: List of file paths
        extensions: List of extensions to include (e.g., ['.py', '.js'])

    Returns:
        Filtered list of file paths
    """
    if not extensions:
        return files

    # Normalize extensions to include dot
    extensions = [ext if ext.startswith(".") else f".{ext}" for ext in extensions]

    return [f for f in files if f.suffix in extensions]


def get_relative_paths(
    files: list[Path],
    base_path: Optional[Path] = None,
) -> list[str]:
    """
    Convert absolute paths to relative paths.

    Args:
        files: List of file paths
        base_path: Base directory to make paths relative to

    Returns:
        List of relative path strings
    """
    if base_path is None:
        base_path = Path.cwd()
    else:
        base_path = Path(base_path).resolve()

    relative_paths = []
    for file in files:
        try:
            rel_path = file.relative_to(base_path)
            relative_paths.append(str(rel_path))
        except ValueError:
            # If file is not under base_path, use absolute path
            relative_paths.append(str(file))

    return relative_paths


def validate_files_exist(files: list[Union[str, Path]]) -> list[Path]:
    """
    Validate that files exist and return resolved paths.

    Args:
        files: List of file paths (as strings or Path objects)

    Returns:
        List of validated Path objects

    Raises:
        FileNotFoundError: If any file does not exist
    """
    validated = []
    for file in files:
        path = Path(file)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file}")
        if not path.is_file():
            raise ValueError(f"Not a file: {file}")
        validated.append(path.resolve())

    return validated


def _validate_pattern(pattern: str) -> None:
    """
    Validate a file pattern for dangerous operations.

    Args:
        pattern: The pattern to validate

    Exits:
        Exits with INVALID_PARAMETERS if the pattern is considered dangerous
    """

    # Check for /**/* pattern (root + recursive + wildcard files) first
    # This is the most dangerous and most specific check - do it early before any other processing
    if pattern.startswith("/**"):
        # Extract what comes after /**
        remainder = pattern[3:]  # Skip /**
        if remainder.startswith("/"):
            remainder = remainder[1:]  # Skip the /

        # Check if remainder is empty (exact /** pattern) or contains wildcards (but not just a specific filename)
        if not remainder or "*" in remainder or "?" in remainder:
            echo(
                f"\nDangerous pattern detected: '{pattern}'",
                err=True,
                log=False,
            )
            echo(
                "\nPatterns starting with '/**' followed by wildcards (like '/**/*.py') would scan the entire filesystem.",
                err=True,
                log=False,
            )
            echo(
                "\nRecommendation: Use more specific patterns instead:",
                err=True,
                log=False,
            )
            echo(
                "  • For files relative to the current directory: '**/*.py'",
                err=True,
                log=False,
            )
            echo(
                "  • For a specific file anywhere: '/**/specific-file.py'",
                err=True,
                log=False,
            )
            echo(
                "  • For a specific directory: '/specific/path/**/*.py'",
                err=True,
                log=False,
            )
            echo(
                "\nFor more information, see: https://docs.zenable.io/integrations/zenable-mcp/commands#file-patterns",
                err=True,
                log=False,
            )
            sys.exit(ExitCode.INVALID_PARAMETERS)

    # Dangerous patterns that could scan entire filesystem
    dangerous_patterns = [
        "/**",  # Recursive scan from root
        "/*",  # All files in root
        "/",  # Root directory
    ]

    # Check for exact dangerous patterns
    if pattern in dangerous_patterns:
        echo(
            f"\nDangerous pattern detected: '{pattern}'",
            err=True,
            log=False,
        )
        echo(
            "\nThis pattern would scan the entire filesystem or root directory.",
            err=True,
            log=False,
        )
        echo(
            "\nRecommendation: Use more specific patterns that target the files you need.",
            err=True,
            log=False,
        )
        echo(
            "\nFor more information, see: https://docs.zenable.io/integrations/zenable-mcp/commands#file-patterns",
            err=True,
            log=False,
        )
        sys.exit(ExitCode.INVALID_PARAMETERS)


def should_skip_file(filename: str, skip_patterns: list[str]) -> bool:
    """
    Check if a file should be skipped based on skip patterns.

    Supports:
    - Exact filename matches (e.g., "package-lock.json")
    - Glob patterns (e.g., "**/*.rbi", "foo/**/*.pyc")
    - Brace expansion (e.g., "*.{log,tmp,bak}", "**/*.{js,ts,jsx,tsx}")
    - Negation patterns with ! prefix (e.g., "!keep-this.json")
    - Escaped ! for literal filenames (e.g., "\\!important.txt" matches "!important.txt")

    Patterns are evaluated in order - the last matching pattern wins.
    This matches .gitignore behavior where later patterns can override earlier ones.

    Args:
        filename: The full file path from the PR
        skip_patterns: List of patterns to check against.
                      Order matters - the last matching pattern wins.

    Returns:
        True if the file should be skipped, False otherwise
    """
    file_path = Path(filename)
    file_parts = file_path.parts
    file_basename = file_path.name

    should_skip = False

    # Pre-expand all patterns once to avoid repeated expansion
    expanded_cache = {}

    for pattern in skip_patterns:
        if pattern.startswith("\\!"):
            literal_pattern = pattern[1:]
            # Use cached expansion
            if literal_pattern not in expanded_cache:
                expanded_cache[literal_pattern] = _expand_braces(literal_pattern)
            expanded_patterns = expanded_cache[literal_pattern]
            for expanded_pattern in expanded_patterns:
                if "*" in expanded_pattern or "?" in expanded_pattern:
                    if _match_glob_pattern(
                        filename, expanded_pattern, file_parts, file_basename
                    ):
                        should_skip = True
                else:
                    if _match_exact_pattern(filename, expanded_pattern, file_basename):
                        should_skip = True
        elif pattern.startswith("!"):
            negated_pattern = pattern[1:]
            # Use cached expansion
            if negated_pattern not in expanded_cache:
                expanded_cache[negated_pattern] = _expand_braces(negated_pattern)
            expanded_patterns = expanded_cache[negated_pattern]
            for expanded_pattern in expanded_patterns:
                if "*" in expanded_pattern or "?" in expanded_pattern:
                    if _match_glob_pattern(
                        filename, expanded_pattern, file_parts, file_basename
                    ):
                        should_skip = False
                else:
                    if _match_exact_pattern(filename, expanded_pattern, file_basename):
                        should_skip = False
        else:
            # Use cached expansion
            if pattern not in expanded_cache:
                expanded_cache[pattern] = _expand_braces(pattern)
            expanded_patterns = expanded_cache[pattern]
            for expanded_pattern in expanded_patterns:
                if "*" in expanded_pattern or "?" in expanded_pattern:
                    if _match_glob_pattern(
                        filename, expanded_pattern, file_parts, file_basename
                    ):
                        should_skip = True
                else:
                    if _match_exact_pattern(filename, expanded_pattern, file_basename):
                        should_skip = True

    return should_skip


def get_file_content(file_path: Path) -> str:
    """
    Get content for a file - either diff in experimental mode or regular content.

    Args:
        file_path: Path to the file

    Returns:
        File content string
    """
    experimental_mode = is_experimental_mode()

    if experimental_mode:
        diff_content = get_git_diff_for_file(file_path)
        if diff_content:
            return diff_content

    return file_path.read_text()
