"""Tests for git_utils.py module."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from blobify.git_utils import (
    is_git_repository,
    get_gitignore_patterns,
    is_ignored_by_git,
    gitignore_to_regex,
    compile_gitignore_patterns,
    read_gitignore_file,
)


class TestGitUtils(unittest.TestCase):
    """Test cases for git utilities."""

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

    def test_is_git_repository_found(self):
        """Test is_git_repository when .git directory exists."""
        git_dir = self.temp_dir / ".git"
        git_dir.mkdir()

        result = is_git_repository(self.temp_dir)
        self.assertEqual(result, self.temp_dir)

    def test_is_git_repository_not_found(self):
        """Test is_git_repository when no .git directory exists."""
        result = is_git_repository(self.temp_dir)
        self.assertIsNone(result)

    def test_is_git_repository_parent_directory(self):
        """Test is_git_repository finds .git in parent directory."""
        git_dir = self.temp_dir / ".git"
        git_dir.mkdir()
        sub_dir = self.temp_dir / "subdir"
        sub_dir.mkdir()

        result = is_git_repository(sub_dir)
        self.assertEqual(result, self.temp_dir)

    def test_read_gitignore_file(self):
        """Test reading .gitignore file patterns."""
        gitignore = self.temp_dir / ".gitignore"
        gitignore.write_text(
            """
# Comment
*.log
temp/

