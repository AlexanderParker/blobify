"""Tests for main.py module."""

import pathlib
import sys
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import Mock, patch

from blobify.main import main


@patch("sys.platform", "linux")  # Avoid Windows Unicode wrapper in all tests
class TestMain(unittest.TestCase):
    """Test cases for main function."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.original_argv = sys.argv.copy()
        self.original_cwd = Path.cwd()
        # Change to temp directory for all tests
        import os

        os.chdir(self.temp_dir)
        # Output temp directory for visibility (using stderr so it doesn't conflict with stdout mocks)
        print(f"\nTest temp directory: {self.temp_dir}", file=sys.stderr)

    def tearDown(self):
        """Clean up test fixtures."""
        import os

        # Change back to original directory
        os.chdir(self.original_cwd)
        sys.argv = self.original_argv
        # Clean up temp directory
        for file in self.temp_dir.rglob("*"):
            if file.is_file():
                file.unlink()
        for dir in sorted(self.temp_dir.rglob("*"), reverse=True):
            if dir.is_dir():
                dir.rmdir()
        self.temp_dir.rmdir()
        print(f"Cleaned up temp directory: {self.temp_dir}", file=sys.stderr)

    @patch("blobify.main.scan_files")
    @patch("blobify.main.format_output")
    @patch("blobify.main.is_git_repository")
    @patch("blobify.main.read_blobify_config")
    @patch("sys.stdout", new_callable=StringIO)
    def test_main_basic_usage(
        self, mock_stdout, mock_read_config, mock_is_git, mock_format, mock_scan
    ):
        """Test basic main function usage."""
        sys.argv = ["bfy", str(self.temp_dir)]

        mock_is_git.return_value = None
        mock_read_config.return_value = ([], [], [])
        mock_scan.return_value = {"included_files": []}
        mock_format.return_value = ("Test output", 0, 1)

        main()

        output = mock_stdout.getvalue()
        self.assertEqual(output, "Test output")

    @patch("blobify.main.scan_files")
    @patch("blobify.main.format_output")
    @patch("blobify.main.is_git_repository")
    @patch("blobify.main.read_blobify_config")
    def test_main_output_file(
        self, mock_read_config, mock_is_git, mock_format, mock_scan
    ):
        """Test main function with output file."""
        output_file = self.temp_dir / "output.txt"
        sys.argv = ["bfy", str(self.temp_dir), "-o", str(output_file)]

        mock_is_git.return_value = None
        mock_read_config.return_value = ([], [], [])
        mock_scan.return_value = {"included_files": []}
        mock_format.return_value = ("Test output", 0, 1)

        main()

        self.assertTrue(output_file.exists())
        self.assertEqual(output_file.read_text(encoding="utf-8"), "Test output")

    @patch("blobify.main.scan_files")
    @patch("blobify.main.format_output")
    @patch("blobify.main.is_git_repository")
    @patch("blobify.main.read_blobify_config")
    @patch("blobify.main.subprocess.run")
    def test_main_clipboard_windows(
        self, mock_subprocess, mock_read_config, mock_is_git, mock_format, mock_scan
    ):
        """Test main function with clipboard on Windows."""
        sys.argv = ["bfy", str(self.temp_dir), "--clip"]

        mock_is_git.return_value = None
        mock_read_config.return_value = ([], [], [])
        mock_scan.return_value = {"included_files": []}
        mock_format.return_value = ("Test output", 0, 1)

        with patch("sys.platform", "win32"):
            main()

        mock_subprocess.assert_called_once()

    @patch("blobify.main.scan_files")
    @patch("blobify.main.format_output")
    @patch("blobify.main.is_git_repository")
    @patch("blobify.main.read_blobify_config")
    @patch("blobify.main.subprocess.Popen")
    def test_main_clipboard_macos(
        self, mock_popen, mock_read_config, mock_is_git, mock_format, mock_scan
    ):
        """Test main function with clipboard on macOS."""
        sys.argv = ["bfy", str(self.temp_dir), "--clip"]

        mock_is_git.return_value = None
        mock_read_config.return_value = ([], [], [])
        mock_scan.return_value = {"included_files": []}
        mock_format.return_value = ("Test output", 0, 1)

        mock_proc = Mock()
        mock_popen.return_value = mock_proc

        with patch("sys.platform", "darwin"):
            main()

        mock_popen.assert_called_once_with(
            ["pbcopy"], stdin=unittest.mock.ANY, text=True, encoding="utf-8"
        )
        mock_proc.communicate.assert_called_once_with("Test output")

    @patch("blobify.main.scan_files")
    @patch("blobify.main.format_output")
    @patch("blobify.main.is_git_repository")
    @patch("blobify.main.read_blobify_config")
    @patch("blobify.main.subprocess.Popen")
    def test_main_clipboard_linux(
        self, mock_popen, mock_read_config, mock_is_git, mock_format, mock_scan
    ):
        """Test main function with clipboard on Linux."""
        sys.argv = ["bfy", str(self.temp_dir), "--clip"]

        mock_is_git.return_value = None
        mock_read_config.return_value = ([], [], [])
        mock_scan.return_value = {"included_files": []}
        mock_format.return_value = ("Test output", 0, 1)

        mock_proc = Mock()
        mock_popen.return_value = mock_proc

        with patch("sys.platform", "linux"):
            main()

        mock_popen.assert_called_once_with(
            ["xclip", "-selection", "clipboard"],
            stdin=unittest.mock.ANY,
            text=True,
            encoding="utf-8",
        )
        mock_proc.communicate.assert_called_once_with("Test output")

    @patch("blobify.main.scan_files")
    @patch("blobify.main.format_output")
    @patch("blobify.main.is_git_repository")
    @patch("blobify.main.read_blobify_config")
    @patch("blobify.main.subprocess.run", side_effect=Exception("Clipboard error"))
    def test_main_clipboard_error(
        self, mock_subprocess, mock_read_config, mock_is_git, mock_format, mock_scan
    ):
        """Test main function with clipboard error."""
        sys.argv = ["bfy", str(self.temp_dir), "--clip"]

        mock_is_git.return_value = None
        mock_read_config.return_value = ([], [], [])
        mock_scan.return_value = {"included_files": []}
        mock_format.return_value = ("Test output", 0, 1)

        with patch("sys.platform", "win32"):
            main()  # Should not raise exception

    def test_main_no_directory_no_blobify(self):
        """Test main function with no directory and no .blobify file."""
        sys.argv = ["bfy"]

        with patch("sys.exit") as mock_exit:
            with patch("argparse.ArgumentParser.error") as mock_error:
                mock_error.side_effect = SystemExit(2)
                try:
                    main()
                except SystemExit:
                    pass
                mock_error.assert_called_once()

    @patch("blobify.main.scan_files")
    @patch("blobify.main.format_output")
    @patch("blobify.main.is_git_repository")
    @patch("blobify.main.read_blobify_config")
    def test_main_no_directory_with_blobify(
        self, mock_read_config, mock_is_git, mock_format, mock_scan
    ):
        """Test main function with no directory but .blobify file exists."""
        # Create .blobify file in current temp directory (safe)
        blobify_file = Path(".blobify")
        blobify_file.write_text("+*.py")

        sys.argv = ["bfy"]

        mock_is_git.return_value = None
        mock_read_config.return_value = ([], [], [])
        mock_scan.return_value = {"included_files": []}
        mock_format.return_value = ("Test output", 0, 1)

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            main()

        output = mock_stdout.getvalue()
        self.assertEqual(output, "Test output")

    @patch("blobify.main.scan_files")
    @patch("blobify.main.format_output")
    @patch("blobify.main.is_git_repository")
    @patch("blobify.main.read_blobify_config")
    @patch("blobify.main.apply_default_switches")
    def test_main_with_default_switches(
        self, mock_apply_switches, mock_read_config, mock_is_git, mock_format, mock_scan
    ):
        """Test main function with default switches from .blobify."""
        sys.argv = ["bfy", str(self.temp_dir)]

        mock_is_git.return_value = self.temp_dir
        mock_read_config.return_value = ([], [], ["debug", "clip"])
        mock_scan.return_value = {"included_files": []}
        mock_format.return_value = ("Test output", 0, 1)

        # Mock apply_default_switches to return modified args
        def mock_apply(args, switches, debug):
            args.debug = True
            args.clip = True
            return args

        mock_apply_switches.side_effect = mock_apply

        with patch("blobify.main.subprocess.run"):  # Mock clipboard
            main()

        mock_apply_switches.assert_called_once()

    @patch("blobify.main.scan_files")
    @patch("blobify.main.format_output")
    @patch("blobify.main.is_git_repository")
    @patch("blobify.main.read_blobify_config")
    def test_main_with_context(
        self, mock_read_config, mock_is_git, mock_format, mock_scan
    ):
        """Test main function with context parameter."""
        sys.argv = ["bfy", str(self.temp_dir), "-x", "test-context"]

        mock_is_git.return_value = self.temp_dir
        mock_read_config.return_value = ([], [], [])
        mock_scan.return_value = {"included_files": []}
        mock_format.return_value = ("Test output", 0, 1)

        with patch("sys.stdout", new_callable=StringIO):
            main()

        # Check that scan_files was called with context
        mock_scan.assert_called_once_with(
            unittest.mock.ANY, context="test-context", debug=False
        )

    @patch("blobify.main.scan_files")
    @patch("blobify.main.format_output")
    @patch("blobify.main.is_git_repository")
    @patch("blobify.main.read_blobify_config")
    def test_main_debug_mode(
        self, mock_read_config, mock_is_git, mock_format, mock_scan
    ):
        """Test main function with debug mode."""
        sys.argv = ["bfy", str(self.temp_dir), "--debug"]

        mock_is_git.return_value = None
        mock_read_config.return_value = ([], [], [])
        mock_scan.return_value = {"included_files": []}
        mock_format.return_value = ("Test output", 0, 1)

        with patch("sys.stdout", new_callable=StringIO):
            main()

        # Check that scan_files was called with debug=True
        mock_scan.assert_called_once_with(unittest.mock.ANY, context=None, debug=True)

    @patch("blobify.main.scan_files")
    @patch("blobify.main.format_output")
    @patch("blobify.main.is_git_repository")
    @patch("blobify.main.read_blobify_config")
    def test_main_no_line_numbers(
        self, mock_read_config, mock_is_git, mock_format, mock_scan
    ):
        """Test main function with no line numbers option."""
        sys.argv = ["bfy", str(self.temp_dir), "--no-line-numbers"]

        mock_is_git.return_value = None
        mock_read_config.return_value = ([], [], [])
        mock_scan.return_value = {"included_files": []}
        mock_format.return_value = ("Test output", 0, 1)

        with patch("sys.stdout", new_callable=StringIO):
            main()

        # Check that format_output was called with include_line_numbers=False
        mock_format.assert_called_once()
        call_args = mock_format.call_args
        self.assertFalse(call_args[1]["include_line_numbers"])

    @patch("blobify.main.scan_files")
    @patch("blobify.main.format_output")
    @patch("blobify.main.is_git_repository")
    @patch("blobify.main.read_blobify_config")
    def test_main_no_index(self, mock_read_config, mock_is_git, mock_format, mock_scan):
        """Test main function with no index option."""
        sys.argv = ["bfy", str(self.temp_dir), "--no-index"]

        mock_is_git.return_value = None
        mock_read_config.return_value = ([], [], [])
        mock_scan.return_value = {"included_files": []}
        mock_format.return_value = ("Test output", 0, 1)

        with patch("sys.stdout", new_callable=StringIO):
            main()

        # Check that format_output was called with include_index=False
        mock_format.assert_called_once()
        call_args = mock_format.call_args
        self.assertFalse(call_args[1]["include_index"])

    @patch("blobify.main.scan_files")
    @patch("blobify.main.format_output")
    @patch("blobify.main.is_git_repository")
    @patch("blobify.main.read_blobify_config")
    def test_main_noclean(self, mock_read_config, mock_is_git, mock_format, mock_scan):
        """Test main function with noclean option."""
        sys.argv = ["bfy", str(self.temp_dir), "--noclean"]

        mock_is_git.return_value = None
        mock_read_config.return_value = ([], [], [])
        mock_scan.return_value = {"included_files": []}
        mock_format.return_value = ("Test output", 0, 1)

        with patch("sys.stdout", new_callable=StringIO):
            main()

        # Check that format_output was called with scrub_data=False
        mock_format.assert_called_once()
        call_args = mock_format.call_args
        # scrub_data should be False (not args.noclean)
        self.assertFalse(call_args[0][3])  # Third positional argument is scrub_data

    @patch("blobify.main.scan_files", side_effect=Exception("Test error"))
    def test_main_exception_handling(self, mock_scan):
        """Test main function exception handling."""
        sys.argv = ["bfy", str(self.temp_dir)]

        with patch("sys.exit") as mock_exit:
            main()
            mock_exit.assert_called_once_with(1)

    @patch("blobify.main.scan_files")
    @patch("blobify.main.format_output")
    @patch("blobify.main.is_git_repository")
    @patch("blobify.main.read_blobify_config")
    def test_main_bom_removal(
        self, mock_read_config, mock_is_git, mock_format, mock_scan
    ):
        """Test main function removes BOM from output."""
        sys.argv = ["bfy", str(self.temp_dir)]

        mock_is_git.return_value = None
        mock_read_config.return_value = ([], [], [])
        mock_scan.return_value = {"included_files": []}
        mock_format.return_value = ("\ufeffTest output with BOM", 0, 1)

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            main()

        output = mock_stdout.getvalue()
        self.assertEqual(output, "Test output with BOM")
        self.assertFalse(output.startswith("\ufeff"))


if __name__ == "__main__":
    unittest.main()
