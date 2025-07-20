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
import fnmatch

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


def read_blobify_config(git_root: Path, debug: bool = False) -> Tuple[List[str], List[str]]:
    """
    Read .blobify configuration file from git root.
    Returns tuple of (include_patterns, exclude_patterns).
    """
    blobify_file = git_root / ".blobify"
    include_patterns = []
    exclude_patterns = []
    
    if not blobify_file.exists():
        if debug:
            print("# No .blobify file found", file=sys.stderr)
        return include_patterns, exclude_patterns
    
    try:
        with open(blobify_file, "r", encoding="utf-8", errors="ignore") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith("#"):
                    continue
                
                if line.startswith("+"):
                    # Include pattern
                    pattern = line[1:].strip()
                    if pattern:
                        include_patterns.append(pattern)
                        if debug:
                            print(f"# .blobify line {line_num}: Include pattern '{pattern}'", file=sys.stderr)
                elif line.startswith("-"):
                    # Exclude pattern
                    pattern = line[1:].strip()
                    if pattern:
                        exclude_patterns.append(pattern)
                        if debug:
                            print(f"# .blobify line {line_num}: Exclude pattern '{pattern}'", file=sys.stderr)
                else:
                    if debug:
                        print(f"# .blobify line {line_num}: Ignoring invalid pattern '{line}' (must start with + or -)", file=sys.stderr)
        
        if debug:
            print(f"# Loaded .blobify config: {len(include_patterns)} include patterns, {len(exclude_patterns)} exclude patterns", file=sys.stderr)
    
    except (IOError, OSError) as e:
        if debug:
            print(f"# Error reading .blobify file: {e}", file=sys.stderr)
    
    return include_patterns, exclude_patterns


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


