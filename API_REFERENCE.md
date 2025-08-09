# Blobify Text File Index
# Generated: 2025-08-09T12:10:35.743604
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


START_FILE: tasks.py
FILE_CONTENT:
import shutil
from pathlib import Path
from invoke import task
@task
def test_to_clip(c):
    import subprocess
    import sys
@task
def install_dev(c):
def run_with_formatting(cmd, capture_output=False, env=None):
    import os
    import shutil
    import subprocess
    import sys
    try:
            return result.returncode
            return result.returncode
    except subprocess.CalledProcessError as e:
        return e.returncode
@task
def test(c):
    import sys
@task
def test_verbose(c):
    import sys
@task
def test_xunit(c):
    import sys
@task
def coverage(c):
    import sys
@task
def lint(c):
    import os
@task
def format(c):
    import os
    import sys
@task
def clean(c):
@task
def clean_dist(c):
@task
def build(c):
    import sys
@task
def publish_test(c):
    import sys
@task
def publish(c):
    import sys
@task
def test_install(c):
    import sys
@task
def get_version(c):
    import tomllib
    return version
@task
def tag_release(c):
    import sys
@task
def bump_patch(c):
@task
def bump_minor(c):
@task
def bump_major(c):
def _bump_version(c, bump_type):
    import re
    import tomllib
    import tomli_w
@task
def set_version(c, version):
    import re
    import tomllib
    import tomli_w
@task
def api_reference(c):
    import sys
@task
def all(c):
END_FILE: tasks.py


START_FILE: test_runner.py
FILE_CONTENT:
import argparse
import sys
import unittest
from pathlib import Path
from typing import Optional
        try:
            import xmlrunner
        except ImportError:
    return result.wasSuccessful()
def main():
END_FILE: test_runner.py


START_FILE: tests\conftest.py
FILE_CONTENT:
import sys
from pathlib import Path
import pytest
@pytest.fixture
def sample_files(tmp_path):
    return files
@pytest.fixture
def mock_git_repo(tmp_path):
    return {"git_root": tmp_path, "git_dir": git_dir, "gitignore": gitignore}
END_FILE: tests\conftest.py


START_FILE: tests\test_config.py
FILE_CONTENT:
import argparse
import tempfile
from pathlib import Path
from unittest.mock import patch
import pytest
from blobify.config import apply_default_switches, read_blobify_config
class TestBlobifyConfig:
    @pytest.fixture
    def temp_dir(self):
        yield temp_dir
    @pytest.fixture
    def blobify_file(self, temp_dir):
        return temp_dir / ".blobify"
    def test_read_blobify_config_no_file(self, temp_dir):
    def test_read_blobify_config_basic_patterns(self, blobify_file):
@debug=true
@output-filename=test.txt
    def test_read_blobify_config_legacy_boolean_switches(self, blobify_file):
@debug
@copy-to-clipboard
    def test_read_blobify_config_with_context(self, blobify_file):
@copy-to-clipboard=true
    def test_read_blobify_config_last_value_wins(self, blobify_file):
@debug=false
@copy-to-clipboard=false
@debug=true
@copy-to-clipboard=true
    def test_read_blobify_config_csv_filters(self, blobify_file):
@filter="functions","^def","*.py"
@filter="imports","^import"
    def test_read_blobify_config_invalid_patterns(self, blobify_file):
    def test_read_blobify_config_file_read_error(self, temp_dir):
    def test_apply_default_switches_no_switches(self):
    def test_apply_default_switches_boolean_switches(self):
    def test_apply_default_switches_key_value_switches(self):
    def test_apply_default_switches_precedence(self):
    def test_apply_default_switches_unknown_switches(self):
    def test_apply_default_switches_dash_underscore_conversion(self):
    def test_apply_default_switches_filter_handling_csv(self):
    def test_apply_default_switches_filter_handling_legacy(self):
    def test_apply_default_switches_list_patterns(self):
    def test_apply_default_switches_invalid_boolean_value(self):
    def test_apply_default_switches_invalid_list_patterns_value(self):
END_FILE: tests\test_config.py


