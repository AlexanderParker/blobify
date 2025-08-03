"""Content processing and scrubbing utilities."""

import datetime
import mimetypes
from pathlib import Path
from typing import Tuple

import scrubadub

from .console import print_debug, print_warning


def scrub_content(content: str, enabled: bool = True, debug: bool = False) -> Tuple[str, int]:
    """
    Attempt to detect and replace sensitive data in file content using scrubadub.

    WARNING: This is a best-effort attempt at data scrubbing. The scrubadub library
    may miss sensitive data or incorrectly identify non-sensitive data. Users must
    review output before sharing to ensure no sensitive information remains.

    Args:
        content: The file content to process
        enabled: Whether scrubbing is enabled (True by default)
        debug: Whether to show debug output for replacements

    Returns:
        Tuple of (scrubbed content, number of substitutions made)
    """
    if not enabled:
        return content, 0

    try:
        scrubber = scrubadub.Scrubber()

        # Disable the twitter detector which has too many false positives
        scrubber.remove_detector("twitter")

        # Get filth items for counting and debug output
        filth_items = list(scrubber.iter_filth(content))

        if debug and filth_items:
            print_debug(f"scrubadub found {len(filth_items)} items:")
            for filth in filth_items:
                original_text = content[filth.beg : filth.end]
                print_debug(f"  {filth.type.upper()}: '{original_text}' -> '{filth.replacement_string}' (pos {filth.beg}-{filth.end})")
        elif debug:
            print_debug("scrubadub found no sensitive data")

        cleaned_content = scrubber.clean(content)
        return cleaned_content, len(filth_items)
    except Exception as e:
        # If scrubbing fails, return original content and warn
        print_warning(f"scrubadub processing failed: {e}")
        return content, 0


def parse_named_filters(filter_args: list) -> tuple:
    """
    Parse named filters and return (filters dict, filter_names list).

    Args:
        filter_args: List of "name:regex" strings

    Returns:
        Tuple of (filters dict, filter_names list)
    """
    filters = {}
    filter_names = []

    for filter_arg in filter_args or []:
        if ":" in filter_arg:
            name, pattern = filter_arg.split(":", 1)
            name = name.strip()
            pattern = pattern.strip()
            filters[name] = pattern
            filter_names.append(name)
        else:
            # Fallback: use pattern as both name and pattern
            filters[filter_arg] = filter_arg
            filter_names.append(filter_arg)

    return filters, filter_names


def filter_content_lines(content: str, filters: dict, debug: bool = False) -> str:
    """
    Filter content using named regex patterns (OR logic).

    Args:
        content: The file content to filter
        filters: Dict of {name: regex_pattern}
        debug: Whether to show debug output

    Returns:
        Filtered content with only matching lines
    """
    if not filters:
        return content

    import re

    lines = content.split("\n")
    filtered_lines = []
    total_matches = 0

    for line in lines:
        for name, pattern in filters.items():
            try:
                if re.search(pattern, line):
                    filtered_lines.append(line)
                    total_matches += 1
                    if debug:
                        print_debug(f"Filter '{name}' matched: {line[:50]}...")
                    break  # Found match, move to next line
            except re.error as e:
                if debug:
                    print_warning(f"Invalid regex in filter '{name}': {e}")
                continue  # Skip invalid regex

    if debug:
        print_debug(f"Content filtering: {len(lines)} lines -> {len(filtered_lines)} lines ({total_matches} total matches)")

    return "\n".join(filtered_lines)


def is_text_file(file_path: Path) -> bool:
    """
    Determine if a file is a text file using multiple detection methods.
    """
    # Known text file extensions
    text_extensions = {
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
    security_extensions = {
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
    if file_suffix in security_extensions:
        return False

    if file_suffix not in text_extensions:
        return False

    # Then check mimetype
    mime_type, _ = mimetypes.guess_type(str(file_path))
    if mime_type and not any(t in mime_type for t in ["text", "xml", "json", "javascript", "typescript"]):
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

    except OSError:
        return False


def get_file_metadata(file_path: Path) -> dict:
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