# Another comment
build/
"""
        )
        patterns = read_gitignore_file(gitignore)
        self.assertEqual(patterns, ["*.log", "temp/", "build/"])

    def test_read_gitignore_file_nonexistent(self):
        """Test reading nonexistent .gitignore file."""
        gitignore = self.temp_dir / ".gitignore"
        patterns = read_gitignore_file(gitignore)
        self.assertEqual(patterns, [])

    def test_gitignore_to_regex_simple(self):
        """Test gitignore pattern to regex conversion."""
        regex = gitignore_to_regex("*.log")
        self.assertEqual(regex, "^([^/]*\\.log|.*[^/]*\\.log)$")

    def test_gitignore_to_regex_directory(self):
        """Test gitignore directory pattern to regex conversion."""
        regex = gitignore_to_regex("build/")
        expected = "^(build|build/.*|.*/build|.*/build/.*)$"
        self.assertEqual(regex, expected)

    def test_gitignore_to_regex_root_relative(self):
        """Test gitignore root-relative pattern to regex conversion."""
        regex = gitignore_to_regex("/build")
        self.assertEqual(regex, "^build$")

    def test_gitignore_to_regex_doublestar(self):
        """Test gitignore doublestar pattern to regex conversion."""
        regex = gitignore_to_regex("docs/**")
        expected = "^(docs/.*|.*/docs/.*)$"
        self.assertEqual(regex, expected)

    def test_compile_gitignore_patterns(self):
        """Test compiling gitignore patterns to regex."""
        patterns = ["*.log", "!important.log", "build/"]
        compiled = compile_gitignore_patterns(patterns)

        self.assertEqual(len(compiled), 3)
        self.assertFalse(compiled[0][1])  # Not negation
        self.assertTrue(compiled[1][1])  # Is negation
        self.assertFalse(compiled[2][1])  # Not negation

    def test_compile_gitignore_patterns_invalid_regex(self):
        """Test compiling patterns with invalid regex."""
        patterns = ["[invalid", "*.log"]
        compiled = compile_gitignore_patterns(patterns)

        # Should skip invalid pattern
        self.assertEqual(len(compiled), 1)

    @patch("blobify.git_utils.subprocess.run")
    def test_get_gitignore_patterns_with_global(self, mock_run):
        """Test getting gitignore patterns including global gitignore."""
        # Setup git directory
        git_dir = self.temp_dir / ".git"
        git_dir.mkdir()

        # Setup global gitignore
        global_gitignore = self.temp_dir / "global.gitignore"
        global_gitignore.write_text("*.tmp\n")

        # Setup repo gitignore
        repo_gitignore = self.temp_dir / ".gitignore"
        repo_gitignore.write_text("*.log\n")

        # Mock git config command
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = str(global_gitignore)
        mock_run.return_value = mock_result

        patterns_by_dir = get_gitignore_patterns(self.temp_dir)

        # Should include both global and repo patterns
        self.assertIn(self.temp_dir, patterns_by_dir)
        patterns = patterns_by_dir[self.temp_dir]
        self.assertIn("*.tmp", patterns)
        self.assertIn("*.log", patterns)

    @patch("blobify.git_utils.subprocess.run")
    def test_get_gitignore_patterns_no_global(self, mock_run):
        """Test getting gitignore patterns without global gitignore."""
        # Setup git directory
        git_dir = self.temp_dir / ".git"
        git_dir.mkdir()

        # Setup repo gitignore
        repo_gitignore = self.temp_dir / ".gitignore"
        repo_gitignore.write_text("*.log\n")

        # Mock git config command (no global gitignore)
        mock_result = Mock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        patterns_by_dir = get_gitignore_patterns(self.temp_dir)

        # Should only include repo patterns
        self.assertIn(self.temp_dir, patterns_by_dir)
        patterns = patterns_by_dir[self.temp_dir]
        self.assertEqual(patterns, ["*.log"])

    @patch("blobify.git_utils.subprocess.run", side_effect=Exception("Git error"))
    def test_get_gitignore_patterns_git_error(self, mock_run):
        """Test getting gitignore patterns when git command fails."""
        # Setup git directory
        git_dir = self.temp_dir / ".git"
        git_dir.mkdir()

        # Setup repo gitignore
        repo_gitignore = self.temp_dir / ".gitignore"
        repo_gitignore.write_text("*.log\n")

        patterns_by_dir = get_gitignore_patterns(self.temp_dir)

        # Should still get repo patterns despite git error
        self.assertIn(self.temp_dir, patterns_by_dir)
        patterns = patterns_by_dir[self.temp_dir]
        self.assertEqual(patterns, ["*.log"])

    def test_is_ignored_by_git_simple(self):
        """Test is_ignored_by_git with simple patterns."""
        # Create test file
        test_file = self.temp_dir / "test.log"
        test_file.write_text("test")

        # Create patterns dict
        patterns_by_dir = {self.temp_dir: ["*.log"]}

        result = is_ignored_by_git(test_file, self.temp_dir, patterns_by_dir)
        self.assertTrue(result)

    def test_is_ignored_by_git_negation(self):
        """Test is_ignored_by_git with negation patterns."""
        # Create test file
        test_file = self.temp_dir / "important.log"
        test_file.write_text("test")

        # Create patterns dict with negation
        patterns_by_dir = {self.temp_dir: ["*.log", "!important.log"]}

        result = is_ignored_by_git(test_file, self.temp_dir, patterns_by_dir)
        self.assertFalse(result)

    def test_is_ignored_by_git_not_ignored(self):
        """Test is_ignored_by_git with non-ignored file."""
        # Create test file
        test_file = self.temp_dir / "test.py"
        test_file.write_text("test")

        # Create patterns dict
        patterns_by_dir = {self.temp_dir: ["*.log"]}

        result = is_ignored_by_git(test_file, self.temp_dir, patterns_by_dir)
        self.assertFalse(result)

    def test_is_ignored_by_git_file_outside_repo(self):
        """Test is_ignored_by_git with file outside repository."""
        # Create file outside temp_dir
        other_dir = Path(tempfile.mkdtemp())
        test_file = other_dir / "test.log"
        test_file.write_text("test")

        try:
            patterns_by_dir = {self.temp_dir: ["*.log"]}

            result = is_ignored_by_git(test_file, self.temp_dir, patterns_by_dir)
            self.assertFalse(result)
        finally:
            test_file.unlink()
            other_dir.rmdir()


if __name__ == "__main__":
    unittest.main()
