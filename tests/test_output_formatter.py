"""Tests for output_formatter.py module."""

import tempfile
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

    def test_generate_header_no_git(self, temp_dir):
        """Test generate_header without git repository."""
        header = generate_header(temp_dir, None, None, False, ([], [], []))

        assert "# Blobify Text File Index" in header
        assert "# Not in a git repository" in header
        assert "# Sensitive data scrubbing DISABLED" in header

    def test_generate_header_with_git(self, temp_dir):
        """Test generate_header with git repository."""
        git_root = temp_dir / "repo"
        git_root.mkdir()

        header = generate_header(
            temp_dir,
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
    def test_generate_header_with_scrubbing(self, temp_dir):
        """Test generate_header with scrubbing enabled."""
        header = generate_header(temp_dir, None, None, True, ([], [], []))

        assert "# Content processed with scrubadub" in header
        assert "# WARNING: Review output carefully" in header

    @patch("blobify.output_formatter.SCRUBADUB_AVAILABLE", False)
    def test_generate_header_scrubbing_unavailable(self, temp_dir):
        """Test generate_header when scrubbing is unavailable."""
        header = generate_header(temp_dir, None, None, True, ([], [], []))

        assert "# Sensitive data scrubbing UNAVAILABLE" in header

    def test_generate_index(self):
        """Test generate_index function."""
        all_files = [
            {
                "relative_path": Path("test.py"),
                "is_git_ignored": False,
                "is_blobify_excluded": False,
                "is_blobify_included": False,
            },
            {
                "relative_path": Path("test.log"),
                "is_git_ignored": True,
                "is_blobify_excluded": False,
                "is_blobify_included": False,
            },
            {
                "relative_path": Path("important.py"),
                "is_git_ignored": False,
                "is_blobify_excluded": False,
                "is_blobify_included": True,
            },
            {
                "relative_path": Path("excluded.txt"),
                "is_git_ignored": False,
                "is_blobify_excluded": True,
                "is_blobify_included": False,
            },
        ]

        gitignored_directories = [Path("node_modules")]

        index = generate_index(all_files, gitignored_directories)

        assert "# FILE INDEX" in index
        assert "node_modules [IGNORED BY GITIGNORE]" in index
        assert "test.py" in index
        assert "test.log [IGNORED BY GITIGNORE]" in index
        assert "important.py [INCLUDED BY .blobify]" in index
        assert "excluded.txt [EXCLUDED BY .blobify]" in index

    @patch("blobify.output_formatter.scrub_content")
    @patch("blobify.output_formatter.get_file_metadata")
    def test_generate_content(self, mock_get_metadata, mock_scrub, temp_dir):
        """Test generate_content function."""
        # Create test file
        test_file = temp_dir / "test.py"
        test_file.write_text("print('hello')")

        mock_get_metadata.return_value = {
            "size": 14,
            "created": "2023-01-01T12:00:00",
            "modified": "2023-01-01T12:00:00",
            "accessed": "2023-01-01T12:00:00",
        }
        mock_scrub.return_value = ("print('hello')", 0)

        all_files = [
            {
                "path": test_file,
                "relative_path": Path("test.py"),
                "is_git_ignored": False,
                "is_blobify_excluded": False,
                "is_blobify_included": False,
            }
        ]

        content, substitutions = generate_content(all_files, False, True, False)

        assert "START_FILE: test.py" in content
        assert "END_FILE: test.py" in content
        assert "FILE_METADATA:" in content
        assert "Size: 14 bytes" in content
        assert "1: print('hello')" in content  # With line numbers
        assert substitutions == 0

    @patch("blobify.output_formatter.scrub_content")
    @patch("blobify.output_formatter.get_file_metadata")
    def test_generate_content_git_ignored(self, mock_get_metadata, mock_scrub, temp_dir):
        """Test generate_content with git ignored file."""
        test_file = temp_dir / "test.log"
        test_file.write_text("log content")

        mock_get_metadata.return_value = {
            "size": 11,
            "created": "2023-01-01T12:00:00",
            "modified": "2023-01-01T12:00:00",
            "accessed": "2023-01-01T12:00:00",
        }

        all_files = [
            {
                "path": test_file,
                "relative_path": Path("test.log"),
                "is_git_ignored": True,
                "is_blobify_excluded": False,
                "is_blobify_included": False,
            }
        ]

        content, substitutions = generate_content(all_files, False, False, False)

        assert "[Content excluded - file ignored by .gitignore]" in content
        assert "Status: IGNORED BY GITIGNORE" in content

    @patch("blobify.output_formatter.scrub_content")
    @patch("blobify.output_formatter.get_file_metadata")
    def test_generate_content_blobify_excluded(self, mock_get_metadata, mock_scrub, temp_dir):
        """Test generate_content with blobify excluded file."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("content")

        mock_get_metadata.return_value = {
            "size": 7,
            "created": "2023-01-01T12:00:00",
            "modified": "2023-01-01T12:00:00",
            "accessed": "2023-01-01T12:00:00",
        }

        all_files = [
            {
                "path": test_file,
                "relative_path": Path("test.txt"),
                "is_git_ignored": False,
                "is_blobify_excluded": True,
                "is_blobify_included": False,
            }
        ]

        content, substitutions = generate_content(all_files, False, False, False)

        assert "[Content excluded - file excluded by .blobify]" in content
        assert "Status: EXCLUDED BY .blobify" in content

    @patch("blobify.output_formatter.scrub_content")
    @patch("blobify.output_formatter.get_file_metadata")
    def test_generate_content_no_line_numbers(self, mock_get_metadata, mock_scrub, temp_dir):
        """Test generate_content without line numbers."""
        test_file = temp_dir / "test.py"
        test_file.write_text("print('hello')")

        mock_get_metadata.return_value = {
            "size": 14,
            "created": "2023-01-01T12:00:00",
            "modified": "2023-01-01T12:00:00",
            "accessed": "2023-01-01T12:00:00",
        }
        mock_scrub.return_value = ("print('hello')", 0)

        all_files = [
            {
                "path": test_file,
                "relative_path": Path("test.py"),
                "is_git_ignored": False,
                "is_blobify_excluded": False,
                "is_blobify_included": False,
            }
        ]

        content, substitutions = generate_content(all_files, False, False, False)

        assert "print('hello')" in content
        assert "1: print('hello')" not in content  # No line numbers

    @patch("blobify.output_formatter.generate_header")
    @patch("blobify.output_formatter.generate_index")
    @patch("blobify.output_formatter.generate_content")
    def test_format_output(self, mock_gen_content, mock_gen_index, mock_gen_header, temp_dir):
        """Test format_output function."""
        mock_gen_header.return_value = "# Header\n"
        mock_gen_index.return_value = "# Index\n"
        mock_gen_content.return_value = ("# Content\n", 5)

        discovery_context = {
            "all_files": [{"relative_path": Path("test.py")}],
            "gitignored_directories": [],
            "git_root": temp_dir,
            "included_files": [{"relative_path": Path("test.py")}],
        }

        result, substitutions, file_count = format_output(
            discovery_context,
            temp_dir,
            None,
            False,
            True,
            True,
            False,
            ([], [], []),
        )

        assert result == "# Header\n# Index\n# Content\n"
        assert substitutions == 5
        assert file_count == 1

    @patch("blobify.output_formatter.generate_header")
    @patch("blobify.output_formatter.generate_content")
    def test_format_output_no_index(self, mock_gen_content, mock_gen_header, temp_dir):
        """Test format_output without index."""
        mock_gen_header.return_value = "# Header\n"
        mock_gen_content.return_value = ("# Content\n", 0)

        discovery_context = {
            "all_files": [],
            "gitignored_directories": [],
            "git_root": None,
            "included_files": [],
        }

        result, substitutions, file_count = format_output(
            discovery_context,
            temp_dir,
            None,
            False,
            True,
            False,  # No index
            False,
            ([], [], []),
        )

        assert "# Header\n" in result
        assert "# FILE CONTENTS\n" in result
        assert "# FILE INDEX" not in result