def scan_directory(
    directory_path, debug=False, scrub_data=True, include_line_numbers=True
):
    """
    Recursively scan directory for text files and build index and content.
    Uses a two-sweep approach:
    1. First sweep: Apply gitignore and built-in exclusions
    2. Second sweep: Apply .blobify overrides
    """
    directory = Path(directory_path)

    # Check if we're in a git repository
    git_root = is_git_repository(directory)
    patterns_by_dir = {}
    blobify_include_patterns = []
    blobify_exclude_patterns = []

    if git_root:
        print(f"# Git repository detected at: {git_root}", file=sys.stderr)
        patterns_by_dir = get_gitignore_patterns(git_root, debug)
        total_patterns = sum(len(patterns) for patterns in patterns_by_dir.values())
        print(
            f"# Loaded {total_patterns} gitignore patterns from {len(patterns_by_dir)} locations",
            file=sys.stderr,
        )

        # Load .blobify configuration
        blobify_include_patterns, blobify_exclude_patterns = read_blobify_config(git_root, debug)

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
    blobify_info = ""
    if git_root and (blobify_include_patterns or blobify_exclude_patterns):
        blobify_info = f"\n# .blobify configuration: {len(blobify_include_patterns)} include patterns, {len(blobify_exclude_patterns)} exclude patterns"
    
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
# Source Directory: {directory}{git_info}{blobify_info}{scrubbing_info}
#
# This file contains an index and contents of all text files found in the specified directory.
# Format:
# 1. File listing with relative paths
# 2. Content sections for each file, including metadata and full content
# 3. Each file section is marked with START_FILE and END_FILE delimiters
# 
# Files ignored by .gitignore are listed in the index but marked as [IGNORED BY GITIGNORE]
# Files excluded by .blobify are listed in the index but marked as [EXCLUDED BY .blobify]
# and their content is excluded with a placeholder message.
#
# This format is designed to be both human-readable and machine-parseable.
# Files are ordered alphabetically by relative path.
#
""".format(
        datetime=datetime.datetime.now().isoformat(),
        directory=str(directory.absolute()),
        git_info=git_info,
        blobify_info=blobify_info,
        scrubbing_info=scrubbing_info,
    )

    # Define patterns to ignore (built-in exclusions)
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

    # FIRST SWEEP: Apply gitignore and built-in exclusions
    print("# First sweep: applying gitignore and built-in exclusions", file=sys.stderr)
    
    all_files = []
    gitignored_directories = []  # Track gitignored directories to show in index
    
    for root, dirs, files in os.walk(directory):
        root_path = Path(root)
        
        # Skip directories based on built-in patterns
        dirs_to_remove = []
        for dir_name in dirs:
            dir_path = root_path / dir_name
            
            # Check built-in patterns
            if dir_name in IGNORED_PATTERNS:
                dirs_to_remove.append(dir_name)
                continue
            
            # Check if directory starts with . but allow if .blobify might include files from it
            if dir_name.startswith("."):
                # Check if any .blobify include patterns might match files in this directory
                should_skip_dot_dir = True
                if blobify_include_patterns:
                    try:
                        dir_relative = dir_path.relative_to(directory)
                        dir_relative_str = str(dir_relative).replace("\\", "/")
                        
                        for pattern in blobify_include_patterns:
                            # Check if pattern could match files in this directory
                            if (pattern.startswith(dir_relative_str + "/") or 
                                pattern.startswith(dir_name + "/") or
                                pattern.startswith("." + dir_name.lstrip('.') + "/") or
                                fnmatch.fnmatch(dir_relative_str, pattern.split('/')[0] if '/' in pattern else pattern)):
                                should_skip_dot_dir = False
                                if debug:
                                    print(f"# NOT SKIPPING dot directory '{dir_relative}' due to .blobify pattern '{pattern}'", file=sys.stderr)
                                break
                    except ValueError:
                        # If we can't get relative path, be safe and don't skip
                        should_skip_dot_dir = False
                
                if should_skip_dot_dir:
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
                            print(f"# SKIPPING gitignored directory: {relative_dir}", file=sys.stderr)
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
                if file_name in IGNORED_PATTERNS or file_name.startswith("."):
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
                all_files.append({
                    'path': file_path,
                    'relative_path': relative_path,
                    'is_git_ignored': is_git_ignored,
                    'is_blobify_excluded': False,
                    'is_blobify_included': False,  # Track if included by .blobify
                    'include_in_output': not is_git_ignored  # Include if not git ignored
                })

    print(f"# First sweep result: {len(all_files)} files", file=sys.stderr)

    # SECOND SWEEP: Apply .blobify rules to build additions and removals
    files_to_add = []
    files_to_remove = []
    
    if git_root and (blobify_include_patterns or blobify_exclude_patterns):
        print("# Second sweep: applying .blobify patterns", file=sys.stderr)
        
        # Find ALL files again (including gitignored ones) for pattern matching
        all_possible_files = []
        for root, dirs, files in os.walk(directory):
            root_path = Path(root)
            
            # Only skip built-in patterns, not gitignore
            dirs_to_remove = []
            for dir_name in dirs:
                if dir_name in IGNORED_PATTERNS or dir_name.startswith("."):
                    dirs_to_remove.append(dir_name)
            
            for dir_name in dirs_to_remove:
                dirs.remove(dir_name)
            
            for file_name in files:
                file_path = root_path / file_name
                if file_name in IGNORED_PATTERNS or file_name.startswith("."):
                    continue
                all_possible_files.append(file_path)
        
        # Apply .blobify patterns in order (both + and - patterns)
        all_blobify_patterns = []
        for pattern in blobify_exclude_patterns:
            all_blobify_patterns.append(('-', pattern))
        for pattern in blobify_include_patterns:
            all_blobify_patterns.append(('+', pattern))
        
        # Sort patterns to maintain the order they appeared in the .blobify file
        # We need to reconstruct the original order from the file
        original_patterns = []
        if git_root:
            blobify_file = git_root / ".blobify"
            if blobify_file.exists():
                try:
                    with open(blobify_file, "r", encoding="utf-8", errors="ignore") as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith("#"):
                                if line.startswith("+"):
                                    pattern = line[1:].strip()
                                    if pattern:
                                        original_patterns.append(('+', pattern))
                                elif line.startswith("-"):
                                    pattern = line[1:].strip()
                                    if pattern:
                                        original_patterns.append(('-', pattern))
                except (IOError, OSError):
                    pass
        
        # If we couldn't read the original order, fall back to exclude-then-include
        if not original_patterns:
            original_patterns = all_blobify_patterns
        
        # Apply patterns in original file order
        for op, pattern in original_patterns:
            for file_path in all_possible_files:
                if matches_pattern(file_path, git_root, pattern):
                    relative_path = file_path.relative_to(directory)
                    
                    if op == '+':  # Include pattern
                        # Check if this pattern matches the exact file path (no wildcards in the match)
                        relative_path_str = str(relative_path).replace("\\", "/")
                        is_exact_file_match = (
                            relative_path_str == pattern or
                            (not ("*" in pattern or "?" in pattern) and not pattern.endswith("/"))
                        )
                        
                        # If it's not an exact file match, check if it's a text file
                        if not is_exact_file_match and not is_text_file(file_path):
                            continue
                        
                        # Check if this file is already in our all_files list
                        found_existing = False
                        for file_info in all_files:
                            if file_info['relative_path'] == relative_path:
                                # File exists, if it was gitignored or excluded, include it
                                file_info['is_git_ignored'] = False
                                file_info['is_blobify_excluded'] = False
                                file_info['is_blobify_included'] = True
                                file_info['include_in_output'] = True
                                found_existing = True
                                if debug:
                                    print(f"# .blobify INCLUDE: '{relative_path}' by pattern '{pattern}'", file=sys.stderr)
                                break
                        
                        # If not in list at all, add it (but check files_to_add for duplicates)
                        if not found_existing:
                            # Check if already in files_to_add
                            already_in_to_add = False
                            for existing_file in files_to_add:
                                if existing_file['relative_path'] == relative_path:
                                    already_in_to_add = True
                                    break
                            
                            if not already_in_to_add:
                                files_to_add.append({
                                    'path': file_path,
                                    'relative_path': relative_path,
                                    'is_git_ignored': False,
                                    'is_blobify_excluded': False,
                                    'is_blobify_included': True,
                                    'include_in_output': True
                                })
                                bypass_msg = " (bypassing text file check)" if is_exact_file_match else ""
                                if debug:
                                    print(f"# .blobify ADD: '{relative_path}' matches pattern '{pattern}'{bypass_msg}", file=sys.stderr)
                            elif debug:
                                print(f"# .blobify ALREADY ADDED: '{relative_path}' matches pattern '{pattern}' but already in list", file=sys.stderr)
                    
                    else:  # Exclude pattern (op == '-')
                        # Check if this file is in our all_files list or files_to_add
                        relative_path = file_path.relative_to(directory)
                        
                        # Remove from all_files if present
                        for file_info in all_files:
                            if file_info['relative_path'] == relative_path:
                                file_info['include_in_output'] = False
                                file_info['is_blobify_excluded'] = True
                                file_info['is_blobify_included'] = False
                                if debug:
                                    print(f"# .blobify EXCLUDE: '{relative_path}' by pattern '{pattern}'", file=sys.stderr)
                                break
                        
                        # Remove from files_to_add if present
                        files_to_add = [f for f in files_to_add if f['relative_path'] != relative_path]
        
        print(f"# Second sweep: {len(files_to_add)} files to add, {len(files_to_remove)} files to remove", file=sys.stderr)
    
    # Apply sweep 2 results to sweep 1
    # Remove files marked for removal (this is now handled in the pattern processing above)
    for file_to_remove in files_to_remove:
        file_to_remove['include_in_output'] = False
        file_to_remove['is_blobify_excluded'] = True
    
    # Add files marked for addition
    all_files.extend(files_to_add)

    # Count final results
    included_files = [f for f in all_files if f['include_in_output']]
    git_ignored_files = [f for f in all_files if f['is_git_ignored']]
    blobify_excluded_files = [f for f in all_files if f['is_blobify_excluded']]
    
    print(f"# Final results: {len(included_files)} included, {len(git_ignored_files)} git ignored, {len(blobify_excluded_files)} blobify excluded", file=sys.stderr)

    # Build index and content
    index = []
    content = []
    
    # Sort all files for consistent output
    all_files.sort(key=lambda x: str(x['relative_path']).lower())
    
    # Add gitignored directories to the index
    for dir_path in sorted(gitignored_directories, key=lambda x: str(x).lower()):
        index.append(f"{dir_path} [IGNORED BY GITIGNORE]")
    
    # Build index for files
    for file_info in all_files:
        relative_path = file_info['relative_path']
        if file_info.get('is_blobify_included', False):
            index.append(f"{relative_path} [INCLUDED BY .blobify]")
        elif file_info['is_git_ignored']:
            index.append(f"{relative_path} [IGNORED BY GITIGNORE]")
        elif file_info['is_blobify_excluded']:
            index.append(f"{relative_path} [EXCLUDED BY .blobify]")
        else:
            index.append(str(relative_path))

    # Build index section
    index_section = "# FILE INDEX\n" + "#" * 80 + "\n"
    index_section += "\n".join(index)
    index_section += "\n\n# FILE CONTENTS\n" + "#" * 80 + "\n"

    # Build content section
    for file_info in all_files:
        file_path = file_info['path']
        relative_path = file_info['relative_path']
        is_git_ignored = file_info['is_git_ignored']
        is_blobify_excluded = file_info['is_blobify_excluded']
        is_blobify_included = file_info.get('is_blobify_included', False)
        
        metadata = get_file_metadata(file_path)

        content.append("\nSTART_FILE: {}\n".format(relative_path))
        content.append("FILE_METADATA:")
        content.append(f"  Path: {relative_path}")
        content.append(f"  Size: {metadata['size']} bytes")
        content.append(f"  Created: {metadata['created']}")
        content.append(f"  Modified: {metadata['modified']}")
        content.append(f"  Accessed: {metadata['accessed']}")

        if is_blobify_included:
            content.append(f"  Status: INCLUDED BY .blobify")
        elif is_git_ignored:
            content.append(f"  Status: IGNORED BY GITIGNORE")
        elif is_blobify_excluded:
            content.append(f"  Status: EXCLUDED BY .blobify")
        elif scrub_data and SCRUBADUB_AVAILABLE:
            content.append(f"  Status: PROCESSED WITH SCRUBADUB")

        content.append("\nFILE_CONTENT:")

        if is_git_ignored:
            content.append("[Content excluded - file ignored by .gitignore]")
        elif is_blobify_excluded:
            content.append("[Content excluded - file excluded by .blobify]")
        else:
            try:
                with open(file_path, "r", encoding="utf-8", errors="strict") as f:
                    file_content = f.read()

                # Attempt to scrub content if enabled
                processed_content = scrub_content(file_content, scrub_data)

                # Add line numbers if enabled
                if include_line_numbers:
                    lines = processed_content.split("\n")
                    numbered_lines = []
                    line_number_width = len(str(len(lines)))

                    for i, line in enumerate(lines, 1):
                        line_number = str(i).rjust(line_number_width)
                        numbered_lines.append(f"{line_number}: {line}")

                    processed_content = "\n".join(numbered_lines)

                    # Add line numbers if enabled
                    if include_line_numbers:
                        lines = processed_content.split("\n")
                        numbered_lines = []
                        line_number_width = len(str(len(lines)))

                        for i, line in enumerate(lines, 1):
                            line_number = str(i).rjust(line_number_width)
                            numbered_lines.append(f"{line_number}: {line}")

                        processed_content = "\n".join(numbered_lines)

                    content.append(processed_content)

            except Exception as e:
                content.append(f"[Error reading file: {str(e)}]")

        content.append("\nEND_FILE: {}\n".format(relative_path))

    return header + index_section + "".join(content)


def main():
    # Fix Windows Unicode output by replacing stdout with UTF-8 wrapper
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer, 
            encoding='utf-8', 
            errors='surrogateescape',
            newline='\n'
        )

    parser = argparse.ArgumentParser(
        description="Recursively scan directory for text files and create index. Respects .gitignore when in a git repository. Supports .blobify configuration files for pattern-based overrides. Attempts to detect and replace sensitive data using scrubadub by default."
    )
    parser.add_argument("directory", help="Directory to scan")
    parser.add_argument("output", nargs="?", help="Output file (optional)")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug output for gitignore and .blobify processing",
    )
    parser.add_argument(
        "--noclean",
        action="store_true",
        help="Disable scrubadub processing of sensitive data (emails, names, etc.)",
    )
    parser.add_argument(
        "--no-line-numbers",
        action="store_true",
        help="Disable line numbers in file content output",
    )
    parser.add_argument(
        "--clip",
        action="store_true",
        help="Copy output to clipboard",
    )
    args = parser.parse_args()

    try:
        result = scan_directory(
            args.directory,
            debug=args.debug,
            scrub_data=not args.noclean,
            include_line_numbers=not args.no_line_numbers,
        )

        # Remove BOM if present
        if result.startswith("\ufeff"):
            result = result[1:]

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(result)
        elif args.clip:
            try:
                if sys.platform == "win32":
                    # Simple file-based approach that preserves UTF-8
                    import tempfile
                    import subprocess
                    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, suffix='.txt') as f:
                        f.write(result)
                        temp_file = f.name
                    
                    # Use type command to read file and pipe to clip
                    subprocess.run(f'type "{temp_file}" | clip', shell=True, check=True)
                    
                    # Clean up
                    import os
                    os.unlink(temp_file)
                    
                elif sys.platform == "darwin":  # macOS
                    import subprocess
                    proc = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE, text=True, encoding='utf-8')
                    proc.communicate(result)
                else:  # Linux
                    import subprocess
                    proc = subprocess.Popen(['xclip', '-selection', 'clipboard'], 
                                          stdin=subprocess.PIPE, text=True, encoding='utf-8')
                    proc.communicate(result)
                    
                print("# Output copied to clipboard", file=sys.stderr)
                
            except Exception as e:
                print(f"# Clipboard failed: {e}. Use: blobify . --noclean > file.txt", file=sys.stderr)
                return  # Don't output to stdout if clipboard was requested
        else:
            sys.stdout.write(result)
            sys.stdout.flush()

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()