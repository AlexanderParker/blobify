# Blobify Text File Index
# Source Directory: C:\tools\blobify
#
# Content filters applied:
# * classes: ^ *class\s+\w+.*: (files: *.py)
# * functions: ^ *(def\s+\w+.*:|async\s+def\s+\w+.*:) (files: *.py)
# * decorators: ^ *@\w+.* (files: *.py)
# * returns: ^ *(return\s+.*|yield\s+.*) (files: *.py)
# * imports: ^ *(from\s+\w+.*import.*|import\s+\w+.*) (files: *.py)
# * constants: ^ *[A-Z_][A-Z0-9_]*\s*=.* (files: *.py)
# * exceptions: ^ *(raise\s+.*|except\s+.*:|try:|finally:) (files: *.py)
# * docstrings: ^ *\\\".*|^ *'''.*"" (files: *.py)
# * public-classes: ^ *class [A-Z][a-zA-Z0-9_]*[^_].*: (files: *.py)
# * public-functions: ^ *(def|async def) [a-z_][a-zA-Z0-9_]*[^_].*: (files: *.py)
# * module-docs: ^ *\\\".*"" (files: *.py)
# * exports: ^ *__all__\s*=.* (files: *.py)
# * comments: ^ *#.* (files: *.py)
#
# This file contains filtered content of all text files found in the specified directory.
# Format:
# 1. Content sections for each file
# 2. Each file section is marked with START_FILE and END_FILE delimiters
#
# Files ignored by .gitignore or excluded by .blobify have their content excluded
# with a placeholder message.
#
# This format is designed to be both human-readable and machine-parseable.
# Files are ordered alphabetically by relative path.
#

# FILE CONTENTS
################################################################################

START_FILE: blobify\__init__.py
FILE_CONTENT:
__all__ = ["main", "__author__", "__email__", "__version__"]
END_FILE: blobify\__init__.py


START_FILE: blobify\config.py
FILE_CONTENT:
import argparse
import csv
import io
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
def validate_boolean_value(value: str) -> bool:
        return True
        return False
        raise ValueError(f"Invalid boolean value: '{value}'. Use 'true' or 'false'.")
def validate_list_patterns_value(value: str) -> str:
        raise ValueError(f"Invalid list-patterns value: '{value}'. Use one of: {', '.join(allowed_values)}")
    return value
def read_blobify_config(git_root: Path, context: Optional[str] = None, debug: bool = False) -> Tuple[List[str], List[str], List[str]]:
        return [], [], []
    try:
        # Get the target context (default to "default")
            return config["include_patterns"], config["exclude_patterns"], config["default_switches"]
            # If a specific context was requested but doesn't exist, that's an error
                # Show available contexts to help the user
            # If no context was specified and default doesn't exist, return empty
            return [], [], []
    except OSError as e:
        return [], [], []
def _parse_contexts_with_inheritance(blobify_file: Path, debug: bool = False) -> Dict[str, Dict]:
    # Initialize with empty default context
            # Skip empty lines and comments
            # Check for context headers [context-name] or [context-name:parent] or [context-name:parent1,parent2]
                # Error if trying to redefine default context
                    raise ValueError(f"Line {line_num}: Cannot redefine 'default' context")
                # Error if context already exists
                    raise ValueError(f"Line {line_num}: Context '{context_name}' already defined")
                # Create new context
                    # Check all parents exist
                        raise ValueError(f"Line {line_num}: Parent context(s) not found: {missing_str}")
                    # Merge all parent contexts
                    # No parent specified, create empty context
            # Process patterns and switches for current context
                # Configuration option pattern
                    # Check if this is a key=value option or legacy boolean switch
                        # Legacy boolean switch format - treat as key=true
                    # For filter options, allow multiple entries; for others, "last value wins"
                        # Allow multiple filter entries
                        # Implement "last value wins" - remove any previous entries for this key
                        # Add the new entry
                # Include pattern
                # Exclude pattern
    return contexts
def get_available_contexts(git_root: Path, debug: bool = False) -> List[str]:
        return contexts
    try:
                # Skip empty lines and comments
                # Check for context headers [context-name] or [context-name:parent] or [context-name:parent1,parent2]
    except OSError as e:
    return contexts
