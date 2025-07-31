"""Tests for git_utils.py module."""

import subprocess
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from blobify.git_utils import (
    compile_gitignore_patterns,
    get_gitignore_patterns,
    gitignore_to_regex,
    is_git_repository,
    is_ignored_by_git,
    read_gitignore_file,
)


class TestGitUtils:
    """Test cases for git utilities."""

    def test_is_git_repository_found(self, temp_dir):
        """Test is_git_repository when .git directory exists."""
        git_dir = temp_dir / ".git"
        git_dir.mkdir()

        result = is_git_repository(temp_dir)
        assert result == temp_dir

    def test_is_git_repository_not_found(self, temp_dir):
        """Test is_git_repository when no .git directory exists."""
        result = is_git_repository(temp_dir)
        assert result is None

    def test_is_git_repository_parent_directory(self, temp_dir):
        """Test is_git_repository finds .git in parent directory."""
        git_dir = temp_dir / ".git"
        git_dir.mkdir()
        sub_dir = temp_dir / "subdir"
        sub_dir.mkdir()

        result = is_git_repository(sub_dir)
        assert result == temp_dir

    def test_read_gitignore_file(self, temp_dir):
        """Test reading .gitignore file patterns."""
        gitignore = temp_dir / ".gitignore"
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
        assert patterns == ["*.log", "temp/", "build/"]

    def test_read_gitignore_file_nonexistent(self, temp_dir):
        """Test reading nonexistent .gitignore file."""
        gitignore = temp_dir / ".gitignore"
        patterns = read_gitignore_file(gitignore)
        assert patterns == []

    def test_gitignore_to_regex_simple(self):
        """Test gitignore pattern to regex conversion."""
        regex = gitignore_to_regex("*.log")
        assert regex == "^([^/]*\\.log|.*/[^/]*\\.log)$"

    def test_gitignore_to_regex_directory(self):
        """Test gitignore directory pattern to regex conversion."""
        regex = gitignore_to_regex("build/")
        expected = "^(build|build/.*|.*/build|.*/build/.*)$"
        assert regex == expected

    def test_gitignore_to_regex_root_relative(self):
        """Test gitignore root-relative pattern to regex conversion."""
        regex = gitignore_to_regex("/build")
        assert regex == "^build$"

    def test_gitignore_to_regex_doublestar(self):
        """Test gitignore doublestar pattern to regex conversion."""
        regex = gitignore_to_regex("docs/**")
        expected = "^(docs/.*|.*/docs/.*)$"
        assert regex == expected

    def test_compile_gitignore_patterns(self):
        """Test compiling gitignore patterns to regex."""
        patterns = ["*.log", "!important.log", "build/"]
        compiled = compile_gitignore_patterns(patterns)

        assert len(compiled) == 3
        assert compiled[0][1] is False  # Not negation
        assert compiled[1][1] is True  # Is negation
        assert compiled[2][1] is False  # Not negation

    def test_compile_gitignore_patterns_invalid_regex(self):
        """Test compiling patterns with invalid regex."""
        patterns = ["[invalid", "*.log"]
        compiled = compile_gitignore_patterns(patterns)

        # Should skip invalid pattern
        assert len(compiled) == 1

    @patch("blobify.git_utils.subprocess.run")
    def test_get_gitignore_patterns_with_global(self, mock_run, temp_dir):
        """Test getting gitignore patterns including global gitignore."""
        # Setup git directory
        git_dir = temp_dir / ".git"
        git_dir.mkdir()

        # Setup global gitignore
        global_gitignore = temp_dir / "global.gitignore"
        global_gitignore.write_text("*.tmp\n")

        # Setup repo gitignore
        repo_gitignore = temp_dir / ".gitignore"
        repo_gitignore.write_text("*.log\n")

        # Mock git config command
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = str(global_gitignore)
        mock_run.return_value = mock_result

        patterns_by_dir = get_gitignore_patterns(temp_dir)

        # Should include both global and repo patterns
        assert temp_dir in patterns_by_dir
        patterns = patterns_by_dir[temp_dir]
        assert "*.tmp" in patterns
        assert "*.log" in patterns

    @patch("blobify.git_utils.subprocess.run")
    def test_get_gitignore_patterns_no_global(self, mock_run, temp_dir):
        """Test getting gitignore patterns without global gitignore."""
        # Setup git directory
        git_dir = temp_dir / ".git"
        git_dir.mkdir()

        # Setup repo gitignore
        repo_gitignore = temp_dir / ".gitignore"
        repo_gitignore.write_text("*.log\n")

        # Mock git config command (no global gitignore)
        mock_result = Mock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        patterns_by_dir = get_gitignore_patterns(temp_dir)

        # Should only include repo patterns
        assert temp_dir in patterns_by_dir
        patterns = patterns_by_dir[temp_dir]
        assert patterns == ["*.log"]

    def test_get_gitignore_patterns_git_error(self, temp_dir):
        """Test getting gitignore patterns when git command fails."""
        # Setup git directory
        git_dir = temp_dir / ".git"
        git_dir.mkdir()

        # Setup repo gitignore
        repo_gitignore = temp_dir / ".gitignore"
        repo_gitignore.write_text("*.log\n")

        # Test that function handles subprocess errors gracefully
        # by patching subprocess to raise various exceptions
        with patch("blobify.git_utils.subprocess.run") as mock_run:
            mock_run.side_effect = [
                subprocess.TimeoutExpired("git", 5),  # First call times out
                subprocess.SubprocessError("Git error"),  # Second call fails
                FileNotFoundError("git command not found"),  # Third call can't find git
            ]

            # Should still work despite git errors
            patterns_by_dir = get_gitignore_patterns(temp_dir)

        # Should still get repo patterns despite git error
        assert temp_dir in patterns_by_dir
        patterns = patterns_by_dir[temp_dir]
        assert patterns == ["*.log"]

    def test_is_ignored_by_git_simple(self, temp_dir):
        """Test is_ignored_by_git with simple patterns."""
        # Create test file
        test_file = temp_dir / "test.log"
        test_file.write_text("test")

        # Create patterns dict
        patterns_by_dir = {temp_dir: ["*.log"]}

        result = is_ignored_by_git(test_file, temp_dir, patterns_by_dir)
        assert result is True

    def test_is_ignored_by_git_negation(self, temp_dir):
        """Test is_ignored_by_git with negation patterns."""
        # Create test file
        test_file = temp_dir / "important.log"
        test_file.write_text("test")

        # Create patterns dict with negation
        patterns_by_dir = {temp_dir: ["*.log", "!important.log"]}

        result = is_ignored_by_git(test_file, temp_dir, patterns_by_dir)
        assert result is False

    def test_is_ignored_by_git_not_ignored(self, temp_dir):
        """Test is_ignored_by_git with non-ignored file."""
        # Create test file
        test_file = temp_dir / "test.py"
        test_file.write_text("test")

        # Create patterns dict
        patterns_by_dir = {temp_dir: ["*.log"]}

        result = is_ignored_by_git(test_file, temp_dir, patterns_by_dir)
        assert result is False

    def test_is_ignored_by_git_file_outside_repo(self, temp_dir):
        """Test is_ignored_by_git with file outside repository."""
        # Create file outside temp_dir
        other_dir = Path(tempfile.mkdtemp())
        test_file = other_dir / "test.log"
        test_file.write_text("test")

        try:
            patterns_by_dir = {temp_dir: ["*.log"]}

            result = is_ignored_by_git(test_file, temp_dir, patterns_by_dir)
            assert result is False
        finally:
            test_file.unlink()
            other_dir.rmdir()
