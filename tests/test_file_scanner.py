"""Tests for file_scanner.py module."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from blobify.file_scanner import (
    matches_pattern,
    get_built_in_ignored_patterns,
    discover_files,
    apply_blobify_patterns,
    scan_files,
)


class TestFileScanner(unittest.TestCase):
    """Test cases for file scanning and pattern matching."""

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

    def test_matches_pattern_exact(self):
        """Test exact pattern matching."""
        test_file = self.temp_dir / "test.py"
        test_file.write_text("test")

        result = matches_pattern(test_file, self.temp_dir, "test.py")
        self.assertTrue(result)

    def test_matches_pattern_glob(self):
        """Test glob pattern matching."""
        test_file = self.temp_dir / "test.py"
        test_file.write_text("test")

        result = matches_pattern(test_file, self.temp_dir, "*.py")
        self.assertTrue(result)

    def test_matches_pattern_directory(self):
        """Test directory pattern matching."""
        sub_dir = self.temp_dir / "src"
        sub_dir.mkdir()
        test_file = sub_dir / "test.py"
        test_file.write_text("test")

        result = matches_pattern(test_file, self.temp_dir, "src/")
        self.assertTrue(result)

    def test_matches_pattern_no_match(self):
        """Test pattern that doesn't match."""
        test_file = self.temp_dir / "test.py"
        test_file.write_text("test")

        result = matches_pattern(test_file, self.temp_dir, "*.js")
        self.assertFalse(result)

    def test_matches_pattern_outside_base(self):
        """Test pattern matching with file outside base path."""
        other_dir = Path(tempfile.mkdtemp())
        test_file = other_dir / "test.py"
        test_file.write_text("test")

        try:
            result = matches_pattern(test_file, self.temp_dir, "*.py")
            self.assertFalse(result)
        finally:
            test_file.unlink()
            other_dir.rmdir()

    def test_get_built_in_ignored_patterns(self):
        """Test getting built-in ignored patterns."""
        patterns = get_built_in_ignored_patterns()

        # Check some expected patterns
        self.assertIn(".git", patterns)
        self.assertIn("node_modules", patterns)
        self.assertIn("__pycache__", patterns)
        self.assertIn(".venv", patterns)

    @patch("blobify.file_scanner.is_git_repository")
    @patch("blobify.file_scanner.get_gitignore_patterns")
    def test_discover_files_no_git(self, mock_get_patterns, mock_is_git):
        """Test discover_files when not in git repository."""
        mock_is_git.return_value = None

        # Create test files
        (self.temp_dir / "test.py").write_text("test")
        (self.temp_dir / "README.md").write_text("readme")

        # Create ignored directory
        ignored_dir = self.temp_dir / "node_modules"
        ignored_dir.mkdir()
        (ignored_dir / "package.js").write_text("ignored")

        context = discover_files(self.temp_dir)

        self.assertIsNone(context["git_root"])
        self.assertEqual(len(context["all_files"]), 2)

        # Check that node_modules was ignored
        file_paths = [f["relative_path"] for f in context["all_files"]]
        self.assertNotIn(Path("node_modules/package.js"), file_paths)

    @patch("blobify.file_scanner.is_git_repository")
    @patch("blobify.file_scanner.get_gitignore_patterns")
    @patch("blobify.file_scanner.is_ignored_by_git")
    def test_discover_files_with_git(
        self, mock_is_ignored, mock_get_patterns, mock_is_git
    ):
        """Test discover_files with git repository."""
        mock_is_git.return_value = self.temp_dir
        mock_get_patterns.return_value = {self.temp_dir: ["*.log"]}
        mock_is_ignored.side_effect = lambda path, *args: path.suffix == ".log"

        # Create test files
        (self.temp_dir / "test.py").write_text("test")
        (self.temp_dir / "test.log").write_text("log")

        context = discover_files(self.temp_dir)

        self.assertEqual(context["git_root"], self.temp_dir)
        self.assertEqual(len(context["all_files"]), 2)

        # Check git ignored status
        log_file = next(
            f for f in context["all_files"] if f["relative_path"].name == "test.log"
        )
        py_file = next(
            f for f in context["all_files"] if f["relative_path"].name == "test.py"
        )

        self.assertTrue(log_file["is_git_ignored"])
        self.assertFalse(py_file["is_git_ignored"])

    def test_apply_blobify_patterns_no_git(self):
        """Test apply_blobify_patterns when not in git repository."""
        context = {"all_files": [], "git_root": None, "patterns_by_dir": {}}

        apply_blobify_patterns(context, self.temp_dir)

        # Should not modify anything
        self.assertEqual(context["all_files"], [])

    @patch("blobify.file_scanner.read_blobify_config")
    def test_apply_blobify_patterns_with_config(self, mock_read_config):
        """Test apply_blobify_patterns with .blobify configuration."""
        mock_read_config.return_value = (["*.py"], ["*.log"], [])

        # Create test files
        (self.temp_dir / "test.py").write_text("test")
        (self.temp_dir / "test.log").write_text("log")
        (self.temp_dir / "README.md").write_text("readme")

        # Initial context with all files marked as git ignored
        context = {
            "all_files": [
                {
                    "path": self.temp_dir / "test.py",
                    "relative_path": Path("test.py"),
                    "is_git_ignored": True,
                    "is_blobify_excluded": False,
                    "is_blobify_included": False,
                    "include_in_output": False,
                },
                {
                    "path": self.temp_dir / "README.md",
                    "relative_path": Path("README.md"),
                    "is_git_ignored": False,
                    "is_blobify_excluded": False,
                    "is_blobify_included": False,
                    "include_in_output": True,
                },
            ],
            "git_root": self.temp_dir,
            "patterns_by_dir": {},
        }

        apply_blobify_patterns(context, self.temp_dir)

        # Check that test.py was included by .blobify
        py_file = next(
            f for f in context["all_files"] if f["relative_path"].name == "test.py"
        )
        self.assertTrue(py_file["is_blobify_included"])
        self.assertTrue(py_file["include_in_output"])

        # Check that README.md was not affected
        md_file = next(
            f for f in context["all_files"] if f["relative_path"].name == "README.md"
        )
        self.assertFalse(md_file["is_blobify_included"])

    @patch("blobify.file_scanner.discover_files")
    @patch("blobify.file_scanner.apply_blobify_patterns")
    def test_scan_files(self, mock_apply_patterns, mock_discover):
        """Test main scan_files function."""
        mock_context = {
            "all_files": [
                {
                    "include_in_output": True,
                    "is_git_ignored": False,
                    "is_blobify_excluded": False,
                },
                {
                    "include_in_output": False,
                    "is_git_ignored": True,
                    "is_blobify_excluded": False,
                },
            ],
            "gitignored_directories": [],
        }
        mock_discover.return_value = mock_context

        result = scan_files(self.temp_dir)

        mock_discover.assert_called_once_with(self.temp_dir, False)
        mock_apply_patterns.assert_called_once_with(
            mock_context, self.temp_dir, None, False
        )

        # Check result structure
        self.assertIn("included_files", result)
        self.assertIn("git_ignored_files", result)
        self.assertIn("blobify_excluded_files", result)

        self.assertEqual(len(result["included_files"]), 1)
        self.assertEqual(len(result["git_ignored_files"]), 1)


if __name__ == "__main__":
    unittest.main()