def get_context_descriptions(git_root: Path) -> Dict[str, str]:
        return descriptions
    try:
                # Collect comments that might describe the next context
                # Check for context headers [context-name] or [context-name:parent] or [context-name:parent1,parent2]
                        # Use the last meaningful comment as description
                # Clear pending comments when we hit patterns/switches
    except OSError:
    return descriptions
def list_available_contexts(directory: Path):
    # Try to read context descriptions and inheritance info
def _get_context_inheritance_info(git_root: Path) -> Dict[str, str]:
        return inheritance_info
    try:
    except OSError:
    return inheritance_info
def apply_default_switches(args: argparse.Namespace, default_switches: List[str], debug: bool = False) -> argparse.Namespace:
        return args
    # Convert args to dict for easier manipulation
    # Process default switches and combine with command line
        # Parse the option
            # Legacy format support - treat as boolean=true
        # Convert key to argument name (handle dashes/underscores)
        # Handle filter options specially - always accumulate them
            # Parse CSV format for filters
            try:
                    # Convert back to CSV format for consistency with command line
            except (csv.Error, StopIteration):
        # For non-filter options, only apply if not already set by command line
            # Determine if this is the default value based on the argument type
                # For boolean options, check against expected defaults
                try:
                        # Handle output filename
                        # Handle list-patterns option
                        # Handle boolean options
                except ValueError as e:
    # Convert back to namespace
    return argparse.Namespace(**args_dict)
END_FILE: blobify\config.py


START_FILE: blobify\console.py
FILE_CONTENT:
import sys
from typing import Optional
try:
    from rich.console import Console
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
# Initialize console for rich output
def print_status(message: str, style: Optional[str] = None):
def print_debug(message: str):
def print_phase(phase_name: str):
def print_warning(message: str):
def print_error(message: str):
def print_success(message: str):
def print_file_processing(message: str):
END_FILE: blobify\console.py


START_FILE: blobify\content_processor.py
FILE_CONTENT:
import csv
import datetime
import io
import mimetypes
from pathlib import Path
from typing import Tuple
import scrubadub
def scrub_content(content: str, enabled: bool = True, debug: bool = False) -> Tuple[str, int]:
        return content, 0
    try:
        # Disable the twitter detector which has too many false positives
        # Get filth items for counting and debug output
        return cleaned_content, len(filth_items)
    except Exception as e:
        # If scrubbing fails, return original content and warn
        return content, 0
def parse_named_filters(filter_args: list) -> tuple:
        # Handle specific malformed cases from tests
        try:
            # Use CSV parser to handle quoted, comma-separated values
                # Don't modify the pattern - CSV parser already handles escaped quotes correctly
        except (csv.Error, StopIteration, IndexError) as e:
    return filters, filter_names
def filter_content_lines(content: str, filters: dict, file_path: Path = None, debug: bool = False) -> str:
        return content
    import re
    # Get applicable filters for this file
            # Convert Path to string for pattern matching, always use forward slashes
            # Use comprehensive pattern matching
        # If no file path provided, extract just the regex patterns
            try:
            except re.error as e:
    return "\n".join(filtered_lines)
def _matches_glob_pattern(file_path: str, file_name: str, pattern: str) -> bool:
    import fnmatch
    import os
    # Handle simple cases first
        return True
    # Try filename match first (most common case)
        return True
    # For cross-platform compatibility, we need to test multiple variations
    # of the path and pattern to handle different path separator conventions
    # Convert path separators to forward slashes for consistent comparison
    # Try full path match with forward slashes (works well cross-platform)
        return True
    # Also try with native path separators
        return True
    # Handle ** patterns - these need special treatment
        # **/*.ext should match any .ext file at any level including root
                return True
        # dir/** should match anything in or under dir/
                return True
        # Try pathlib for complex ** patterns
        try:
            from pathlib import PurePath
                return True
        except (ValueError, TypeError):
    # Handle directory patterns like "migrations/*.sql"
        # For simple dir/file patterns
            # Check if file is in a directory matching the pattern
                # Check if the directory part matches and the file part matches
                    return True
                # Also check if any parent directory matches the pattern
                        return True
    return False
