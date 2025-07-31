"""Tests for output_formatter.py module."""

from pathlib import Path
from unittest.mock import patch

import pytest

from blobify.output_formatter import (
    format_output,
    generate_content,
    generate_header,
    generate_index,
)


class TestOutputFormatter:
    """Test cases for output formatting functions."""

    def test_generate_header_basic(self, tmp_path):
        """Test generate_header with basic functionality."""
        header = generate_header(tmp_path, None, None, False, ([], [], []))

        assert "# Blobify Text File Index" in header
        assert "# Not in a git repository" in header
        assert "# Sensitive data scrubbing DISABLED" in header
        assert str(tmp_path.absolute()) in header

    def test_generate_header_with_git_and_context(self, tmp_path):
        """Test generate_header with git repository and context."""
        git_root = tmp_path / "repo"
        git_root.mkdir()

        header = generate_header(
            tmp_path,
            git_root,
            "test-context",
            True,
            (["*.py"], ["*.log"], ["debug"]),
        )

        assert f"# Git repository: {git_root}" in header
        assert (
            "# .blobify configuration (context: test-context): 1 include patterns, 1 exclude patterns, 1 default switches"
            in header
        )

    @patch("blobify.output_formatter.SCRUBADUB_AVAILABLE", True)
    def test_generate_header_scrubbing_enabled(self, tmp_path):
        """Test generate_header with scrubbing enabled."""
        header = generate_header(tmp_path, None, None, True, ([], [], []))

        assert "# Content processed with scrubadub" in header
        assert "# WARNING: Review output carefully" in header

    @patch("blobify.output_formatter.SCRUBADUB_AVAILABLE", False)
    def test_generate_header_scrubbing_unavailable(self, tmp_path):
        """Test generate_header when scrubbing is unavailable."""
        header = generate_header(tmp_path, None, None, True, ([], [], []))

        assert "# Sensitive data scrubbing UNAVAILABLE" in header

    def test_generate_index_all_file_types(self):
        """Test generate_index with comprehensive file types."""
        all_files = [
            {
                "relative_path": Path("normal.py"),
                "is_git_ignored": False,
                "is_blobify_excluded": False,
                "is_blobify_included": False,
            },
            {
                "relative_path": Path("ignored.log"),
                "is_git_ignored": True,
                "is_blobify_excluded": False,
                "is_blobify_included": False,
            },
            {
                "relative_path": Path("included.txt"),
                "is_git_ignored": False,
                "is_blobify_excluded": False,
                "is_blobify_included": True,
            },
            {
                "relative_path": Path("excluded.md"),
                "is_git_ignored": False,
                "is_blobify_excluded": True,
                "is_blobify_included": False,
            },
        ]

        gitignored_directories = [Path("node_modules"), Path("build")]

        index = generate_index(all_files, gitignored_directories)

        # Check structure
        assert "# FILE INDEX" in index
        assert "# FILE CONTENTS" in index
        assert "#" * 80 in index

        # Check directory entries
        assert "node_modules [IGNORED BY GITIGNORE]" in index
        assert "build [IGNORED BY GITIGNORE]" in index

        # Check file entries with correct labels
        lines = index.split("\n")
        assert any("normal.py" in line and "[" not in line for line in lines)  # Normal file, no label
        assert "ignored.log [IGNORED BY GITIGNORE]" in index
        assert "included.txt [INCLUDED BY .blobify]" in index
        assert "excluded.md [EXCLUDED BY .blobify]" in index

    def test_generate_content_with_real_files(self, tmp_path):
        """Test generate_content with actual files."""
        # Create real test files
        py_file = tmp_path / "test.py"
        py_content = "def hello():\n    print('world')\n    return 42"
        py_file.write_text(py_content)

        log_file = tmp_path / "debug.log"
        log_file.write_text("Error: something happened")

        all_files = [
            {
                "path": py_file,
                "relative_path": Path("test.py"),
                "is_git_ignored": False,
                "is_blobify_excluded": False,
                "is_blobify_included": False,
            },
            {
                "path": log_file,
                "relative_path": Path("debug.log"),
                "is_git_ignored": True,
                "is_blobify_excluded": False,
                "is_blobify_included": False,
            },
        ]

        # Test with line numbers
        content, substitutions = generate_content(all_files, scrub_data=False, include_line_numbers=True, debug=False)

        # Verify structure
        assert "START_FILE: test.py" in content
        assert "END_FILE: test.py" in content
        assert "FILE_METADATA:" in content

        # Check actual file size (content length in bytes when encoded as UTF-8)
        expected_size = len(py_content.encode("utf-8"))
        assert f"Size: {expected_size} bytes" in content

        # Verify line numbers are added
        assert "1: def hello():" in content
        assert "2:     print('world')" in content
        assert "3:     return 42" in content

        # Verify git ignored file handling
        assert "START_FILE: debug.log" in content
        assert "[Content excluded - file ignored by .gitignore]" in content
        assert "Error: something happened" not in content
        assert substitutions == 0

    def test_generate_content_line_numbers_control(self, tmp_path):
        """Test line number inclusion/exclusion."""
        test_file = tmp_path / "simple.py"
        test_file.write_text("print('no lines')")

        all_files = [
            {
                "path": test_file,
                "relative_path": Path("simple.py"),
                "is_git_ignored": False,
                "is_blobify_excluded": False,
                "is_blobify_included": False,
            }
        ]

        # Without line numbers
        content, *_ = generate_content(all_files, scrub_data=False, include_line_numbers=False, debug=False)
        assert "print('no lines')" in content
        assert "1: print('no lines')" not in content

        # With line numbers
        content_with_lines, *_ = generate_content(all_files, scrub_data=False, include_line_numbers=True, debug=False)
        assert "1: print('no lines')" in content_with_lines

    def test_generate_content_exclusion_handling(self, tmp_path):
        """Test different file exclusion scenarios."""
        # Test blobify excluded
        excluded_file = tmp_path / "secret.txt"
        excluded_file.write_text("secret content")

        excluded_files = [
            {
                "path": excluded_file,
                "relative_path": Path("secret.txt"),
                "is_git_ignored": False,
                "is_blobify_excluded": True,
                "is_blobify_included": False,
            }
        ]

        content, *_ = generate_content(excluded_files, scrub_data=False, include_line_numbers=False, debug=False)
        assert "[Content excluded - file excluded by .blobify]" in content
        assert "secret content" not in content
        assert "Status: EXCLUDED BY .blobify" in content

    def test_generate_content_error_handling(self, tmp_path):
        """Test file read error handling."""
        # Reference non-existent file
        missing_file = tmp_path / "missing.py"

        all_files = [
            {
                "path": missing_file,  # File doesn't exist
                "relative_path": Path("missing.py"),
                "is_git_ignored": False,
                "is_blobify_excluded": False,
                "is_blobify_included": False,
            }
        ]

        # The function should handle the missing file gracefully
        content, *_ = generate_content(all_files, scrub_data=False, include_line_numbers=False, debug=False)

        assert "START_FILE: missing.py" in content
        assert "END_FILE: missing.py" in content
        # Should contain error message about reading the file
        assert "[Error reading file:" in content
        # Should show metadata with default values for missing file
        assert "Size: 0 bytes" in content

    def test_format_output_end_to_end(self, tmp_path):
        """Test format_output with real files - complete integration."""
        # Create real files
        py_file = tmp_path / "app.py"
        py_file.write_text("print('hello')")

        md_file = tmp_path / "README.md"
        md_file.write_text("# Project")

        # Create realistic discovery context
        discovery_context = {
            "all_files": [
                {
                    "path": py_file,
                    "relative_path": Path("app.py"),
                    "is_git_ignored": False,
                    "is_blobify_excluded": False,
                    "is_blobify_included": False,
                },
                {
                    "path": md_file,
                    "relative_path": Path("README.md"),
                    "is_git_ignored": True,
                    "is_blobify_excluded": False,
                    "is_blobify_included": False,
                },
            ],
            "gitignored_directories": [Path("node_modules")],
            "git_root": tmp_path,
            "included_files": [
                {
                    "path": py_file,
                    "relative_path": Path("app.py"),
                    "is_git_ignored": False,
                    "is_blobify_excluded": False,
                    "is_blobify_included": False,
                }
            ],
        }

        result, substitutions, file_count = format_output(
            discovery_context,
            tmp_path,
            context=None,
            scrub_data=False,
            include_line_numbers=True,
            include_index=True,
            debug=False,
            blobify_patterns_info=([], [], []),
        )

        # Verify complete output structure
        assert "# Blobify Text File Index" in result
        assert f"# Git repository: {tmp_path}" in result
        assert "# FILE INDEX" in result
        assert "# FILE CONTENTS" in result

        # Verify index content
        assert "app.py" in result
        assert "README.md [IGNORED BY GITIGNORE]" in result
        assert "node_modules [IGNORED BY GITIGNORE]" in result

        # Verify file content
        assert "START_FILE: app.py" in result
        assert "1: print('hello')" in result
        assert "END_FILE: app.py" in result
        assert "START_FILE: README.md" in result
        assert "[Content excluded - file ignored by .gitignore]" in result

        # Verify metadata
        assert substitutions == 0
        assert file_count == 1

    def test_format_output_no_index_option(self, tmp_path):
        """Test format_output without file index."""
        py_file = tmp_path / "test.py"
        py_file.write_text("test content")

        discovery_context = {
            "all_files": [
                {
                    "path": py_file,
                    "relative_path": Path("test.py"),
                    "is_git_ignored": False,
                    "is_blobify_excluded": False,
                    "is_blobify_included": False,
                }
            ],
            "gitignored_directories": [],
            "git_root": None,
            "included_files": [
                {
                    "path": py_file,
                    "relative_path": Path("test.py"),
                    "is_git_ignored": False,
                    "is_blobify_excluded": False,
                    "is_blobify_included": False,
                }
            ],
        }

        result, substitutions, file_count = format_output(
            discovery_context,
            tmp_path,
            context=None,
            scrub_data=False,
            include_line_numbers=True,
            include_index=False,  # No index
            debug=False,
            blobify_patterns_info=([], [], []),
        )

        # Should have contents but no index section
        assert "# FILE CONTENTS" in result
        assert "# FILE INDEX" not in result
        assert "test.py" in result  # Still appears in content
        assert "START_FILE: test.py" in result
        assert "test content" in result

    def test_format_output_with_blobify_context(self, tmp_path):
        """Test format_output with blobify context information."""
        test_file = tmp_path / "script.py"
        test_file.write_text("import os")

        discovery_context = {
            "all_files": [
                {
                    "path": test_file,
                    "relative_path": Path("script.py"),
                    "is_git_ignored": False,
                    "is_blobify_excluded": False,
                    "is_blobify_included": True,  # Included by blobify
                }
            ],
            "gitignored_directories": [],
            "git_root": tmp_path,
            "included_files": [
                {
                    "path": test_file,
                    "relative_path": Path("script.py"),
                    "is_git_ignored": False,
                    "is_blobify_excluded": False,
                    "is_blobify_included": True,
                }
            ],
        }

        result, substitutions, file_count = format_output(
            discovery_context,
            tmp_path,
            context="dev-context",
            scrub_data=False,
            include_line_numbers=False,
            include_index=True,
            debug=False,
            blobify_patterns_info=(["*.py"], ["*.log"], ["debug"]),
        )

        # Verify context and patterns are reflected in header
        assert (
            "# .blobify configuration (context: dev-context): 1 include patterns, 1 exclude patterns, 1 default switches"
            in result
        )
        assert "script.py [INCLUDED BY .blobify]" in result
        assert "import os" in result
