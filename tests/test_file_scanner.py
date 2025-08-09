"""Tests for file_scanner.py module."""

import tempfile
from pathlib import Path
from unittest.mock import patch

from blobify.file_scanner import (
    apply_blobify_patterns,
    discover_files,
    get_built_in_ignored_patterns,
    matches_pattern,
    scan_files,
)


class TestFileScanner:
    """Test cases for file scanning and pattern matching."""

    def test_matches_pattern_exact(self, tmp_path):
        """Test exact pattern matching."""
        test_file = tmp_path / "test.py"
        test_file.write_text("test")

        result = matches_pattern(test_file, tmp_path, "test.py")
        assert result is True

    def test_matches_pattern_glob(self, tmp_path):
        """Test glob pattern matching."""
        test_file = tmp_path / "test.py"
        test_file.write_text("test")

        result = matches_pattern(test_file, tmp_path, "*.py")
        assert result is True

    def test_matches_pattern_directory(self, tmp_path):
        """Test directory pattern matching."""
        sub_dir = tmp_path / "src"
        sub_dir.mkdir()
        test_file = sub_dir / "test.py"
        test_file.write_text("test")

        result = matches_pattern(test_file, tmp_path, "src/")
        assert result is True

    def test_matches_pattern_no_match(self, tmp_path):
        """Test pattern that doesn't match."""
        test_file = tmp_path / "test.py"
        test_file.write_text("test")

        result = matches_pattern(test_file, tmp_path, "*.js")
        assert result is False

    def test_matches_pattern_outside_base(self):
        """Test pattern matching with file outside base path."""
        other_dir = Path(tempfile.mkdtemp())
        temp_dir = Path(tempfile.mkdtemp())
        test_file = other_dir / "test.py"
        test_file.write_text("test")

        try:
            result = matches_pattern(test_file, temp_dir, "*.py")
            assert result is False
        finally:
            test_file.unlink()
            other_dir.rmdir()
            temp_dir.rmdir()

    def test_get_built_in_ignored_patterns(self):
        """Test getting built-in ignored patterns."""
        patterns = get_built_in_ignored_patterns()

        # Check some expected patterns
        assert ".git" in patterns
        assert "node_modules" in patterns
        assert "__pycache__" in patterns
        assert ".venv" in patterns

    @patch("blobify.file_scanner.is_git_repository")
    @patch("blobify.file_scanner.get_gitignore_patterns")
    def test_discover_files_no_git(self, mock_get_patterns, mock_is_git, tmp_path):
        """Test discover_files when not in git repository."""
        mock_is_git.return_value = None

        # Create test files
        (tmp_path / "test.py").write_text("test")
        (tmp_path / "README.md").write_text("readme")

        # Create ignored directory
        ignored_dir = tmp_path / "node_modules"
        ignored_dir.mkdir()
        (ignored_dir / "package.js").write_text("ignored")

        context = discover_files(tmp_path)

        assert context["git_root"] is None
        assert len(context["all_files"]) == 2

        # Check that node_modules was ignored
        file_paths = [f["relative_path"] for f in context["all_files"]]
        assert Path("node_modules/package.js") not in file_paths

    @patch("blobify.file_scanner.is_git_repository")
    @patch("blobify.file_scanner.get_gitignore_patterns")
    @patch("blobify.file_scanner.is_ignored_by_git")
    def test_discover_files_with_git(self, mock_is_ignored, mock_get_patterns, mock_is_git, tmp_path):
        """Test discover_files with git repository."""
        mock_is_git.return_value = tmp_path
        mock_get_patterns.return_value = {tmp_path: ["*.log"]}
        mock_is_ignored.side_effect = lambda path, *args: path.suffix == ".log"

        # Create test files
        (tmp_path / "test.py").write_text("test")
        (tmp_path / "test.log").write_text("log")

        context = discover_files(tmp_path)

        assert context["git_root"] == tmp_path
        assert len(context["all_files"]) == 2

        # Check git ignored status
        log_file = next(f for f in context["all_files"] if f["relative_path"].name == "test.log")
        py_file = next(f for f in context["all_files"] if f["relative_path"].name == "test.py")

        assert log_file["is_git_ignored"] is True
        assert py_file["is_git_ignored"] is False

    def test_apply_blobify_patterns_no_git(self, tmp_path):
        """Test apply_blobify_patterns when not in git repository."""
        context = {"all_files": [], "git_root": None, "patterns_by_dir": {}}

        apply_blobify_patterns(context, tmp_path)

        # Should not modify anything
        assert context["all_files"] == []

    @patch("blobify.file_scanner.read_blobify_config")
    def test_apply_blobify_patterns_with_config(self, mock_read_config, tmp_path):
        """Test apply_blobify_patterns with .blobify configuration."""
        # Fix: Return 4-tuple to match expected signature
        mock_read_config.return_value = (["*.py"], ["*.log"], [], [])

        # Create test files
        (tmp_path / "test.py").write_text("test")
        (tmp_path / "test.log").write_text("log")
        (tmp_path / "README.md").write_text("readme")

        # Initial context with all files marked as git ignored
        context = {
            "all_files": [
                {
                    "path": tmp_path / "test.py",
                    "relative_path": Path("test.py"),
                    "is_git_ignored": True,
                    "is_blobify_excluded": False,
                    "is_blobify_included": False,
                    "include_in_output": False,
                },
                {
                    "path": tmp_path / "README.md",
                    "relative_path": Path("README.md"),
                    "is_git_ignored": False,
                    "is_blobify_excluded": False,
                    "is_blobify_included": False,
                    "include_in_output": True,
                },
            ],
            "git_root": tmp_path,
            "patterns_by_dir": {},
        }

        apply_blobify_patterns(context, tmp_path)

        # Check that test.py was included by .blobify
        py_file = next(f for f in context["all_files"] if f["relative_path"].name == "test.py")
        assert py_file["is_blobify_included"] is True
        assert py_file["include_in_output"] is True

        # Check that README.md was not affected
        md_file = next(f for f in context["all_files"] if f["relative_path"].name == "README.md")
        assert md_file["is_blobify_included"] is False

    @patch("blobify.file_scanner.discover_files")
    @patch("blobify.file_scanner.apply_blobify_patterns")
    def test_scan_files(self, mock_apply_patterns, mock_discover, tmp_path):
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

        result = scan_files(tmp_path)

        mock_discover.assert_called_once_with(tmp_path, False)
        mock_apply_patterns.assert_called_once_with(mock_context, tmp_path, None, False)

        # Check result structure
        assert "included_files" in result
        assert "git_ignored_files" in result
        assert "blobify_excluded_files" in result

        assert len(result["included_files"]) == 1
        assert len(result["git_ignored_files"]) == 1
