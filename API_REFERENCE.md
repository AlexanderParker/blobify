# Blobify Text File Index
# Generated: 2025-08-09T12:17:46.002411
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
            return config["include_patterns"], config["exclude_patterns"], config["default_switches"]
            return [], [], []
    except OSError as e:
        return [], [], []
def _parse_contexts_with_inheritance(blobify_file: Path, debug: bool = False) -> Dict[str, Dict]:
                    raise ValueError(f"Line {line_num}: Cannot redefine 'default' context")
                    raise ValueError(f"Line {line_num}: Context '{context_name}' already defined")
                        raise ValueError(f"Line {line_num}: Parent context(s) not found: {missing_str}")
    return contexts
def get_available_contexts(git_root: Path, debug: bool = False) -> List[str]:
        return contexts
    try:
    except OSError as e:
    return contexts
def get_context_descriptions(git_root: Path) -> Dict[str, str]:
        return descriptions
    try:
    except OSError:
    return descriptions
def list_available_contexts(directory: Path):
def _get_context_inheritance_info(git_root: Path) -> Dict[str, str]:
        return inheritance_info
    try:
    except OSError:
    return inheritance_info
def apply_default_switches(args: argparse.Namespace, default_switches: List[str], debug: bool = False) -> argparse.Namespace:
        return args
            try:
            except (csv.Error, StopIteration):
                try:
                except ValueError as e:
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
        return cleaned_content, len(filth_items)
    except Exception as e:
        return content, 0
def parse_named_filters(filter_args: list) -> tuple:
        try:
        except (csv.Error, StopIteration, IndexError) as e:
    return filters, filter_names
def filter_content_lines(content: str, filters: dict, file_path: Path = None, debug: bool = False) -> str:
        return content
    import re
            try:
            except re.error as e:
    return "\n".join(filtered_lines)
def _matches_glob_pattern(file_path: str, file_name: str, pattern: str) -> bool:
    import fnmatch
    import os
        return True
        return True
        return True
        return True
                return True
                return True
        try:
            from pathlib import PurePath
                return True
        except (ValueError, TypeError):
                    return True
                        return True
    return False
def is_text_file(file_path: Path) -> bool:
        return False
        return False
        return False
    try:
                return False
                return False
                return False
                return False
                return False
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
            return True
            return True
            return True
                    return True
        return False
    except ValueError:
        return False
def get_built_in_ignored_patterns() -> set:
    return {
def check_if_dot_item_might_be_included(item_name: str, git_root: Path, context: Optional[str] = None) -> bool:
        return False
    try:
            return False
                return True
                return True
                return True
                return True
        return False
    except Exception:
        return False
def discover_files(directory: Path, debug: bool = False) -> Dict:
                try:
                except Exception:
                    try:
                    except Exception:
    return {
def apply_blobify_patterns(discovery_context: Dict, directory: Path, context: Optional[str] = None, debug: bool = False) -> None:
        try:
        except OSError:
def scan_files(directory: Path, context: Optional[str] = None, debug: bool = False) -> Dict:
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
    try:
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
    return patterns_by_dir
    try:
    except ValueError:
        return False
                return True
    return False
def is_path_ignored_by_patterns(path_str: str, compiled_patterns: List[Tuple[re.Pattern, bool]], debug: bool = False) -> bool:
    return is_ignored
def read_gitignore_file(gitignore_path: Path) -> List[str]:
    try:
    except OSError:
    return patterns
def compile_gitignore_patterns(patterns: List[str]) -> List[Tuple[re.Pattern, bool]]:
        try:
        except re.error:
    return compiled_patterns
def gitignore_to_regex(pattern: str) -> str:
    return final_pattern
    try:
    except ValueError:
        return False
        try:
        except ValueError:
    return is_ignored
END_FILE: blobify\git_utils.py


START_FILE: blobify\main.py
FILE_CONTENT:
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
        raise argparse.ArgumentTypeError(f"Invalid list-patterns value: '{value}'. Use one of: {', '.join(allowed_values)}")
    return value
def _should_modify_stdout():
        return False
        return False
        return False
        return False
    return True
def list_ignored_patterns():
def show_version():
def main():
    try:
            try:
            except Exception as e:
                return  # Don't output to stdout if clipboard was requested
    except Exception as e:
    finally:
END_FILE: blobify\main.py


START_FILE: blobify\output_formatter.py
FILE_CONTENT:
import datetime
from pathlib import Path
from typing import Dict, List
    return header
    return index_section
        return "", 0
            try:
            except OSError as e:
                try:
                except Exception as e:
    return "\n".join(content), total_substitutions
            try:
            except Exception:
    return result, total_substitutions, len(included_files)
END_FILE: blobify\output_formatter.py
