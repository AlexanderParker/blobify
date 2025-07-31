"""Content processing and scrubbing utilities."""

import datetime
import mimetypes
from pathlib import Path
from typing import Tuple

from .console import print_debug, print_warning

try:
    import scrubadub

    SCRUBADUB_AVAILABLE = True
except ImportError:
    SCRUBADUB_AVAILABLE = False


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
    if not enabled or not SCRUBADUB_AVAILABLE:
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
                print_debug(
                    f"  {filth.type.upper()}: '{original_text}' -> '{filth.replacement_string}' (pos {filth.beg}-{filth.end})"
                )
        elif debug:
            print_debug("scrubadub found no sensitive data")

        cleaned_content = scrubber.clean(content)
        return cleaned_content, len(filth_items)
    except Exception as e:
        # If scrubbing fails, return original content and warn
        print_warning(f"scrubadub processing failed: {e}")
        return content, 0


def is_text_file(file_path: Path) -> bool:
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

    except (IOError, OSError):
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