START_FILE: tests\test_console.py
FILE_CONTENT:
import sys
from io import StringIO
from unittest.mock import patch
from blobify.console import (
class TestConsoleOutput:
    def test_print_status_without_style(self, capsys):
    def test_print_status_with_style(self, capsys):
    def test_print_debug_output(self, capsys):
    def test_print_phase_output(self, capsys):
    def test_print_warning_output(self, capsys):
    def test_print_error_output(self, capsys):
    def test_print_success_output(self, capsys):
    def test_print_file_processing_output(self, capsys):
    def test_console_output_goes_to_stderr(self, capsys):
    def test_console_functions_with_no_rich(self, capsys):
    def test_console_functions_preserve_message_content(self, capsys):
    def test_stderr_redirection_compatibility(self):
        try:
        finally:
END_FILE: tests\test_console.py


START_FILE: tests\test_content_processor.py
FILE_CONTENT:
from pathlib import Path
from blobify.content_processor import (
class TestContentProcessor:
    def test_scrub_content_disabled(self):
    def test_scrub_content_with_email(self):
    def test_scrub_content_with_phone_number(self):
    def test_scrub_content_with_social_security_number(self):
    def test_scrub_content_with_multiple_sensitive_items(self):
    def test_scrub_content_with_no_sensitive_data(self):
    def test_scrub_content_debug_output(self, capsys):
    def test_scrub_content_with_twitter_detector_disabled(self):
    def test_scrub_content_exception_handling(self):
    def test_is_text_file_python(self, tmp_path):
    def test_is_text_file_text(self, tmp_path):
    def test_is_text_file_security_extension(self, tmp_path):
    def test_is_text_file_unknown_extension(self, tmp_path):
    def test_is_text_file_binary_content(self, tmp_path):
    def test_is_text_file_high_null_bytes(self, tmp_path):
    def test_is_text_file_unicode_decode_error(self, tmp_path):
    def test_is_text_file_io_error(self, tmp_path):
    def test_get_file_metadata(self, tmp_path):
            import datetime
    def test_scrub_content_real_world_patterns(self):
    def test_parse_named_filters_csv_format(self):
    def test_parse_named_filters_csv_with_commas_in_regex(self):
    def test_parse_named_filters_csv_two_values(self):
    def test_parse_named_filters_csv_single_value(self):
    def test_parse_named_filters_csv_quotes_in_regex(self):
    def test_parse_named_filters_csv_malformed(self):
    def test_parse_named_filters_empty(self):
    def test_parse_named_filters_none(self):
    def test_filter_content_lines_file_targeting_debug(self):
    def test_filter_content_lines_complex_file_patterns(self):
    def test_filter_content_lines_nested_directory_patterns(self):
    def test_filter_content_lines_edge_cases(self):
    def test_filter_content_lines_glob_pattern_matching(self):
END_FILE: tests\test_content_processor.py


START_FILE: tests\test_context_inheritance.py
FILE_CONTENT:
from unittest.mock import patch
import pytest
from blobify.config import get_available_contexts, list_available_contexts, read_blobify_config
from blobify.main import main
class TestContextInheritance:
    def test_default_context_behavior(self, tmp_path):
@copy-to-clipboard=true
    def test_single_level_inheritance(self, tmp_path):
@copy-to-clipboard=true
    def test_multi_level_inheritance(self, tmp_path):
@copy-to-clipboard=true
@debug=true
@output-metadata=false
    def test_context_without_inheritance(self, tmp_path):
@copy-to-clipboard=true
@debug=true
    def test_missing_parent_context(self, tmp_path):
@debug=true
    def test_inheritance_preserves_pattern_order(self, tmp_path):
@copy-to-clipboard=true
@debug=true
    def test_context_inheritance_with_blobify_patterns_file_order(self, tmp_path):
    def test_get_available_contexts_with_inheritance(self, tmp_path):
    def test_list_available_contexts_shows_inheritance(self, tmp_path, capsys):
    def test_context_inheritance_help_text(self, tmp_path, capsys):
    def test_context_inheritance_with_filter_defaults(self, tmp_path):
@filter="functions","^def"
@filter="classes","^class"
    def test_nonexistent_context_inheritance(self, tmp_path, capsys):
    def test_nonexistent_context_exits_with_error(self, tmp_path, capsys):
    def test_nonexistent_context_no_available_contexts(self, tmp_path, capsys):
    def test_default_context_behavior_unchanged(self, tmp_path):
    def test_empty_inheritance_syntax(self, tmp_path):
    def test_context_inheritance_integration_example(self, tmp_path):
@copy-to-clipboard=true
    def test_inheritance_with_complex_patterns(self, tmp_path):
@show-excluded=false
    def test_contexts_processed_in_file_order(self, tmp_path):
@copy-to-clipboard=true
    def test_cannot_redefine_default_context(self, tmp_path):
@copy-to-clipboard=true
    def test_cannot_inherit_from_nonexistent_context(self, tmp_path):
    def test_cannot_inherit_from_context_defined_later(self, tmp_path):
    def test_cannot_define_context_twice(self, tmp_path):
    def test_multiple_inheritance_basic(self, tmp_path):
@copy-to-clipboard=true
@debug=true
    def test_multiple_inheritance_complex(self, tmp_path):
@copy-to-clipboard=true
@output-metadata=false
@debug=true
@show-excluded=false
    def test_multiple_inheritance_with_duplicates(self, tmp_path):
@copy-to-clipboard=true
@copy-to-clipboard=true
    def test_multiple_inheritance_missing_one_parent(self, tmp_path):
    def test_multiple_inheritance_missing_multiple_parents(self, tmp_path):
    def test_multiple_inheritance_order_preserved(self, tmp_path):
@first-switch=true
@second-switch=true
@third-switch=true
@combined-switch=true
    def test_multiple_inheritance_display_in_list(self, tmp_path, capsys):
    def test_multiple_inheritance_help_text(self, tmp_path, capsys):
    def test_edge_case_empty_parent_list(self, tmp_path):
    def test_multiple_inheritance_integration_with_blobify(self, tmp_path):
@show-excluded=false
END_FILE: tests\test_context_inheritance.py


START_FILE: tests\test_context_listing.py
FILE_CONTENT:
from unittest.mock import patch
import pytest
from blobify.config import get_available_contexts, get_context_descriptions, list_available_contexts
from blobify.main import main
class TestContextListing:
    def test_get_available_contexts_basic(self, tmp_path):
@filter="sigs","^def"
    def test_get_available_contexts_no_file(self, tmp_path):
    def test_get_available_contexts_no_contexts(self, tmp_path):
@debug=true
    def test_get_available_contexts_duplicate_contexts(self, tmp_path):
    def test_get_context_descriptions(self, tmp_path):
@filter="sigs","^def"
    def test_get_context_descriptions_empty_comments(self, tmp_path):
    def test_get_context_descriptions_comments_cleared_by_patterns(self, tmp_path):
    def test_list_available_contexts_with_contexts(self, tmp_path, capsys):
@filter="sigs","^(def|class)"
    def test_list_available_contexts_no_contexts(self, tmp_path, capsys):
    def test_list_available_contexts_no_git_repo(self, tmp_path, capsys):
    def test_list_available_contexts_no_blobify_file(self, tmp_path, capsys):
    def test_context_flag_without_value_lists_contexts(self, tmp_path, capsys):
    def test_context_flag_without_value_current_directory(self, tmp_path, monkeypatch, capsys):
    def test_context_flag_without_value_no_blobify_current_dir(self, tmp_path, monkeypatch, capsys):
    def test_long_context_flag_without_value(self, tmp_path, capsys):
    def test_context_sorting_in_output(self, tmp_path, capsys):
    def test_context_flag_with_specific_context_still_works(self, tmp_path):
@debug=true
    def test_context_flag_nonexistent_directory_error(self, capsys):
    def test_context_descriptions_with_special_characters(self, tmp_path, capsys):
    def test_context_debug_output(self, tmp_path, capsys):
END_FILE: tests\test_context_listing.py


START_FILE: tests\test_dot_file_inclusion.py
FILE_CONTENT:
from pathlib import Path
from blobify.file_scanner import (
class TestDotFileInclusion:
    def test_check_if_dot_item_might_be_included_exact_match(self, tmp_path):
    def test_check_if_dot_item_might_be_included_directory_patterns(self, tmp_path):
    def test_check_if_dot_item_might_be_included_wildcard_patterns(self, tmp_path):
    def test_check_if_dot_item_might_be_included_no_blobify_file(self, tmp_path):
    def test_check_if_dot_item_might_be_included_with_context(self, tmp_path):
    def test_dot_file_inclusion_in_discover_files(self, tmp_path):
    def test_github_workflow_inclusion_full_scan(self, tmp_path):
    def test_cross_platform_path_handling(self, tmp_path):
    def test_dot_directory_exclusion_without_patterns(self, tmp_path):
    def test_built_in_ignored_patterns_still_work(self, tmp_path):
END_FILE: tests\test_dot_file_inclusion.py


START_FILE: tests\test_file_scanner.py
FILE_CONTENT:
import tempfile
from pathlib import Path
from unittest.mock import patch
from blobify.file_scanner import (
class TestFileScanner:
    def test_matches_pattern_exact(self, tmp_path):
    def test_matches_pattern_glob(self, tmp_path):
    def test_matches_pattern_directory(self, tmp_path):
    def test_matches_pattern_no_match(self, tmp_path):
    def test_matches_pattern_outside_base(self):
        try:
        finally:
    def test_get_built_in_ignored_patterns(self):
    @patch("blobify.file_scanner.is_git_repository")
    @patch("blobify.file_scanner.get_gitignore_patterns")
    def test_discover_files_no_git(self, mock_get_patterns, mock_is_git, tmp_path):
    @patch("blobify.file_scanner.is_git_repository")
    @patch("blobify.file_scanner.get_gitignore_patterns")
    @patch("blobify.file_scanner.is_ignored_by_git")
    def test_discover_files_with_git(self, mock_is_ignored, mock_get_patterns, mock_is_git, tmp_path):
    def test_apply_blobify_patterns_no_git(self, tmp_path):
    @patch("blobify.file_scanner.read_blobify_config")
    def test_apply_blobify_patterns_with_config(self, mock_read_config, tmp_path):
    @patch("blobify.file_scanner.discover_files")
    @patch("blobify.file_scanner.apply_blobify_patterns")
    def test_scan_files(self, mock_apply_patterns, mock_discover, tmp_path):
END_FILE: tests\test_file_scanner.py


START_FILE: tests\test_filter_file_targeting.py
FILE_CONTENT:
from pathlib import Path
from unittest.mock import patch
import pytest
from blobify.content_processor import filter_content_lines, parse_named_filters
from blobify.main import main
class TestFileTargetedFilters:
    def test_parse_named_filters_with_file_patterns(self):
    def test_parse_named_filters_mixed_with_and_without_file_patterns(self):
    def test_parse_named_filters_fallback_with_colons_in_regex(self):
    def test_filter_content_lines_with_file_pattern_match(self):
    def test_filter_content_lines_with_file_pattern_no_match(self):
    def test_filter_content_lines_multiple_filters_different_files(self):
    def test_filter_content_lines_wildcard_file_pattern(self):
    def test_filter_content_lines_complex_file_patterns(self):
    def test_filter_content_lines_no_file_path_applies_all(self):
class TestFileTargetedFiltersIntegration:
    def setup_multi_language_project(self, tmp_path):
    return True
class Application:
    def __init__(self):
import os
import sys
    def __init__(self, name):
def create_user(name):
    return User(name)
    return true;
        return tmp_path
    def setup_multi_language_project_with_sql(self, tmp_path):
        from blobify.content_processor import is_text_file
        return tmp_path
    def test_python_specific_filters(self, tmp_path):
    def test_javascript_specific_filters(self, tmp_path):
    def test_css_selector_filters(self, tmp_path):
    def test_migration_sql_filters(self, tmp_path):
    def test_cross_language_analysis(self, tmp_path):
    def test_file_pattern_with_directory_paths(self, tmp_path):
        from blobify.content_processor import is_text_file
    def test_filter_exclusion_by_file_pattern(self, tmp_path):
    def test_blobify_config_with_file_targeted_filters(self, tmp_path):
@filter="py-functions","^def","*.py"
@filter="js-functions","^function","*.js"
@filter="css-selectors","^[.#]","*.css"
    def test_command_line_override_with_file_patterns(self, tmp_path):
@filter="functions","^(def|function)"
END_FILE: tests\test_filter_file_targeting.py


START_FILE: tests\test_filter_functionality.py
FILE_CONTENT:
from pathlib import Path
from unittest.mock import patch
import pytest
from blobify.content_processor import filter_content_lines, parse_named_filters
from blobify.main import main
class TestFilterParsing:
    def test_parse_named_filters_csv_format(self):
    def test_parse_named_filters_with_file_patterns(self):
    def test_parse_named_filters_with_colon_in_regex(self):
    def test_parse_named_filters_with_commas_in_regex(self):
    def test_parse_named_filters_fallback_single_value(self):
    def test_parse_named_filters_mixed(self):
    def test_parse_named_filters_empty(self):
    def test_parse_named_filters_none(self):
    def test_parse_named_filters_malformed_csv(self):
class TestFilterContentLines:
    def test_filter_content_lines_single_match(self):
    def test_filter_content_lines_with_file_path_matching(self):
    def test_filter_content_lines_with_file_path_not_matching(self):
    def test_filter_content_lines_multiple_matches(self):
    def test_filter_content_lines_no_matches(self):
    def test_filter_content_lines_or_logic(self):
    def test_filter_content_lines_regex_patterns(self):
    def test_filter_content_lines_invalid_regex(self):
    def test_filter_content_lines_empty_filters(self):
    def test_filter_content_lines_case_sensitive(self):
    def test_filter_content_lines_file_pattern_with_directory(self):
class TestFilterIntegration:
    def setup_test_files(self, tmp_path):
    return True
class MyClass:
    def method(self):
        return False
import os
import sys
    return "world";
        return {"py_file": py_file, "js_file": js_file, "config_file": config_file}
    def test_filter_basic_function_extraction(self, tmp_path):
    def test_filter_file_targeted_extraction(self, tmp_path):
    def test_filter_multiple_patterns(self, tmp_path):
    def test_filter_with_suppress_excluded(self, tmp_path):
    def test_filter_with_no_content_flag(self, tmp_path):
    def test_filter_cli_summary_message(self, tmp_path, capsys):
    def test_filter_context_interaction(self, tmp_path):
@filter="functions","^(def|function)"
    def test_filter_empty_file_handling(self, tmp_path):
    def test_filter_line_numbers_interaction(self, tmp_path):
    def test_filter_with_scrubbing_interaction(self, tmp_path):
class TestFilterErrorHandling:
    def test_filter_invalid_regex_graceful_handling(self, tmp_path, capsys):
class TestFilterBlobifyIntegration:
    def test_filter_default_switch_in_blobify(self, tmp_path):
@filter="functions","^def"
@filter="imports","^import"
    def test_filter_default_switch_with_file_patterns_in_blobify(self, tmp_path):
@filter="py-functions","^def","*.py"
@filter="js-functions","^function","*.js"
    def test_filter_command_line_override_blobify(self, tmp_path):
@filter="functions","^def"
    def test_filter_context_specific_defaults(self, tmp_path):
@filter="functions","^def"
@filter="signatures","^(def|class)"
@output-line-numbers=false
@filter="imports","^import","*.py"
@filter="js-funcs","^function","*.js"
END_FILE: tests\test_filter_functionality.py


START_FILE: tests\test_git_utils.py
FILE_CONTENT:
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from blobify.git_utils import (
class TestGitUtils:
    def test_is_git_repository_found(self, tmp_path):
    def test_is_git_repository_not_found(self, tmp_path):
    def test_is_git_repository_parent_directory(self, tmp_path):
    def test_read_gitignore_file(self, tmp_path):
    def test_read_gitignore_file_nonexistent(self, tmp_path):
    def test_gitignore_to_regex_simple(self):
    def test_gitignore_to_regex_directory(self):
    def test_gitignore_to_regex_root_relative(self):
    def test_gitignore_to_regex_doublestar(self):
    def test_compile_gitignore_patterns(self):
    def test_compile_gitignore_patterns_invalid_regex(self):
    @patch("blobify.git_utils.subprocess.run")
    def test_get_gitignore_patterns_with_global(self, mock_run, tmp_path):
    @patch("blobify.git_utils.subprocess.run")
    def test_get_gitignore_patterns_no_global(self, mock_run, tmp_path):
    def test_get_gitignore_patterns_git_error(self, tmp_path):
    def test_is_ignored_by_git_simple(self, tmp_path):
    def test_is_ignored_by_git_negation(self, tmp_path):
    def test_is_ignored_by_git_not_ignored(self, tmp_path):
    def test_is_ignored_by_git_file_outside_repo(self, tmp_path):
        try:
        finally:
END_FILE: tests\test_git_utils.py


START_FILE: tests\test_list_ignored.py
FILE_CONTENT:
from unittest.mock import patch
from blobify.main import list_ignored_patterns, main
class TestListIgnoredFeature:
    def test_list_ignored_patterns_option(self, capsys):
    def test_list_ignored_patterns_categories(self, capsys):
    def test_list_ignored_patterns_exits_early(self, tmp_path, capsys):
    def test_list_ignored_patterns_with_other_flags_ignored(self, capsys):
    def test_list_ignored_patterns_function_output(self, capsys):
    def test_list_ignored_patterns_function_sorted_output(self, capsys):
    def test_list_ignored_patterns_no_directory_needed(self, capsys):
    def test_list_ignored_patterns_comprehensive_coverage(self, capsys):
        from blobify.file_scanner import get_built_in_ignored_patterns
END_FILE: tests\test_list_ignored.py


START_FILE: tests\test_main.py
FILE_CONTENT:
import subprocess
from unittest.mock import Mock, patch
import pytest
from blobify.main import main
class TestMain:
    def test_main_processes_real_files(self, tmp_path):
    def test_main_with_output_file_simple(self, tmp_path):
    def test_main_gitignore_behavior(self, tmp_path):
    @patch("subprocess.run")
    def test_clipboard_integration_windows(self, mock_subprocess, tmp_path):
    @patch("subprocess.Popen")
    def test_clipboard_integration_macos(self, mock_popen, tmp_path):
    def test_error_handling_invalid_directory(self):
    def test_bom_removal_with_file_output(self, tmp_path):
        import sys
    def test_default_directory_with_blobify(self, tmp_path, monkeypatch):
    def test_default_directory_no_blobify_fails(self, tmp_path, monkeypatch):
    def test_blobify_config_integration(self, tmp_path):
    def test_context_option_integration(self, tmp_path):
class TestCliSummaryMessages:
    def setup_test_files(self, tmp_path):
        return tmp_path
    def test_cli_summary_all_combinations(self, tmp_path, capsys):
    def test_cli_warning_for_no_useful_output(self, tmp_path, capsys):
    def test_cli_context_in_summary(self, tmp_path, capsys):
    def test_cli_scrubbing_messages(self, tmp_path, capsys):
    def test_cli_debug_scrubbing_messages(self, tmp_path, capsys):
class TestCommandLineOptions:
    def test_line_numbers_option(self, tmp_path):
    def test_index_option(self, tmp_path):
    def test_content_option(self, tmp_path):
    def test_metadata_option(self, tmp_path):
    def test_debug_option_behavior(self, tmp_path, capsys):
    def test_enable_scrubbing_option_behavior(self, tmp_path):
    def test_filter_option_with_csv_format(self, tmp_path):
    def test_filter_option_with_file_pattern(self, tmp_path):
END_FILE: tests\test_main.py


START_FILE: tests\test_output_formatter.py
FILE_CONTENT:
from pathlib import Path
from unittest.mock import patch
from blobify.output_formatter import (
class TestGenerateIndex:
    def test_generate_index_with_content_shows_status_labels(self):
    def test_generate_index_without_content_clean_listing(self):
    def test_generate_index_empty_lists(self):
    def test_generate_index_sorting_behavior(self):
class TestGenerateContent:
    def test_generate_content_with_real_files_all_enabled(self, tmp_path):
    def test_generate_content_line_numbers_control(self, tmp_path):
    def test_generate_content_exclusion_scenarios(self, tmp_path):
    def test_generate_content_file_read_error_handling(self, tmp_path):
    def test_generate_content_both_sections_disabled(self, tmp_path):
    @patch("blobify.output_formatter.scrub_content")
    def test_generate_content_scrubbing_integration(self, mock_scrub, tmp_path):
    def test_generate_content_multiline_line_numbering(self, tmp_path):
    def test_generate_content_empty_file_list(self):
    def test_generate_content_suppress_excluded_basic(self, tmp_path):
END_FILE: tests\test_output_formatter.py


START_FILE: tests\test_suppress_excluded.py
FILE_CONTENT:
from unittest.mock import patch
import pytest
from blobify.main import main
class TestShowExcluded:
    def setup_test_environment(self, tmp_path):
        return tmp_path
    def test_default_behavior_shows_excluded_files(self, tmp_path):
    def test_show_excluded_false_removes_files_from_content_section(self, tmp_path):
    def test_show_excluded_with_no_content_flag(self, tmp_path):
    def test_show_excluded_with_metadata_only(self, tmp_path):
    def test_show_excluded_as_default_switch_in_blobify(self, tmp_path):
@show-excluded=false
    def test_command_line_override_blobify_default(self, tmp_path):
    def test_show_excluded_context_integration(self, tmp_path):
@show-excluded=false
    def test_config_apply_default_switches_show_excluded(self):
        import argparse
        from blobify.config import apply_default_switches
    def test_config_apply_default_switches_precedence_show_excluded(self):
        import argparse
        from blobify.config import apply_default_switches
    def test_integration_with_other_switches(self, tmp_path):
    def test_clean_output_example(self, tmp_path):
    def test_show_excluded_with_filters(self, tmp_path):
END_FILE: tests\test_suppress_excluded.py


START_FILE: tests\test_switch_combinations.py
FILE_CONTENT:
from unittest.mock import patch
from blobify.main import main
class TestConfigurationOptionCombinations:
    def setup_test_files(self, tmp_path):
        return tmp_path
    def test_default_all_enabled(self, tmp_path):
    def test_output_content_false_only(self, tmp_path):
    def test_output_index_false_only(self, tmp_path):
    def test_output_metadata_false_only(self, tmp_path):
    def test_output_content_false_output_index_false_metadata_only(self, tmp_path):
    def test_output_content_false_output_metadata_false_index_only(self, tmp_path):
    def test_output_index_false_output_metadata_false_content_only(self, tmp_path):
    def test_all_disabled_no_useful_output(self, tmp_path):
    def test_header_descriptions_accuracy(self, tmp_path):
    def test_status_labels_only_with_content(self, tmp_path):
    def test_line_numbers_enabled_by_default(self, tmp_path):
    def test_output_line_numbers_false_disables_line_numbers(self, tmp_path):
    def test_output_content_false_excludes_all_content_and_line_numbers(self, tmp_path):
class TestConfigurationOptionsWithContext:
    def test_context_with_output_content_false(self, tmp_path):
    def test_context_with_all_options(self, tmp_path):
@output-content=false
@output-metadata=false
    def test_context_with_content_filtering(self, tmp_path):
    def test_context_with_filters_csv_format(self, tmp_path):
@filter="functions","^(def|function)"
@filter="py-only","^def","*.py"
class TestConfigurationOptionDefaults:
    def test_apply_default_options_output_content_false(self):
        import argparse
        from blobify.config import apply_default_switches
    def test_apply_default_options_output_metadata_false(self):
        import argparse
        from blobify.config import apply_default_switches
    def test_apply_default_options_output_index_false(self):
        import argparse
        from blobify.config import apply_default_switches
    def test_apply_default_options_precedence(self):
        import argparse
        from blobify.config import apply_default_switches
    def test_blobify_default_options_integration(self, tmp_path):
    def test_blobify_filter_defaults_csv_format(self, tmp_path):
@filter="functions","^def"
@filter="py-functions","^def","*.py"
END_FILE: tests\test_switch_combinations.py


START_FILE: tests\test_version_consistency.py
FILE_CONTENT:
import re
from pathlib import Path
import pytest
class TestVersionConsistency:
    def test_main_version_matches_pyproject_toml(self):
    def test_version_format_is_valid(self):
        from blobify.main import __version__
    def test_imported_version_accessible(self):
        from blobify.main import __version__
    def test_version_exposed_in_package_init(self):
        import blobify
        from blobify.main import __version__ as main_version
END_FILE: tests\test_version_consistency.py


START_FILE: tests\test_version_switch.py
FILE_CONTENT:
from unittest.mock import patch
from blobify.main import __version__, main
class TestVersionSwitch:
    def test_version_long_flag(self, capsys):
    def test_version_short_flag(self, capsys):
    def test_version_with_directory_ignored(self, tmp_path, capsys):
    def test_version_takes_precedence_over_other_flags(self, tmp_path, capsys):
    def test_version_output_format(self, capsys):
    def test_version_exits_cleanly(self, capsys):
END_FILE: tests\test_version_switch.py
