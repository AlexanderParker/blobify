"""File discovery and pattern matching utilities."""

import fnmatch
import os
from pathlib import Path
from typing import Dict, Optional

from .config import read_blobify_config
from .console import print_debug, print_phase
from .content_processor import is_text_file
from .git_utils import get_gitignore_patterns, is_git_repository, is_ignored_by_git


def matches_pattern(file_path: Path, base_path: Path, pattern: str) -> bool:
    """
    Check if a file matches a given pattern.
    Supports glob patterns and relative paths from base_path.
    """
    try:
        # Get path relative to base path
        relative_path = file_path.resolve().relative_to(base_path.resolve())
        relative_path_str = str(relative_path).replace("\\", "/")

        # Try exact match first
        if relative_path_str == pattern:
            return True

        # Try glob pattern matching
        if fnmatch.fnmatch(relative_path_str, pattern):
            return True

        # Try matching just the filename
        if fnmatch.fnmatch(file_path.name, pattern):
            return True

        # Try matching directory patterns
        if pattern.endswith("/"):
            # Directory pattern - check if file is in this directory
            dir_pattern = pattern[:-1]
            for parent in relative_path.parents:
                parent_str = str(parent).replace("\\", "/")
                if parent_str == dir_pattern or fnmatch.fnmatch(parent_str, dir_pattern):
                    return True

        return False

    except ValueError:
        # File not within base path
        return False


def get_built_in_ignored_patterns() -> set:
    """Get the set of built-in patterns to ignore."""
    return {
        # Dot folders
        ".git",
        ".svn",
        ".hg",
        ".idea",
        ".vscode",
        ".vs",
        # Package manager directories
        "node_modules",
        "bower_components",
        "vendor",
        "packages",
        "venv",
        "env",
        ".env",
        ".venv",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        # Build directories
        "dist",
        "build",
        "target",
        "out",
        "obj",
        "Debug",
        # Others
        ".npm",
        ".yarn",
        "pip-wheel-metadata",
        # Security and certificate directories
        "certs",
        "certificates",
        "keys",
        "private",
        "ssl",
        ".ssh",
        "tls",
        ".gpg",
        ".keyring",
        ".gnupg",
        "release",
        "Release",
        "package-lock.json",
    }


def check_if_dot_item_might_be_included(item_name: str, git_root: Path, context: Optional[str] = None) -> bool:
    """
    Check if a dot file or directory might be included by .blobify patterns.

    By default, blobify excludes all dot files and directories (like .git, .vscode, etc.)
    for performance and cleanliness. However, some dot files are legitimate project
    files that users may want to include (like .github/workflows, .blobify, etc.).

    This function performs a quick check of .blobify include patterns to see if
    a dot item should be preserved for later pattern matching, preventing
    premature exclusion during the first sweep.

    Args:
        item_name: Name of the dot file or directory (e.g., ".github", ".blobify")
        git_root: Root of the git repository where .blobify file is located
        context: Optional context section to read from .blobify file

    Returns:
        True if .blobify patterns might include this item, False otherwise
    """
    if not git_root:
        return False

    try:
        blobify_include_patterns, _, _ = read_blobify_config(git_root, context, False)
        if not blobify_include_patterns:
            return False

        # Check if any include pattern might match this item
        for pattern in blobify_include_patterns:
            # Direct match
            if pattern == item_name:
                return True
            # Wildcard patterns that might match
            if fnmatch.fnmatch(item_name, pattern):
                return True
            # Patterns that might match files within this directory (if it's a directory)
            if pattern.startswith(f"{item_name}/") or pattern.startswith(f"{item_name}\\"):
                return True
            # Patterns like .github/** that would include everything in .github
            if pattern == f"{item_name}/**" or pattern.startswith(f"{item_name}/*"):
                return True

        return False
    except Exception:
        # If we can't read .blobify, err on the side of caution and don't allow
        return False


