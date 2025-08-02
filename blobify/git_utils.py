"""Git repository utilities and gitignore handling."""

import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .console import print_debug


def is_git_repository(path: Path) -> Optional[Path]:
    """
    Check if the given path is within a git repository.
    Returns the git root directory if found, None otherwise.
    """
    current = path.resolve()
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
    return None


def get_gitignore_patterns(git_root: Path, debug: bool = False) -> Dict[Path, List[str]]:
    """
    Get gitignore patterns from all applicable .gitignore files in the repository.
    Returns a dictionary mapping directory paths to their patterns.
    Only includes .gitignore files that are not themselves in ignored directories.
    """
    patterns_by_dir = {}

    # Get global gitignore
    global_patterns = []
    try:
        result = subprocess.run(
            ["git", "config", "--get", "core.excludesfile"],
            cwd=git_root,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            global_gitignore = Path(result.stdout.strip()).expanduser()
            if global_gitignore.exists():
                global_patterns = read_gitignore_file(global_gitignore)
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        pass

    # Add global patterns to git root
    if global_patterns:
        patterns_by_dir[git_root] = global_patterns

    # Get repository-level .gitignore
    repo_gitignore = git_root / ".gitignore"
    if repo_gitignore.exists():
        repo_patterns = read_gitignore_file(repo_gitignore)
        if repo_patterns:
            if git_root in patterns_by_dir:
                patterns_by_dir[git_root].extend(repo_patterns)
            else:
                patterns_by_dir[git_root] = repo_patterns

    # Compile patterns for the root directory so we can check if subdirectories are ignored
    compile_gitignore_patterns(patterns_by_dir.get(git_root, []))

    # Get all .gitignore files in subdirectories, but only if their containing directory is not ignored
    for gitignore_file in git_root.rglob(".gitignore"):
        if gitignore_file == repo_gitignore:
            continue

        gitignore_dir = gitignore_file.parent

        # Check if this directory (or any of its parents) is ignored
        if is_directory_ignored(gitignore_dir, git_root, patterns_by_dir, debug):
            if debug:
                rel_dir = gitignore_dir.relative_to(git_root)
                print_debug(f"SKIPPING .gitignore in ignored directory: {rel_dir}")
            continue

        # This .gitignore is in a non-ignored directory, so include its patterns
        patterns = read_gitignore_file(gitignore_file)
        if patterns:
            patterns_by_dir[gitignore_dir] = patterns
            if debug:
                rel_dir = gitignore_dir.relative_to(git_root)
                print_debug(f"LOADED .gitignore from: {rel_dir} ({len(patterns)} patterns)")

    return patterns_by_dir


def is_directory_ignored(
    directory: Path,
    git_root: Path,
    patterns_by_dir: Dict[Path, List[str]],
    debug: bool = False,
) -> bool:
    """
    Check if a directory is ignored by checking all applicable gitignore files.
    A directory is ignored if any gitignore pattern from a parent directory matches it.
    """
    # Get relative path from git root
    try:
        rel_path = directory.resolve().relative_to(git_root)
    except ValueError:
        return False

    rel_path_str = str(rel_path).replace("\\", "/")

    # Check each parent directory for gitignore patterns that might apply
    current_dir = git_root
    path_parts = rel_path.parts

    for i in range(len(path_parts) + 1):
        # Check if current_dir has gitignore patterns
        if current_dir in patterns_by_dir:
            compiled_patterns = compile_gitignore_patterns(patterns_by_dir[current_dir])

            # Construct the path relative to the current gitignore's directory
            if i == 0:
                # We're checking from the git root
                test_path = rel_path_str
            else:
                # We're checking from a subdirectory
                remaining_parts = path_parts[i - 1 :]
                test_path = "/".join(remaining_parts) if remaining_parts else ""

            if test_path and is_path_ignored_by_patterns(test_path, compiled_patterns, debug):
                return True

        # Move to the next directory level
        if i < len(path_parts):
            current_dir = current_dir / path_parts[i]

    return False


def is_path_ignored_by_patterns(path_str: str, compiled_patterns: List[Tuple[re.Pattern, bool]], debug: bool = False) -> bool:
    """
    Check if a path is ignored by a set of compiled gitignore patterns.
    """
    is_ignored = False

    for pattern, is_negation in compiled_patterns:
        matched = pattern.match(path_str)

        if matched:
            if is_negation:
                is_ignored = False  # Negation pattern un-ignores the file
            else:
                is_ignored = True  # Normal pattern ignores the file

    return is_ignored


def read_gitignore_file(gitignore_path: Path) -> List[str]:
    """
    Read and parse a .gitignore file, returning a list of patterns.
    """
    patterns = []
    try:
        with open(gitignore_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if line and not line.startswith("#"):
                    patterns.append(line)
    except (IOError, OSError):
        pass
    return patterns


def compile_gitignore_patterns(patterns: List[str]) -> List[Tuple[re.Pattern, bool]]:
    """
    Compile gitignore patterns into regex patterns.
    Returns list of (compiled_pattern, is_negation) tuples.
    """
    compiled_patterns = []

    for pattern in patterns:
        is_negation = pattern.startswith("!")
        if is_negation:
            pattern = pattern[1:]

        # Convert gitignore pattern to regex
        regex_pattern = gitignore_to_regex(pattern)
        try:
            compiled_pattern = re.compile(regex_pattern)
            compiled_patterns.append((compiled_pattern, is_negation))
        except re.error:
            # Skip invalid regex patterns
            continue

    return compiled_patterns


def gitignore_to_regex(pattern: str) -> str:
    """
    Convert a gitignore pattern to a regex pattern.
    """
    # Handle directory-only patterns (ending with /)
    is_directory_only = pattern.endswith("/")
    if is_directory_only:
        pattern = pattern[:-1]

    # Handle patterns that start with / (root-relative)
    is_root_relative = pattern.startswith("/")
    if is_root_relative:
        pattern = pattern[1:]

    # Escape special regex characters except for *, ?, [, ], and /
    pattern = re.escape(pattern)

    # Unescape the characters we want to handle specially
    pattern = pattern.replace(r"\*", "*").replace(r"\?", "?").replace(r"\[", "[").replace(r"\]", "]").replace(r"\/", "/")

    # Handle gitignore-specific patterns
    # First handle ** (must be done before single *)
    pattern = pattern.replace("**", "DOUBLESTAR_PLACEHOLDER")

    # * matches anything except /
    pattern = pattern.replace("*", "[^/]*")

    # Replace placeholder with proper regex for **
    pattern = pattern.replace("DOUBLESTAR_PLACEHOLDER", ".*")

    # ? matches any single character except /
    pattern = pattern.replace("?", "[^/]")

    # Build the final pattern
    if is_directory_only:
        # For directory patterns like "*.egg-info/" or "build/":
        # Match the directory name itself AND anything inside it
        if is_root_relative:
            # Root-relative directory pattern like "/build/"
            final_pattern = f"^({pattern}|{pattern}/.*)$"
        else:
            # Non-root-relative directory pattern like "*.egg-info/" or "node_modules/"
            # This should match:
            # 1. The directory at root: "some.egg-info"
            # 2. Contents of directory at root: "some.egg-info/file.txt"
            # 3. The directory in subdirs: "path/some.egg-info"
            # 4. Contents in subdirs: "path/some.egg-info/file.txt"
            final_pattern = f"^({pattern}|{pattern}/.*|.*/{pattern}|.*/{pattern}/.*)$"
    else:
        # Regular file patterns
        if is_root_relative:
            final_pattern = f"^{pattern}$"
        else:
            final_pattern = f"^({pattern}|.*/{pattern})$"

    return final_pattern


def is_ignored_by_git(
    file_path: Path,
    git_root: Path,
    patterns_by_dir: Dict[Path, List[str]],
    debug: bool = False,
) -> bool:
    """
    Check if a file should be ignored based on gitignore patterns.
    """
    # Get relative path from git root
    try:
        relative_path = file_path.resolve().relative_to(git_root)
    except ValueError:
        return False

    relative_path_str = str(relative_path).replace("\\", "/")

    # Check each gitignore file's patterns
    is_ignored = False

    # We need to check patterns from git root and all parent directories
    # Start from the git root and work our way down
    for gitignore_dir, patterns in patterns_by_dir.items():
        if not patterns:
            continue

        # Calculate the path relative to this gitignore's directory
        try:
            if gitignore_dir == git_root:
                test_path = relative_path_str
            else:
                # This gitignore is in a subdirectory
                gitignore_relative = gitignore_dir.relative_to(git_root)
                if relative_path.is_relative_to(gitignore_relative):
                    # File is in or under this gitignore's directory
                    test_path = str(relative_path.relative_to(gitignore_relative)).replace("\\", "/")
                else:
                    # File is not under this gitignore's influence
                    continue
        except ValueError:
            continue

        # Compile and test patterns
        compiled_patterns = compile_gitignore_patterns(patterns)

        for pattern, is_negation in compiled_patterns:
            matched = pattern.match(test_path)

            if matched:
                if is_negation:
                    is_ignored = False
                else:
                    is_ignored = True

    return is_ignored
