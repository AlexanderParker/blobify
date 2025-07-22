"""Tests for output_formatter.py module."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from blobify.output_formatter import (
    generate_header,
    generate_index,
    generate_content,
    format_output,
)


class TestOutputFormatter(unittest.TestCase):
    """Test cases for output formatting functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        """Clean up test fixtures."""
        for file in self.temp_dir.rglob("*"):
            if file.is_file():
                file.unlink()
        for dir in sorted(self.temp_dir.rglob("*"), reverse=True):
            if dir.is_dir():
                dir.rmdir()
        self.temp_dir.rmdir()

    def test_generate_header_no_git(self):
        """Test generate_header without git repository."""
        header = generate_header(self.temp_dir, None, None, False, ([], [], []))

        self.assertIn("# Blobify Text File Index", header)
        self.assertIn("# Not in a git repository", header)
        self.assertIn("# Sensitive data scrubbing DISABLED", header)

    def test_generate_header_with_git(self):
        """Test generate_header with git repository."""
        git_root = self.temp_dir / "repo"
        git_root.mkdir()

        header = generate_header(
            self.temp_dir,
            git_root,
            "test-context",
            True,
            (["*.py"], ["*.log"], ["debug"]),
        )

        self.assertIn(f"# Git repository: {git_root}", header)
        self.assertIn(
            "# .blobify configuration (context: test-context): 1 include patterns, 1 exclude patterns, 1 default switches",
            header,
        )

    @patch("blobify.output_formatter.SCRUBADUB_AVAILABLE", True)
    def test_generate_header_with_scrubbing(self):
        """Test generate_header with scrubbing enabled."""
        header = generate_header(self.temp_dir, None, None, True, ([], [], []))

        self.assertIn("# Content processed with scrubadub", header)
        self.assertIn("# WARNING: Review output carefully", header)

    @patch("blobify.output_formatter.SCRUBADUB_AVAILABLE", False)
    def test_generate_header_scrubbing_unavailable(self):
        """Test generate_header when scrubbing is unavailable."""
        header = generate_header(self.temp_dir, None, None, True, ([], [], []))

        self.assertIn("# Sensitive data scrubbing UNAVAILABLE", header)

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

        self.assertIn("# FILE INDEX", index)
        self.assertIn("node_modules [IGNORED BY GITIGNORE]", index)
        self.assertIn("test.py", index)
        self.assertIn("test.log [IGNORED BY GITIGNORE]", index)
        self.assertIn("important.py [INCLUDED BY .blobify]", index)
        self.assertIn("excluded.txt [EXCLUDED BY .blobify]", index)

    @patch("blobify.output_formatter.scrub_content")
    @patch("blobify.output_formatter.get_file_metadata")
    def test_generate_content(self, mock_get_metadata, mock_scrub):
        """Test generate_content function."""
        # Create test file
        test_file = self.temp_dir / "test.py"
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

        self.assertIn("START_FILE: test.py", content)
        self.assertIn("END_FILE: test.py", content)
        self.assertIn("FILE_METADATA:", content)
        self.assertIn("Size: 14 bytes", content)
        self.assertIn("1: print('hello')", content)  # With line numbers
        self.assertEqual(substitutions, 0)

    @patch("blobify.output_formatter.scrub_content")
    @patch("blobify.output_formatter.get_file_metadata")
    def test_generate_content_git_ignored(self, mock_get_metadata, mock_scrub):
        """Test generate_content with git ignored file."""
        test_file = self.temp_dir / "test.log"
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

        self.assertIn("[Content excluded - file ignored by .gitignore]", content)
        self.assertIn("Status: IGNORED BY GITIGNORE", content)

    @patch("blobify.output_formatter.scrub_content")
    @patch("blobify.output_formatter.get_file_metadata")
    def test_generate_content_blobify_excluded(self, mock_get_metadata, mock_scrub):
        """Test generate_content with blobify excluded file."""
        test_file = self.temp_dir / "test.txt"
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

        self.assertIn("[Content excluded - file excluded by .blobify]", content)
        self.assertIn("Status: EXCLUDED BY .blobify", content)

    @patch("blobify.output_formatter.scrub_content")
    @patch("blobify.output_formatter.get_file_metadata")
    def test_generate_content_no_line_numbers(self, mock_get_metadata, mock_scrub):
        """Test generate_content without line numbers."""
        test_file = self.temp_dir / "test.py"
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

        self.assertIn("print('hello')", content)
        self.assertNotIn("1: print('hello')", content)  # No line numbers

    @patch("blobify.output_formatter.generate_header")
    @patch("blobify.output_formatter.generate_index")
    @patch("blobify.output_formatter.generate_content")
    def test_format_output(self, mock_gen_content, mock_gen_index, mock_gen_header):
        """Test format_output function."""
        mock_gen_header.return_value = "# Header\n"
        mock_gen_index.return_value = "# Index\n"
        mock_gen_content.return_value = ("# Content\n", 5)

        discovery_context = {
            "all_files": [{"relative_path": Path("test.py")}],
            "gitignored_directories": [],
            "git_root": self.temp_dir,
            "included_files": [{"relative_path": Path("test.py")}],
        }

        result, substitutions, file_count = format_output(
            discovery_context,
            self.temp_dir,
            None,
            False,
            True,
            True,
            False,
            ([], [], []),
        )

        self.assertEqual(result, "# Header\n# Index\n# Content\n")
        self.assertEqual(substitutions, 5)
        self.assertEqual(file_count, 1)

    @patch("blobify.output_formatter.generate_header")
    @patch("blobify.output_formatter.generate_content")
    def test_format_output_no_index(self, mock_gen_content, mock_gen_header):
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
            self.temp_dir,
            None,
            False,
            True,
            False,  # No index
            False,
            ([], [], []),
        )

        self.assertIn("# Header\n", result)
        self.assertIn("# FILE CONTENTS\n", result)
        self.assertNotIn("# FILE INDEX", result)


if __name__ == "__main__":
    unittest.main()