def discover_files(directory: Path, debug: bool = False) -> Dict:
    """
    First sweep: Apply gitignore and built-in exclusions.
    Returns discovery context with files and git information.
    """
    # Check if we're in a git repository
    git_root = is_git_repository(directory)
    patterns_by_dir = {}

    if git_root:
        if debug:
            print_phase("Git Repository Detection")
            print_debug(f"Git repository detected at: {git_root}")
        patterns_by_dir = get_gitignore_patterns(git_root, debug)
        total_patterns = sum(len(patterns) for patterns in patterns_by_dir.values())
        if debug:
            print_debug(f"Loaded {total_patterns} gitignore patterns from {len(patterns_by_dir)} locations")

    if debug:
        print_phase("First Sweep: Gitignore & Built-in Exclusions")
        print_debug("First sweep: applying gitignore and built-in exclusions")

    ignored_patterns = get_built_in_ignored_patterns()
    all_files = []
    gitignored_directories = []

    for root, dirs, files in os.walk(directory):
        root_path = Path(root)

        # Skip directories based on built-in patterns
        dirs_to_remove = []
        for dir_name in dirs:
            dir_path = root_path / dir_name

            # Check built-in patterns
            if dir_name in ignored_patterns:
                dirs_to_remove.append(dir_name)
                continue

            # Check if directory starts with . but allow if .blobify might include files from it
            if dir_name.startswith("."):
                might_be_included = check_if_dot_item_might_be_included(dir_name, git_root)
                if not might_be_included:
                    dirs_to_remove.append(dir_name)
                    continue

            # Check if directory is gitignored
            if git_root and patterns_by_dir:
                try:
                    is_dir_ignored = is_ignored_by_git(dir_path, git_root, patterns_by_dir, debug)
                    if is_dir_ignored:
                        # Add directory to gitignored list but don't walk into it
                        relative_dir = dir_path.relative_to(directory)
                        gitignored_directories.append(relative_dir)
                        dirs_to_remove.append(dir_name)
                        if debug:
                            print_debug(f"SKIPPING gitignored directory: {relative_dir}")
                        continue
                except Exception:
                    pass

        for dir_name in dirs_to_remove:
            dirs.remove(dir_name)

        # Collect all text files that pass sweep 1
        for file_name in files:
            file_path = root_path / file_name
            if is_text_file(file_path):
                # Skip files with built-in ignored names
                if file_name in ignored_patterns:
                    continue
                # Skip dot files unless .blobify might include them
                if file_name.startswith("."):
                    might_be_included = check_if_dot_item_might_be_included(file_name, git_root)
                    if not might_be_included:
                        continue

                # Check gitignore if we're in a git repo
                is_git_ignored = False
                if git_root and patterns_by_dir:
                    try:
                        is_git_ignored = is_ignored_by_git(file_path, git_root, patterns_by_dir, debug)
                    except Exception:
                        pass

                # Add all files to the list (including gitignored ones for the index)
                relative_path = file_path.relative_to(directory)
                all_files.append(
                    {
                        "path": file_path,
                        "relative_path": relative_path,
                        "is_git_ignored": is_git_ignored,
                        "is_blobify_excluded": False,
                        "is_blobify_included": False,
                        "include_in_output": not is_git_ignored,
                    }
                )

    if debug:
        print_debug(f"First sweep result: {len(all_files)} files")

    return {
        "all_files": all_files,
        "gitignored_directories": gitignored_directories,
        "git_root": git_root,
        "patterns_by_dir": patterns_by_dir,
    }


