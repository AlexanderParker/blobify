#!/usr/bin/env python3

import argparse
from pathlib import Path
import mimetypes
import datetime
import os
import sys
import locale
import io
import re
import subprocess
from typing import List, Set, Optional, Tuple, Dict

try:
    import scrubadub

    SCRUBADUB_AVAILABLE = True
except ImportError:
    SCRUBADUB_AVAILABLE = False


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


def get_gitignore_patterns(
    git_root: Path, debug: bool = False
) -> Dict[Path, List[str]]:
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
    root_compiled_patterns = compile_gitignore_patterns(
        patterns_by_dir.get(git_root, [])
    )

    # Get all .gitignore files in subdirectories, but only if their containing directory is not ignored
    for gitignore_file in git_root.rglob(".gitignore"):
        if gitignore_file == repo_gitignore:
            continue

        gitignore_dir = gitignore_file.parent

        # Check if this directory (or any of its parents) is ignored
        if is_directory_ignored(gitignore_dir, git_root, patterns_by_dir, debug):
            if debug:
                rel_dir = gitignore_dir.relative_to(git_root)
                print(
                    f"# SKIPPING .gitignore in ignored directory: {rel_dir}",
                    file=sys.stderr,
                )
            continue

        # This .gitignore is in a non-ignored directory, so include its patterns
        patterns = read_gitignore_file(gitignore_file)
        if patterns:
            patterns_by_dir[gitignore_dir] = patterns
            if debug:
                rel_dir = gitignore_dir.relative_to(git_root)
                print(
                    f"# LOADED .gitignore from: {rel_dir} ({len(patterns)} patterns)",
                    file=sys.stderr,
                )

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

            if test_path and is_path_ignored_by_patterns(
                test_path, compiled_patterns, debug
            ):
                return True

        # Move to the next directory level
        if i < len(path_parts):
            current_dir = current_dir / path_parts[i]

    return False


def is_path_ignored_by_patterns(
    path_str: str, compiled_patterns: List[Tuple[re.Pattern, bool]], debug: bool = False
) -> bool:
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
    pattern = (
        pattern.replace(r"\*", "*")
        .replace(r"\?", "?")
        .replace(r"\[", "[")
        .replace(r"\]", "]")
        .replace(r"\/", "/")
    )

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
    if is_root_relative:
        final_pattern = "^" + pattern + "$"
    else:
        final_pattern = "^(" + pattern + "|.*/" + pattern + ")$"

    return final_pattern


def is_ignored_by_git(
    file_path: Path,
    git_root: Path,
    patterns_by_dir: Dict[Path, List[str]],
    debug: bool = False,
) -> bool:
    """
    Check if a file should be ignored based on gitignore patterns.
    Only considers patterns from gitignore files in parent directories.
    """
    # Get relative path from git root - use resolved paths for consistency
    try:
        relative_path = file_path.resolve().relative_to(git_root)
    except ValueError:
        # File is not within the git repository, so it can't be ignored by git
        return False

    # Convert to forward slashes for consistent matching
    relative_path_str = str(relative_path).replace("\\", "/")

    # Check if file is ignored by walking up the directory tree
    is_ignored = False
    current_path = relative_path

    # Debug: For specific files, show detailed matching
    debug_this_file = debug and (
        relative_path_str == "local.settings.json"
        or "settings" in relative_path_str.lower()
    )

    if debug_this_file:
        print(f"# DEBUG: Processing {relative_path_str}", file=sys.stderr)

    # Walk up the directory tree, checking gitignore patterns at each level
    while True:
        current_dir = (
            git_root / current_path.parent
            if current_path.parent != Path(".")
            else git_root
        )

        # Check if this directory has gitignore patterns
        if current_dir in patterns_by_dir:
            # Calculate the path relative to this gitignore file
            if current_path.parent == Path("."):
                # File is at git root level
                test_path = relative_path_str
            else:
                # Calculate path relative to the current directory
                try:
                    test_relative_path = relative_path.relative_to(current_path.parent)
                    test_path = str(test_relative_path).replace("\\", "/")
                except ValueError:
                    test_path = relative_path_str

            # Compile patterns for this directory
            compiled_patterns = compile_gitignore_patterns(patterns_by_dir[current_dir])

            if debug_this_file:
                print(
                    f"# DEBUG: Checking patterns from {current_dir.relative_to(git_root) if current_dir != git_root else '.'}",
                    file=sys.stderr,
                )
                print(f"# DEBUG: Test path: {test_path}", file=sys.stderr)

            # Check patterns from this directory
            for i, (pattern, is_negation) in enumerate(compiled_patterns):
                matched = pattern.match(test_path)

                if debug_this_file and ("settings" in pattern.pattern.lower() or i < 3):
                    print(
                        f"# DEBUG: Pattern {i}: '{pattern.pattern}' -> matched={bool(matched)}, is_negation={is_negation}",
                        file=sys.stderr,
                    )

                if matched:
                    if is_negation:
                        is_ignored = False  # Negation pattern un-ignores the file
                    else:
                        is_ignored = True  # Normal pattern ignores the file

                    if debug_this_file:
                        print(
                            f"# DEBUG: Pattern {i} matched! Setting is_ignored={is_ignored}",
                            file=sys.stderr,
                        )

        # Move up one directory level
        if current_path.parent == Path("."):
            break
        current_path = current_path.parent

    if debug_this_file:
        print(
            f"# DEBUG: Final result for {relative_path_str}: is_ignored={is_ignored}",
            file=sys.stderr,
        )

    return is_ignored


