"""Tests for main.py module - WORKING SOLUTION."""

import io
import subprocess
import sys
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from blobify.main import main


class TestMain:
    """Test cases for main function - with proper capture handling."""

    def test_main_processes_real_files(self, tmp_path):
        """Test that main actually processes files and produces output."""
        # Create real test files
        (tmp_path / "test.py").write_text("print('hello')")
        (tmp_path / "README.md").write_text("# Test Project")

        # Use file output to avoid capture issues
        output_file = tmp_path / "output.txt"
        with patch("sys.argv", ["bfy", str(tmp_path), "-o", str(output_file)]):
            main()

        # Check real output was produced
        content = output_file.read_text(encoding="utf-8")
        assert "# Blobify Text File Index" in content
        assert "test.py" in content
        assert "README.md" in content
        assert "print('hello')" in content
        assert "# Test Project" in content

    def test_main_with_output_file_simple(self, tmp_path):
        """Test that main writes to output file correctly - no capture needed."""
        # Create real test file
        (tmp_path / "test.py").write_text("def hello(): pass")
        output_file = tmp_path / "output.txt"

        # Run main with output file
        with patch("sys.argv", ["bfy", str(tmp_path), "-o", str(output_file)]):
            main()

        # Check file was created with real content
        assert output_file.exists()
        content = output_file.read_text(encoding="utf-8")
        assert "# Blobify Text File Index" in content
        assert "test.py" in content
        assert "def hello(): pass" in content

    def test_main_gitignore_behavior(self, tmp_path):
        """Test .gitignore handling with file output."""
        # Create git repo with .gitignore
        (tmp_path / ".git").mkdir()
        (tmp_path / ".gitignore").write_text("*.log\n")

        # Create files
        (tmp_path / "app.py").write_text("print('app')")
        (tmp_path / "debug.log").write_text("log content")

        # Use file output
        output_file = tmp_path / "output.txt"
        with patch("sys.argv", ["bfy", str(tmp_path), "-o", str(output_file)]):
            main()

        content = output_file.read_text(encoding="utf-8")
        # Should include non-ignored files
        assert "app.py" in content
        assert "print('app')" in content
        # Should show ignored files in index but not content
        assert "debug.log [IGNORED BY GITIGNORE]" in content
        assert "log content" not in content

    def test_main_command_line_options(self, tmp_path):
        """Test command line options work."""
        # Create test data in subdirectory
        test_data_dir = tmp_path / "test_data"
        test_data_dir.mkdir()
        (test_data_dir / "test.py").write_text("line1\nline2\nline3")

        # Test with line numbers (default)
        output_file1 = tmp_path / "with_lines.txt"
        with patch("sys.argv", ["bfy", str(test_data_dir), "-o", str(output_file1)]):
            main()

        with_lines = output_file1.read_text()
        assert "1: line1" in with_lines
        assert "2: line2" in with_lines

        # Test without line numbers
        output_file2 = tmp_path / "without_lines.txt"
        with patch("sys.argv", ["bfy", str(test_data_dir), "--no-line-numbers", "-o", str(output_file2)]):
            main()

        without_lines = output_file2.read_text()
        assert "1: line1" not in without_lines
        assert "2: line2" not in without_lines
        assert "line1\nline2\nline3" in without_lines

    def test_main_index_option(self, tmp_path):
        """Test --no-index option."""
        (tmp_path / "test.py").write_text("print('test')")

        # Test with index (default)
        output_file1 = tmp_path / "with_index.txt"
        with patch("sys.argv", ["bfy", str(tmp_path), "-o", str(output_file1)]):
            main()

        with_index = output_file1.read_text()
        assert "# FILE INDEX" in with_index

        # Test without index
        output_file2 = tmp_path / "without_index.txt"
        with patch("sys.argv", ["bfy", str(tmp_path), "--no-index", "-o", str(output_file2)]):
            main()

        without_index = output_file2.read_text()
        # The key fix: Check that the index section header is not present
        # but FILE CONTENTS header should still be there
        assert "# FILE INDEX\n" + "#" * 80 not in without_index
        assert "# FILE CONTENTS" in without_index

    @patch("subprocess.run")
    def test_clipboard_integration_windows(self, mock_subprocess, tmp_path):
        """Test clipboard functionality - mock only the subprocess call."""
        # Create real test file
        (tmp_path / "test.py").write_text("print('hello world')")

        # Mock subprocess.run to avoid actually calling clipboard
        mock_subprocess.return_value = None

        # Run with clipboard option on Windows
        with patch("sys.argv", ["bfy", str(tmp_path), "--clip"]):
            with patch("sys.platform", "win32"):
                main()

        # Verify subprocess was called correctly
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args[0][0]  # First positional argument
        assert "clip" in call_args
        assert "type" in call_args

    @patch("subprocess.Popen")
    def test_clipboard_integration_macos(self, mock_popen, tmp_path):
        """Test macOS clipboard functionality."""
        # Create real test file
        (tmp_path / "test.py").write_text("print('hello mac')")

        # Mock Popen for macOS clipboard
        mock_proc = Mock()
        mock_popen.return_value = mock_proc

        # Run with clipboard on macOS
        with patch("sys.argv", ["bfy", str(tmp_path), "--clip"]):
            with patch("sys.platform", "darwin"):
                main()

        # Verify pbcopy was called
        mock_popen.assert_called_once_with(["pbcopy"], stdin=subprocess.PIPE, text=True, encoding="utf-8")
        # Verify our content was passed to pbcopy
        mock_proc.communicate.assert_called_once()
        passed_content = mock_proc.communicate.call_args[0][0]
        assert "print('hello mac')" in passed_content

    def test_error_handling_invalid_directory(self):
        """Test main handles invalid directory gracefully."""
        with patch("sys.argv", ["bfy", "/nonexistent/directory"]):
            with pytest.raises(SystemExit):
                main()

    def test_bom_removal_with_file_output(self, tmp_path):
        """Test BOM removal using file output."""
        (tmp_path / "test.py").write_text("print('test')")
        output_file = tmp_path / "output.txt"

        # Mock format_output to return content with BOM
        with patch("blobify.main.format_output") as mock_format:
            mock_format.return_value = ("\ufeffTest output with BOM", 0, 1)

            with patch("sys.argv", ["bfy", str(tmp_path), "-o", str(output_file)]):
                main()

        # Check BOM was removed from file
        content = output_file.read_text(encoding="utf-8")
        assert not content.startswith("\ufeff")
        assert content == "Test output with BOM"

    def test_default_directory_with_blobify(self, tmp_path, monkeypatch):
        """Test main uses current directory when .blobify exists."""
        # Change to temp directory and create .blobify
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".blobify").write_text("+*.py")
        (tmp_path / "test.py").write_text("print('default dir test')")

        # Use file output to avoid capture issues
        output_file = tmp_path / "output.txt"

        # Run without directory argument
        with patch("sys.argv", ["bfy", "-o", str(output_file)]):
            main()

        content = output_file.read_text()
        assert "test.py" in content
        assert "print('default dir test')" in content

    def test_default_directory_no_blobify_fails(self, tmp_path, monkeypatch):
        """Test main fails when no directory and no .blobify file."""
        monkeypatch.chdir(tmp_path)

        with patch("sys.argv", ["bfy"]):
            with pytest.raises(SystemExit):
                main()

    def test_blobify_config_integration(self, tmp_path):
        """Test .blobify configuration works."""
        # Create git repo with .blobify config
        (tmp_path / ".git").mkdir()
        (tmp_path / ".blobify").write_text(
            """
+*.py
-*.log
"""
        )

        # Create files
        (tmp_path / "app.py").write_text("print('app')")
        (tmp_path / "README.md").write_text("# README")
        (tmp_path / "debug.log").write_text("debug log content")

        # Use file output
        output_file = tmp_path / "output.txt"
        with patch("sys.argv", ["bfy", str(tmp_path), "-o", str(output_file)]):
            main()

        content = output_file.read_text()
        # Should include .py files
        assert "app.py" in content
        assert "print('app')" in content
        # Should show other files as excluded/ignored
        assert "debug.log" in content  # In index
        # The key fix: Check that the actual file content is not included,
        # but allow the filename to appear in index and labels
        assert "debug log content" not in content  # Actual file content should not be there

    def test_context_option_integration(self, tmp_path):
        """Test --context option with real .blobify config."""
        # Create git repo with context-specific .blobify config
        (tmp_path / ".git").mkdir()
        (tmp_path / ".blobify").write_text(
            """
# Default patterns
+*.py

[docs-only]
+*.md
+docs/**
"""
        )

        # Create files
        (tmp_path / "app.py").write_text("print('app')")
        (tmp_path / "README.md").write_text("# README")

        # Test with docs-only context
        output_file = tmp_path / "output.txt"
        with patch("sys.argv", ["bfy", str(tmp_path), "--context", "docs-only", "-o", str(output_file)]):
            main()

        content = output_file.read_text()
        # Should include markdown files in docs-only context
        assert "README.md" in content
        assert "# README" in content
