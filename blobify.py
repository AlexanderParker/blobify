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
from typing import List, Set, Optional, Tuple


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


def get_gitignore_patterns(git_root: Path) -> List[str]:
    """
    Get gitignore patterns from all .gitignore files in the repository.
    This includes global, repository-level, and directory-level .gitignore files.
    """
    patterns = []
    
    # Get global gitignore
    try:
        result = subprocess.run(
            ["git", "config", "--get", "core.excludesfile"],
            cwd=git_root,
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            global_gitignore = Path(result.stdout.strip()).expanduser()
            if global_gitignore.exists():
                patterns.extend(read_gitignore_file(global_gitignore))
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        pass
    
    # Get repository-level .gitignore
    repo_gitignore = git_root / ".gitignore"
    if repo_gitignore.exists():
        patterns.extend(read_gitignore_file(repo_gitignore))
    
    # Get all .gitignore files in subdirectories
    for gitignore_file in git_root.rglob(".gitignore"):
        if gitignore_file != repo_gitignore:
            patterns.extend(read_gitignore_file(gitignore_file))
    
    return patterns


def read_gitignore_file(gitignore_path: Path) -> List[str]:
    """
    Read and parse a .gitignore file, returning a list of patterns.
    """
    patterns = []
    try:
        with open(gitignore_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if line and not line.startswith('#'):
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
        is_negation = pattern.startswith('!')
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
    is_directory_only = pattern.endswith('/')
    if is_directory_only:
        pattern = pattern[:-1]
    
    # Handle patterns that start with / (root-relative)
    is_root_relative = pattern.startswith('/')
    if is_root_relative:
        pattern = pattern[1:]
    
    # Escape special regex characters except for *, ?, [, ], and /
    pattern = re.escape(pattern)
    
    # Unescape the characters we want to handle specially
    pattern = pattern.replace(r'\*', '*').replace(r'\?', '?').replace(r'\[', '[').replace(r'\]', ']').replace(r'\/', '/')
    
    # Handle gitignore-specific patterns
    # First handle ** (must be done before single *)
    pattern = pattern.replace('**', 'DOUBLESTAR_PLACEHOLDER')
    
    # * matches anything except /
    pattern = pattern.replace('*', '[^/]*')
    
    # Replace placeholder with proper regex for **
    pattern = pattern.replace('DOUBLESTAR_PLACEHOLDER', '.*')
    
    # ? matches any single character except /
    pattern = pattern.replace('?', '[^/]')
    
    # Build the final pattern
    if is_root_relative:
        final_pattern = '^' + pattern + '$'
    else:
        final_pattern = '^(' + pattern + '|.*/' + pattern + ')$'
    
    return final_pattern


def is_ignored_by_git(file_path: Path, git_root: Path, compiled_patterns: List[Tuple[re.Pattern, bool]], debug: bool = False) -> bool:
    """
    Check if a file should be ignored based on gitignore patterns.
    """
    # Get relative path from git root - use resolved paths for consistency
    try:
        relative_path = file_path.resolve().relative_to(git_root)
    except ValueError:
        # File is not within the git repository, so it can't be ignored by git
        return False
    
    # Convert to forward slashes for consistent matching
    relative_path_str = str(relative_path).replace('\\', '/')
    
    # Check if file is ignored
    is_ignored = False
    
    # Debug: For specific files, show detailed matching
    debug_this_file = debug and (relative_path_str == 'local.settings.json' or 'settings' in relative_path_str.lower())
    
    if debug_this_file:
        print(f"# DEBUG: Processing {relative_path_str}", file=sys.stderr)
        print(f"# DEBUG: Found {len(compiled_patterns)} compiled patterns", file=sys.stderr)
    
    for i, (pattern, is_negation) in enumerate(compiled_patterns):
        matched = pattern.match(relative_path_str)
        
        if debug_this_file and ('settings' in pattern.pattern.lower() or i < 5):
            print(f"# DEBUG: Pattern {i}: '{pattern.pattern}' -> matched={bool(matched)}, is_negation={is_negation}", file=sys.stderr)
        
        if matched:
            if is_negation:
                is_ignored = False  # Negation pattern un-ignores the file
            else:
                is_ignored = True   # Normal pattern ignores the file
            
            if debug_this_file:
                print(f"# DEBUG: Pattern {i} matched! Setting is_ignored={is_ignored}", file=sys.stderr)
    
    if debug_this_file:
        print(f"# DEBUG: Final result for {relative_path_str}: is_ignored={is_ignored}", file=sys.stderr)
    
    return is_ignored


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


def scan_directory(directory_path, debug=False):
    """
    Recursively scan directory for text files and build index and content.
    """
    directory = Path(directory_path)
    text_files = []
    index = []
    content = []

    # Check if we're in a git repository
    git_root = is_git_repository(directory)
    compiled_patterns = []
    
    if git_root:
        print(f"# Git repository detected at: {git_root}", file=sys.stderr)
        gitignore_patterns = get_gitignore_patterns(git_root)
        compiled_patterns = compile_gitignore_patterns(gitignore_patterns)
        print(f"# Loaded {len(gitignore_patterns)} gitignore patterns", file=sys.stderr)
        
        # Debug: Show some patterns only if debug mode is enabled
        if debug and gitignore_patterns:
            print("# Sample patterns:", file=sys.stderr)
            for i, pattern in enumerate(gitignore_patterns[:5]):
                regex_pattern = gitignore_to_regex(pattern)
                print(f"#   '{pattern}' -> '{regex_pattern}'", file=sys.stderr)
            if len(gitignore_patterns) > 5:
                print(f"#   ... and {len(gitignore_patterns) - 5} more", file=sys.stderr)

    # Header explaining the file format
    git_info = f"\n# Git repository: {git_root}" if git_root else "\n# Not in a git repository"
    header = """# Blobify Text File Index
# Generated: {datetime}
# Source Directory: {directory}{git_info}
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
        "Release"
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
        if file_path.is_file() and not should_ignore(file_path) and is_text_file(file_path):
            files_checked += 1
            
            # Get relative path for consistent cross-platform representation
            relative_path = file_path.relative_to(directory)
            
            # Check gitignore if we're in a git repository
            is_git_ignored = False
            if git_root and compiled_patterns:
                # Only check gitignore if the file is within the git repository
                try:
                    git_relative_path = file_path.resolve().relative_to(git_root)
                    git_relative_str = str(git_relative_path).replace('\\', '/')
                    
                    is_git_ignored = is_ignored_by_git(file_path, git_root, compiled_patterns, debug)
                    
                    if is_git_ignored:
                        files_ignored += 1
                        ignored_files.append(relative_path)
                        if debug:
                            print(f"# IGNORED: {git_relative_str}", file=sys.stderr)
                        
                except ValueError as e:
                    # File is not within git repository, skip gitignore check
                    if debug:
                        print(f"# NOT IN GIT REPO: {relative_path} (Error: {e})", file=sys.stderr)
            
            # Add to index regardless of whether it's ignored
            text_files.append((relative_path, file_path, is_git_ignored))
            
            # Add to index list with appropriate marking
            if is_git_ignored:
                index.append(f"{relative_path} [IGNORED BY GITIGNORE]")
            else:
                index.append(str(relative_path))
    
    if git_root:
        print(f"# Ignored {files_ignored} files due to gitignore patterns", file=sys.stderr)

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
        
        content.append("\nFILE_CONTENT:")

        if is_ignored:
            content.append("[Content excluded - file ignored by .gitignore]")
        else:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    file_content = f.read()
                content.append(file_content)
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
        description="Recursively scan directory for text files and create index. Respects .gitignore when in a git repository."
    )
    parser.add_argument("directory", help="Directory to scan")
    parser.add_argument("output", nargs="?", help="Output file (optional)")
    parser.add_argument("--debug", action="store_true", help="Enable debug output for gitignore processing")
    args = parser.parse_args()

    try:
        result = scan_directory(args.directory, debug=args.debug)

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