def scrub_content(content: str, enabled: bool = True) -> str:
    """
    Attempt to detect and replace sensitive data in file content using scrubadub.

    WARNING: This is a best-effort attempt at data scrubbing. The scrubadub library
    may miss sensitive data or incorrectly identify non-sensitive data. Users must
    review output before sharing to ensure no sensitive information remains.

    Args:
        content: The file content to process
        enabled: Whether scrubbing is enabled (True by default)

    Returns:
        Scrubbed content if enabled and scrubadub is available, otherwise original content
    """
    if not enabled or not SCRUBADUB_AVAILABLE:
        return content

    try:
        scrubber = scrubadub.Scrubber()
        return scrubber.clean(content)
    except Exception as e:
        # If scrubbing fails, return original content and warn
        print(f"# WARNING: scrubadub processing failed: {e}", file=sys.stderr)
        return content


def is_text_file(file_path):
    """
    Determine if a file is a text file using multiple detection methods.
    """
    # Known text file extensions
    TEXT_EXTENSIONS = {
        ".txt",
        ".md",
        ".csv",
        ".log",
        ".json",
        ".yaml",
        ".yml",
        ".xml",
        ".html",
        ".htm",
        ".css",
        ".js",
        ".py",
        ".java",
        ".c",
        ".cpp",
        ".h",
        ".hpp",
        ".cs",
        ".rb",
        ".php",
        ".pl",
        ".sh",
        ".bat",
        ".ps1",
        ".ini",
        ".cfg",
        ".conf",
        ".properties",
        ".env",
        ".rst",
        ".tex",
        ".sql",
        ".r",
        ".m",
        ".swift",
        ".kt",
        ".kts",
        ".ts",
        ".tsx",
        ".jsx",
        ".vue",
        ".go",
        ".gd",
    }

    # Security-sensitive file extensions to exclude
    SECURITY_EXTENSIONS = {
        # Certificates
        ".crt",
        ".cer",
        ".der",
        ".p7b",
        ".p7c",
        ".p12",
        ".pfx",
        ".pem",
        # Keys
        ".key",
        ".keystore",
        ".jks",
        ".p8",
        ".pkcs12",
        ".pk8",
        ".pkcs8",
        ".asc",
        ".ppk",
        ".pub",
        # Certificate signing requests
        ".csr",
        ".spc",
        # Other security files
        ".gpg",
        ".pgp",
        ".asc",
        ".kdb",
        ".sig",
    }

    # First check extension
    file_suffix = file_path.suffix.lower()
    if file_suffix in SECURITY_EXTENSIONS:
        return False

    if file_suffix not in TEXT_EXTENSIONS:
        return False

    # Then check mimetype
    mime_type, _ = mimetypes.guess_type(str(file_path))
    if mime_type and not any(
        t in mime_type for t in ["text", "xml", "json", "javascript", "typescript"]
    ):
        return False

    # Finally, check content
    try:
        with open(file_path, "rb") as f:
            # Read first 8KB for analysis
            chunk = f.read(8192)

            # Check for common binary file signatures
            if chunk.startswith(bytes([0x7F, 0x45, 0x4C, 0x46])):  # ELF
                return False
            if chunk.startswith(bytes([0x4D, 0x5A])):  # PE/DOS
                return False
            if chunk.startswith(bytes([0x50, 0x4B, 0x03, 0x04])):  # ZIP
                return False
            if chunk.startswith(bytes([0x25, 0x50, 0x44, 0x46])):  # PDF
                return False

            # Check for high concentration of null bytes or non-ASCII characters
            null_count = chunk.count(0)
            if null_count > len(chunk) * 0.3:  # More than 30% nulls
                return False

            # Try decoding as UTF-8
            try:
                chunk.decode("utf-8")
                return True
            except UnicodeDecodeError:
                return False

    except (IOError, OSError):
        return False