def apply_blobify_patterns(discovery_context: Dict, directory: Path, context: Optional[str] = None, debug: bool = False) -> None:
    """
    Second sweep: Apply .blobify rules to modify the file list.
    Modifies the discovery context in place.
    """
    all_files = discovery_context["all_files"]
    git_root = discovery_context["git_root"]

    if not git_root:
        return

    # Load .blobify configuration
    if debug:
        print_phase("Blobify Configuration")
    blobify_include_patterns, blobify_exclude_patterns, _ = read_blobify_config(git_root, context, debug)

    if not (blobify_include_patterns or blobify_exclude_patterns):
        return

    if debug:
        print_phase("Second Sweep: Blobify Pattern Application")
        print_debug("Second sweep: applying .blobify patterns")

    # Find ALL files again (including gitignored ones and dot files) for pattern matching
    ignored_patterns = get_built_in_ignored_patterns()
    all_possible_files = []
    for root, dirs, files in os.walk(directory):
        root_path = Path(root)

        # Only skip built-in patterns, not gitignore or dot directories
        dirs_to_remove = []
        for dir_name in dirs:
            if dir_name in ignored_patterns:
                dirs_to_remove.append(dir_name)

        for dir_name in dirs_to_remove:
            dirs.remove(dir_name)

        for file_name in files:
            file_path = root_path / file_name
            if file_name in ignored_patterns:
                continue
            # Include all files including dot files for pattern matching
            all_possible_files.append(file_path)

    # Get original pattern order from file
    original_patterns = []
    blobify_file = git_root / ".blobify"
    if blobify_file.exists():
        try:
            with open(blobify_file, "r", encoding="utf-8", errors="ignore") as f:
                current_context = None
                target_context = context
                in_target_section = target_context is None

                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue

                    # Check for context headers
                    if line.startswith("[") and line.endswith("]"):
                        current_context = line[1:-1]
                        in_target_section = target_context == current_context
                        continue

                    # Only process lines in target context
                    if not in_target_section:
                        continue

                    if line.startswith("@"):
                        continue  # Skip switches
                    elif line.startswith("+"):
                        pattern = line[1:].strip()
                        if pattern:
                            original_patterns.append(("+", pattern))
                    elif line.startswith("-"):
                        pattern = line[1:].strip()
                        if pattern:
                            original_patterns.append(("-", pattern))
        except OSError:
            pass

    # If we couldn't read the original order, fall back to exclude-then-include
    if not original_patterns:
        for pattern in blobify_exclude_patterns:
            original_patterns.append(("-", pattern))
        for pattern in blobify_include_patterns:
            original_patterns.append(("+", pattern))

    files_to_add = []

    # Apply patterns in original file order
    for op, pattern in original_patterns:
        for file_path in all_possible_files:
            if matches_pattern(file_path, git_root, pattern):
                relative_path = file_path.relative_to(directory)

                if op == "+":  # Include pattern
                    # Check if this pattern matches the exact file path (no wildcards in the match)
                    relative_path_str = str(relative_path).replace("\\", "/")
                    is_exact_file_match = relative_path_str == pattern or (not ("*" in pattern or "?" in pattern) and not pattern.endswith("/"))

                    # If it's not an exact file match, check if it's a text file
                    if not is_exact_file_match and not is_text_file(file_path):
                        continue

                    # Check if this file is already in our all_files list
                    found_existing = False
                    for file_info in all_files:
                        if file_info["relative_path"] == relative_path:
                            # File exists, if it was gitignored or excluded, include it
                            file_info["is_git_ignored"] = False
                            file_info["is_blobify_excluded"] = False
                            file_info["is_blobify_included"] = True
                            file_info["include_in_output"] = True
                            found_existing = True
                            if debug:
                                print_debug(f".blobify INCLUDE: '{relative_path}' by pattern '{pattern}'")
                            break

                    # If not in list at all, add it (but check files_to_add for duplicates)
                    if not found_existing:
                        # Check if already in files_to_add
                        already_in_to_add = False
                        for existing_file in files_to_add:
                            if existing_file["relative_path"] == relative_path:
                                already_in_to_add = True
                                break

                        if not already_in_to_add:
                            files_to_add.append(
                                {
                                    "path": file_path,
                                    "relative_path": relative_path,
                                    "is_git_ignored": False,
                                    "is_blobify_excluded": False,
                                    "is_blobify_included": True,
                                    "include_in_output": True,
                                }
                            )
                            bypass_msg = " (bypassing text file check)" if is_exact_file_match else ""
                            if debug:
                                print_debug(f".blobify ADD: '{relative_path}' matches pattern '{pattern}'{bypass_msg}")
                        elif debug:
                            print_debug(f".blobify ALREADY ADDED: '{relative_path}' matches pattern '{pattern}' but already in list")

                else:  # Exclude pattern (op == '-')
                    # Remove from all_files if present
                    for file_info in all_files:
                        if file_info["relative_path"] == relative_path:
                            file_info["include_in_output"] = False
                            file_info["is_blobify_excluded"] = True
                            file_info["is_blobify_included"] = False
                            if debug:
                                print_debug(f".blobify EXCLUDE: '{relative_path}' by pattern '{pattern}'")
                            break

                    # Remove from files_to_add if present
                    files_to_add = [f for f in files_to_add if f["relative_path"] != relative_path]

    # Add new files to the main list
    all_files.extend(files_to_add)

    if debug:
        print_debug(f"Second sweep: {len(files_to_add)} files added")


def scan_files(directory: Path, context: Optional[str] = None, debug: bool = False) -> Dict:
    """
    Main file scanning function that orchestrates the two-sweep approach.
    Returns discovery context with all file information.
    """
    # First sweep: gitignore and built-in exclusions
    discovery_context = discover_files(directory, debug)

    # Second sweep: apply .blobify patterns
    apply_blobify_patterns(discovery_context, directory, context, debug)

    # Count final results
    all_files = discovery_context["all_files"]
    included_files = [f for f in all_files if f["include_in_output"]]
    git_ignored_files = [f for f in all_files if f["is_git_ignored"]]
    blobify_excluded_files = [f for f in all_files if f["is_blobify_excluded"]]

    if debug:
        print_phase("Final Results")
        print_debug(f"Final results: {len(included_files)} included, {len(git_ignored_files)} git ignored, {len(blobify_excluded_files)} blobify excluded")

    discovery_context["included_files"] = included_files
    discovery_context["git_ignored_files"] = git_ignored_files
    discovery_context["blobify_excluded_files"] = blobify_excluded_files

    return discovery_context