def is_text_file(file_path: Path) -> bool:
    # Known text file extensions
    # Security-sensitive file extensions to exclude
        # Certificates
        # Keys
        # Certificate signing requests
        # Other security files
    # First check extension
        return False
        return False
    # Then check mimetype
        return False
    # Finally, check content
    try:
            # Read first 8KB for analysis
            # Check for common binary file signatures
                return False
                return False
                return False
                return False
            # Check for high concentration of null bytes or non-ASCII characters
                return False
            # Try decoding as UTF-8
            try:
                return True
            except UnicodeDecodeError:
                return False
    except OSError:
        return False
def get_file_metadata(file_path: Path) -> dict:
    return {
END_FILE: blobify\content_processor.py


START_FILE: blobify\file_scanner.py
FILE_CONTENT:
import fnmatch
import os
from pathlib import Path
from typing import Dict, Optional
def matches_pattern(file_path: Path, base_path: Path, pattern: str) -> bool:
    try:
        # Get path relative to base path
        # Try exact match first
            return True
        # Try glob pattern matching
            return True
        # Try matching just the filename
            return True
        # Try matching directory patterns
            # Directory pattern - check if file is in this directory
                    return True
        return False
    except ValueError:
        # File not within base path
        return False
def get_built_in_ignored_patterns() -> set:
    return {
        # Dot folders
        # Package manager directories
        # Build directories
        # Others
        # Security and certificate directories
def check_if_dot_item_might_be_included(item_name: str, git_root: Path, context: Optional[str] = None) -> bool:
        return False
    try:
            return False
        # Check if any include pattern might match this item
            # Direct match
                return True
            # Wildcard patterns that might match
                return True
            # Patterns that might match files within this directory (if it's a directory)
                return True
            # Patterns like .github/** that would include everything in .github
                return True
        return False
    except Exception:
        # If we can't read .blobify, err on the side of caution and don't allow
        return False
def discover_files(directory: Path, debug: bool = False) -> Dict:
    # Check if we're in a git repository
        # Skip directories based on built-in patterns
            # Check built-in patterns
            # Check if directory starts with . but allow if .blobify might include files from it
            # Check if directory is gitignored
                try:
                        # Add directory to gitignored list but don't walk into it
                except Exception:
        # Collect all text files that pass sweep 1
                # Skip files with built-in ignored names
                # Skip dot files unless .blobify might include them
                # Check gitignore if we're in a git repo
                    try:
                    except Exception:
                # Add all files to the list (including gitignored ones for the index)
    return {
def apply_blobify_patterns(discovery_context: Dict, directory: Path, context: Optional[str] = None, debug: bool = False) -> None:
    # Load .blobify configuration
    # Find ALL files again (including gitignored ones and dot files) for pattern matching
        # Only skip built-in patterns, not gitignore or dot directories
            # Include all files including dot files for pattern matching
    # Get original pattern order from file
        try:
                    # Check for context headers
                    # Only process lines in target context
        except OSError:
    # If we couldn't read the original order, fall back to exclude-then-include
    # Apply patterns in original file order
                    # Check if this is an exact file match by seeing if the pattern
                    # directly matches the file path without wildcards doing the work
                    # A pattern is considered "exact" if it contains no wildcards
                    # AND it matches the file path exactly
                    # For non-exact matches, still check if it's a text file
                    # But for exact matches, bypass the text file check (security override)
                    # Check if this file is already in our all_files list
                            # File exists, if it was gitignored or excluded, include it
                    # If not in list at all, add it (but check files_to_add for duplicates)
                        # Check if already in files_to_add
                    # Mark as excluded in all_files if present
                    # Remove from files_to_add if present
    # Add new files to the main list
def scan_files(directory: Path, context: Optional[str] = None, debug: bool = False) -> Dict:
    # First sweep: gitignore and built-in exclusions
    # Second sweep: apply .blobify patterns
    # Count final results - filter files properly by context patterns
    # Apply context filtering to determine final included files
    # Both context and default should use the same logic
    return discovery_context
END_FILE: blobify\file_scanner.py


START_FILE: blobify\git_utils.py
FILE_CONTENT:
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
def is_git_repository(path: Path) -> Optional[Path]:
            return current
    return None
def get_gitignore_patterns(git_root: Path, debug: bool = False) -> Dict[Path, List[str]]:
    # Get global gitignore
    try:
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
    # Add global patterns to git root
    # Get repository-level .gitignore
    # Compile patterns for the root directory so we can check if subdirectories are ignored
    # Get all .gitignore files in subdirectories, but only if their containing directory is not ignored
        # Check if this directory (or any of its parents) is ignored
        # This .gitignore is in a non-ignored directory, so include its patterns
    return patterns_by_dir
    # Get relative path from git root
    try:
    except ValueError:
        return False
    # Check each parent directory for gitignore patterns that might apply
        # Check if current_dir has gitignore patterns
            # Construct the path relative to the current gitignore's directory
                # We're checking from the git root
                # We're checking from a subdirectory
                return True
        # Move to the next directory level
    return False
def is_path_ignored_by_patterns(path_str: str, compiled_patterns: List[Tuple[re.Pattern, bool]], debug: bool = False) -> bool:
    return is_ignored
def read_gitignore_file(gitignore_path: Path) -> List[str]:
    try:
                # Skip empty lines and comments
    except OSError:
    return patterns
def compile_gitignore_patterns(patterns: List[str]) -> List[Tuple[re.Pattern, bool]]:
        # Convert gitignore pattern to regex
        try:
        except re.error:
            # Skip invalid regex patterns
    return compiled_patterns
def gitignore_to_regex(pattern: str) -> str:
    # Handle directory-only patterns (ending with /)
    # Handle patterns that start with / (root-relative)
    # Escape special regex characters except for *, ?, [, ], and /
    # Unescape the characters we want to handle specially
    # Handle gitignore-specific patterns
    # First handle ** (must be done before single *)
    # * matches anything except /
    # Replace placeholder with proper regex for **
    # ? matches any single character except /
    # Build the final pattern
        # For directory patterns like "*.egg-info/" or "build/":
        # Match the directory name itself AND anything inside it
            # Root-relative directory pattern like "/build/"
            # Non-root-relative directory pattern like "*.egg-info/" or "node_modules/"
            # This should match:
            # 1. The directory at root: "some.egg-info"
            # 2. Contents of directory at root: "some.egg-info/file.txt"
            # 3. The directory in subdirs: "path/some.egg-info"
            # 4. Contents in subdirs: "path/some.egg-info/file.txt"
        # Regular file patterns
    return final_pattern
    # Get relative path from git root
    try:
    except ValueError:
        return False
    # Check each gitignore file's patterns
    # We need to check patterns from git root and all parent directories
    # Start from the git root and work our way down
        # Calculate the path relative to this gitignore's directory
        try:
                # This gitignore is in a subdirectory
                    # File is in or under this gitignore's directory
                    # File is not under this gitignore's influence
        except ValueError:
        # Compile and test patterns
    return is_ignored
END_FILE: blobify\git_utils.py


START_FILE: blobify\main.py
FILE_CONTENT:
#!/usr/bin/env python3
import argparse
import io
import os
import subprocess
import sys
import tempfile
from pathlib import Path
def validate_boolean(value):
        return value
        return True
        return False
        raise argparse.ArgumentTypeError(f"Invalid boolean value: '{value}'. Use 'true' or 'false'.")
def validate_list_patterns(value):
        raise argparse.ArgumentTypeError(
    return value
def _should_modify_stdout():
        return False
    # Check if running under pytest
        return False
    # Check if stdout is a real terminal
        return False
    # Check if stdout has a buffer attribute (real file-like object)
        return False
    return True
def list_ignored_patterns():
    # Group patterns by type for better readability
def show_version():
def main():
    # Fix Windows Unicode output by replacing stdout with UTF-8 wrapper
    # Only do this when running in a real terminal, not under pytest or when redirected
    try:
        # Handle version flag first
        # Handle --list-patterns option
            # Handle case where --list-patterns=contexts was provided
                # Try to use current directory if .blobify exists
        # Handle --context without value (list contexts)
            # Handle case where --context was provided without a value
                # Try to use current directory if .blobify exists
        # Handle default directory logic
        # Check if we're in a git repository and apply default switches from .blobify
        # Parse named filters
        # Check scrubbing configuration
        # Scan files
        # Get blobify pattern info for header generation
        # Format output
        # Show final summary
            # Show helpful hint in CLI when there's essentially no output
        # Remove BOM if present
        # Handle output
            try:
                    # Write file with UTF-16 encoding (required for clip.exe Unicode support)
                    # Use type command to read file and pipe to clip
                    # Clean up
            except Exception as e:
                return  # Don't output to stdout if clipboard was requested
    except Exception as e:
    finally:
        # Restore original stdout if we modified it
END_FILE: blobify\main.py


START_FILE: blobify\output_formatter.py
FILE_CONTENT:
import datetime
from pathlib import Path
from typing import Dict, List
    # Keep headers minimal - no verbose metadata
    # Add filter information
    # Adjust format description based on options
        # Metadata only
# Format:
# 1. Metadata sections for each file (size, timestamps)
# 2. Each file section is marked with START_FILE and END_FILE delimiters"""
        # Index only
        # Index + metadata
# Format:
# 1. File listing with relative paths
# 2. Metadata sections for each file (size, timestamps)
# 3. Each file section is marked with START_FILE and END_FILE delimiters"""
        # Content only
# Format:
# 1. Content sections for each file
# 2. Each file section is marked with START_FILE and END_FILE delimiters
#
# Files ignored by .gitignore or excluded by .blobify have their content excluded
# with a placeholder message."""
        # Index + content
# Format:
# 1. File listing with relative paths
# 2. Content sections for each file
# 3. Each file section is marked with START_FILE and END_FILE delimiters
#
# Files ignored by .gitignore are listed in the index but marked as [IGNORED BY GITIGNORE]
# Files excluded by .blobify are listed in the index but marked as [EXCLUDED BY .blobify]
# and their content is excluded with a placeholder message."""
        # Content + metadata
# Format:
# 1. Content sections for each file, including metadata and full content
# 2. Each file section is marked with START_FILE and END_FILE delimiters
#
# Files ignored by .gitignore or excluded by .blobify have their content excluded
# with a placeholder message."""
        # Index + content + metadata (default)
# Format:
# 1. File listing with relative paths
# 2. Content sections for each file, including metadata and full content
# 3. Each file section is marked with START_FILE and END_FILE delimiters
#
# Files ignored by .gitignore are listed in the index but marked as [IGNORED BY GITIGNORE]
# Files excluded by .blobify are listed in the index but marked as [EXCLUDED BY .blobify]
# and their content is excluded with a placeholder message."""
    # Build the header intro
# Source Directory: {directory}{git_info}{blobify_info}{scrubbing_info}{filter_info}
# Generated: {datetime}
# Source Directory: {directory}{git_info}{blobify_info}{scrubbing_info}{filter_info}
    # Add description to header
#
# This format is designed to be both human-readable and machine-parseable.
# Files are ordered alphabetically by relative path.
#
    return header
    # When content is disabled, don't show status labels since they refer to content inclusion
        # Add gitignored directories to the index with status labels
        # Build index for files with status labels
            # Priority order: git ignored > blobify excluded > filter excluded > blobify included > normal
        # When content is disabled, just show clean file listings without status labels
        # Include all discovered files regardless of git/blobify status
        # Add directories (without status labels)
        # Add files (without status labels)
        # Sort all paths together for a clean listing
    # Build index section
    # Add appropriate section header based on what content will follow
    return index_section
    # If both content and metadata are disabled, return empty string immediately
        return "", 0
        # Skip excluded files entirely if suppress_excluded is enabled
        # Always include the START_FILE marker when metadata or content is enabled
        # Include metadata section if enabled
            try:
                # Only include status when content is also being included
            except OSError as e:
                # If we can't get metadata, add an error message
        # Include content section if enabled
                try:
                    # Attempt to scrub content if enabled
                    # Apply content filters if specified
                    # Add line numbers if enabled AND include_line_numbers is True
                except Exception as e:
    return "\n".join(content), total_substitutions
    # Sort all files for consistent output
    # Pre-process filters to determine which files are excluded by filters
    # This needs to happen before index generation so the status labels are correct
            # Skip files already excluded by git or blobify
            try:
                # Apply filters to check if content would be excluded
                # Mark as filter-excluded if no content remains
            except Exception:
                # If we can't read the file, don't mark it as filter-excluded
    # Generate header
    # Generate index section (if enabled)
        # No index - add appropriate header based on what we're including
    # Generate content section (only if content or metadata is enabled)
        # Add debug output to see if this branch is being taken
    # Combine all sections
    return result, total_substitutions, len(included_files)
END_FILE: blobify\output_formatter.py