def get_file_metadata(file_path):
    """
    Get file metadata including creation time, modification time, and size.
    """
    stats = file_path.stat()
    return {
        "size": stats.st_size,
        "created": datetime.datetime.fromtimestamp(stats.st_ctime).isoformat(),
        "modified": datetime.datetime.fromtimestamp(stats.st_mtime).isoformat(),
        "accessed": datetime.datetime.fromtimestamp(stats.st_atime).isoformat(),
    }


def scan_directory(directory_path, debug=False, scrub_data=True):
    """
    Recursively scan directory for text files and build index and content.
    """
    directory = Path(directory_path)
    text_files = []
    index = []
    content = []

    # Check if we're in a git repository
    git_root = is_git_repository(directory)
    patterns_by_dir = {}

    if git_root:
        print(f"# Git repository detected at: {git_root}", file=sys.stderr)
        patterns_by_dir = get_gitignore_patterns(git_root, debug)
        total_patterns = sum(len(patterns) for patterns in patterns_by_dir.values())
        print(
            f"# Loaded {total_patterns} gitignore patterns from {len(patterns_by_dir)} locations",
            file=sys.stderr,
        )

        # Debug: Show some patterns only if debug mode is enabled
        if debug and patterns_by_dir:
            print("# Gitignore locations and sample patterns:", file=sys.stderr)
            for gitignore_dir, patterns in list(patterns_by_dir.items())[:3]:
                rel_dir = (
                    gitignore_dir.relative_to(git_root)
                    if gitignore_dir != git_root
                    else "."
                )
                print(f"#   {rel_dir}: {len(patterns)} patterns", file=sys.stderr)
                for pattern in patterns[:2]:
                    regex_pattern = gitignore_to_regex(pattern)
                    print(f"#     '{pattern}' -> '{regex_pattern}'", file=sys.stderr)
            if len(patterns_by_dir) > 3:
                print(
                    f"#   ... and {len(patterns_by_dir) - 3} more locations",
                    file=sys.stderr,
                )

    # Check scrubadub availability and warn if needed
    if scrub_data and not SCRUBADUB_AVAILABLE:
        print(
            "# WARNING: scrubadub not installed - sensitive data will NOT be processed",
            file=sys.stderr,
        )
        print("# Install with: pip install scrubadub", file=sys.stderr)
        scrub_data = False

    # Header explaining the file format
    git_info = (
        f"\n# Git repository: {git_root}" if git_root else "\n# Not in a git repository"
    )
    scrubbing_info = ""
    if scrub_data and SCRUBADUB_AVAILABLE:
        scrubbing_info = (
            "\n# Content processed with scrubadub for sensitive data detection"
        )
        scrubbing_info += (
            "\n# WARNING: Review output carefully - scrubadub may miss sensitive data"
        )
    elif not scrub_data:
        scrubbing_info = "\n# Sensitive data scrubbing DISABLED (--noclean flag used)"
    else:
        scrubbing_info = (
            "\n# Sensitive data scrubbing UNAVAILABLE (scrubadub not installed)"
        )

    header = """# Blobify Text File Index
# Generated: {datetime}
# Source Directory: {directory}{git_info}{scrubbing_info}
#
# This file contains an index and contents of all text files found in the specified directory.
# Format:
# 1. File listing with relative paths
# 2. Content sections for each file, including metadata and full content
# 3. Each file section is marked with START_FILE and END_FILE delimiters
# 
# Files ignored by .gitignore are listed in the index but marked as [IGNORED BY GITIGNORE]
# and their content is excluded with a placeholder message.
#
# This format is designed to be both human-readable and machine-parseable.
# Files are ordered alphabetically by relative path.
#
""".format(
        datetime=datetime.datetime.now().isoformat(),
        directory=str(directory.absolute()),
        git_info=git_info,
        scrubbing_info=scrubbing_info,
    )

    # Define patterns to ignore
    IGNORED_PATTERNS = {
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

    # Helper function to check if path should be ignored
    def should_ignore(path):
        # Check if any part of the path starts with a dot
        if any(part.startswith(".") for part in path.parts):
            return True
        # Check if any part of the path matches ignored patterns
        return any(pattern in path.parts for pattern in IGNORED_PATTERNS)

    # Recursively find all files
    files_ignored = 0
    files_checked = 0
    ignored_files = []  # Track ignored files for the index

    for file_path in directory.rglob("*"):
        if (
            file_path.is_file()
            and not should_ignore(file_path)
            and is_text_file(file_path)
        ):
            files_checked += 1

            # Get relative path for consistent cross-platform representation
            relative_path = file_path.relative_to(directory)

            # Check gitignore if we're in a git repository
            is_git_ignored = False
            if git_root and patterns_by_dir:
                # Only check gitignore if the file is within the git repository
                try:
                    git_relative_path = file_path.resolve().relative_to(git_root)
                    git_relative_str = str(git_relative_path).replace("\\", "/")

                    is_git_ignored = is_ignored_by_git(
                        file_path, git_root, patterns_by_dir, debug
                    )

                    if is_git_ignored:
                        files_ignored += 1
                        ignored_files.append(relative_path)
                        if debug:
                            print(f"# IGNORED: {git_relative_str}", file=sys.stderr)

                except ValueError as e:
                    # File is not within git repository, skip gitignore check
                    if debug:
                        print(
                            f"# NOT IN GIT REPO: {relative_path} (Error: {e})",
                            file=sys.stderr,
                        )

            # Add to index regardless of whether it's ignored
            text_files.append((relative_path, file_path, is_git_ignored))

            # Add to index list with appropriate marking
            if is_git_ignored:
                index.append(f"{relative_path} [IGNORED BY GITIGNORE]")
            else:
                index.append(str(relative_path))

    if git_root:
        print(
            f"# Ignored {files_ignored} files due to gitignore patterns",
            file=sys.stderr,
        )

    # Sort files by name for consistent output
    text_files.sort(key=lambda x: str(x[0]).lower())
    index.sort(key=str.lower)

    # Build index section
    index_section = "# FILE INDEX\n" + "#" * 80 + "\n"
    index_section += "\n".join(index)
    index_section += "\n\n# FILE CONTENTS\n" + "#" * 80 + "\n"

    # Build content section
    for relative_path, file_path, is_ignored in text_files:
        metadata = get_file_metadata(file_path)

        content.append("\nSTART_FILE: {}\n".format(relative_path))
        content.append("FILE_METADATA:")
        content.append(f"  Path: {relative_path}")
        content.append(f"  Size: {metadata['size']} bytes")
        content.append(f"  Created: {metadata['created']}")
        content.append(f"  Modified: {metadata['modified']}")
        content.append(f"  Accessed: {metadata['accessed']}")

        if is_ignored:
            content.append(f"  Status: IGNORED BY GITIGNORE")
        elif scrub_data and SCRUBADUB_AVAILABLE:
            content.append(f"  Status: PROCESSED WITH SCRUBADUB")

        content.append("\nFILE_CONTENT:")

        if is_ignored:
            content.append("[Content excluded - file ignored by .gitignore]")
        else:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    file_content = f.read()

                # Attempt to scrub content if enabled
                processed_content = scrub_content(file_content, scrub_data)
                content.append(processed_content)

            except Exception as e:
                content.append(f"[Error reading file: {str(e)}]")

        content.append("\nEND_FILE: {}\n".format(relative_path))

    return header + index_section + "".join(content)


def setup_console():
    """
    Set up console for proper UTF-8 output on Windows
    """
    if sys.platform == "win32":
        # Configure stdout
        if sys.stdout.isatty():
            # Terminal output
            sys.stdout.reconfigure(encoding="utf-8")
        else:
            # Piped output
            sys.stdout = io.TextIOWrapper(
                sys.stdout.buffer,
                encoding="utf-8",
                errors="replace",
                line_buffering=True,
            )

        # Configure stderr
        sys.stderr.reconfigure(encoding="utf-8")


def main():
    # Set up proper console encoding
    setup_console()

    parser = argparse.ArgumentParser(
        description="Recursively scan directory for text files and create index. Respects .gitignore when in a git repository. Attempts to detect and replace sensitive data using scrubadub by default."
    )
    parser.add_argument("directory", help="Directory to scan")
    parser.add_argument("output", nargs="?", help="Output file (optional)")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug output for gitignore processing",
    )
    parser.add_argument(
        "--noclean",
        action="store_true",
        help="Disable scrubadub processing of sensitive data (emails, names, etc.)",
    )
    args = parser.parse_args()

    try:
        result = scan_directory(
            args.directory, debug=args.debug, scrub_data=not args.noclean
        )

        # Remove BOM if present
        if result.startswith("\ufeff"):
            result = result[1:]

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(result)
        else:
            sys.stdout.write(result)
            sys.stdout.flush()

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
