"""Tests for main.py module."""

import sys
import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from blobify.main import main


@patch("sys.platform", "linux")  # Avoid Windows Unicode wrapper in all tests
class TestMain:
    """Test cases for main function."""

    @pytest.fixture
    def test_temp_dir(self):
        """Create a test temp directory."""
        temp_dir = Path(tempfile.mkdtemp())
        original_cwd = Path.cwd()
        import os

        os.chdir(temp_dir)
        yield temp_dir
        os.chdir(original_cwd)
        # Cleanup
        for file in temp_dir.rglob("*"):
            if file.is_file():
                file.unlink()
        for dir in sorted(temp_dir.rglob("*"), reverse=True):
            if dir.is_dir():
                dir.rmdir()
        temp_dir.rmdir()

    @patch("blobify.main.scan_files")
    @patch("blobify.main.format_output")
    @patch("blobify.main.is_git_repository")
    @patch("blobify.main.read_blobify_config")
    @patch("sys.stdout", new_callable=StringIO)
    @patch("sys.argv", ["bfy", "test_dir"])
    def test_main_basic_usage(self, mock_stdout, mock_read_config, mock_is_git, mock_format, mock_scan, test_temp_dir):
        """Test basic main function usage."""
        # Change sys.argv to use test_temp_dir
        with patch("sys.argv", ["bfy", str(test_temp_dir)]):
            mock_is_git.return_value = None
            mock_read_config.return_value = ([], [], [])
            mock_scan.return_value = {"included_files": []}
            mock_format.return_value = ("Test output", 0, 1)

            main()

            output = mock_stdout.getvalue()
            assert output == "Test output"

    @patch("blobify.main.scan_files")
    @patch("blobify.main.format_output")
    @patch("blobify.main.is_git_repository")
    @patch("blobify.main.read_blobify_config")
    @patch("sys.argv", ["bfy", "test_dir", "-o", "output.txt"])
    def test_main_output_file(self, mock_read_config, mock_is_git, mock_format, mock_scan, test_temp_dir):
        """Test main function with output file."""
        output_file = test_temp_dir / "output.txt"
        with patch("sys.argv", ["bfy", str(test_temp_dir), "-o", str(output_file)]):
            mock_is_git.return_value = None
            mock_read_config.return_value = ([], [], [])
            mock_scan.return_value = {"included_files": []}
            mock_format.return_value = ("Test output", 0, 1)

            main()

            assert output_file.exists()
            assert output_file.read_text(encoding="utf-8") == "Test output"

    @patch("blobify.main.scan_files")
    @patch("blobify.main.format_output")
    @patch("blobify.main.is_git_repository")
    @patch("blobify.main.read_blobify_config")
    @patch("blobify.main.subprocess.run")
    @patch("sys.argv", ["bfy", "test_dir", "--clip"])
    def test_main_clipboard_windows(
        self, mock_subprocess, mock_read_config, mock_is_git, mock_format, mock_scan, test_temp_dir
    ):
        """Test main function with clipboard on Windows."""
        with patch("sys.argv", ["bfy", str(test_temp_dir), "--clip"]):
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
    @patch("sys.argv", ["bfy", "test_dir", "--clip"])
    def test_main_clipboard_macos(
        self, mock_popen, mock_read_config, mock_is_git, mock_format, mock_scan, test_temp_dir
    ):
        """Test main function with clipboard on macOS."""
        with patch("sys.argv", ["bfy", str(test_temp_dir), "--clip"]):
            mock_is_git.return_value = None
            mock_read_config.return_value = ([], [], [])
            mock_scan.return_value = {"included_files": []}
            mock_format.return_value = ("Test output", 0, 1)

            mock_proc = Mock()
            mock_popen.return_value = mock_proc

            with patch("sys.platform", "darwin"):
                main()

            mock_popen.assert_called_once_with(
                ["pbcopy"], stdin=pytest.importorskip("subprocess").PIPE, text=True, encoding="utf-8"
            )
            mock_proc.communicate.assert_called_once_with("Test output")

    @patch("blobify.main.scan_files")
    @patch("blobify.main.format_output")
    @patch("blobify.main.is_git_repository")
    @patch("blobify.main.read_blobify_config")
    @patch("blobify.main.subprocess.Popen")
    @patch("sys.argv", ["bfy", "test_dir", "--clip"])
    def test_main_clipboard_linux(
        self, mock_popen, mock_read_config, mock_is_git, mock_format, mock_scan, test_temp_dir
    ):
        """Test main function with clipboard on Linux."""
        with patch("sys.argv", ["bfy", str(test_temp_dir), "--clip"]):
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
                stdin=pytest.importorskip("subprocess").PIPE,
                text=True,
                encoding="utf-8",
            )
            mock_proc.communicate.assert_called_once_with("Test output")

    @patch("blobify.main.scan_files")
    @patch("blobify.main.format_output")
    @patch("blobify.main.is_git_repository")
    @patch("blobify.main.read_blobify_config")
    @patch("blobify.main.subprocess.run", side_effect=Exception("Clipboard error"))
    @patch("sys.argv", ["bfy", "test_dir", "--clip"])
    def test_main_clipboard_error(
        self, mock_subprocess, mock_read_config, mock_is_git, mock_format, mock_scan, test_temp_dir
    ):
        """Test main function with clipboard error."""
        with patch("sys.argv", ["bfy", str(test_temp_dir), "--clip"]):
            mock_is_git.return_value = None
            mock_read_config.return_value = ([], [], [])
            mock_scan.return_value = {"included_files": []}
            mock_format.return_value = ("Test output", 0, 1)

            with patch("sys.platform", "win32"):
                main()  # Should not raise exception

    @patch("sys.argv", ["bfy"])
    def test_main_no_directory_no_blobify(self, test_temp_dir):
        """Test main function with no directory and no .blobify file."""
        with patch("sys.exit") as mock_exit:
            with patch("argparse.ArgumentParser.error") as mock_error:
                mock_error.side_effect = SystemExit(2)
                with pytest.raises(SystemExit):
                    main()
                mock_error.assert_called_once()

    @patch("blobify.main.scan_files")
    @patch("blobify.main.format_output")
    @patch("blobify.main.is_git_repository")
    @patch("blobify.main.read_blobify_config")
    @patch("sys.argv", ["bfy"])
    def test_main_no_directory_with_blobify(self, mock_read_config, mock_is_git, mock_format, mock_scan, test_temp_dir):
        """Test main function with no directory but .blobify file exists."""
        # Create .blobify file in current temp directory
        blobify_file = Path(".blobify")
        blobify_file.write_text("+*.py")

        mock_is_git.return_value = None
        mock_read_config.return_value = ([], [], [])
        mock_scan.return_value = {"included_files": []}
        mock_format.return_value = ("Test output", 0, 1)

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            main()

        output = mock_stdout.getvalue()
        assert output == "Test output"

    @patch("blobify.main.scan_files")
    @patch("blobify.main.format_output")
    @patch("blobify.main.is_git_repository")
    @patch("blobify.main.read_blobify_config")
    @patch("blobify.main.apply_default_switches")
    @patch("blobify.main.subprocess.run")
    @patch("blobify.main.tempfile.NamedTemporaryFile")
    @patch("blobify.main.os.unlink")
    @patch("blobify.main.io.TextIOWrapper")
    @patch("sys.argv", ["bfy", "test_dir"])
    def test_main_with_default_switches(
        self,
        mock_textiowrapper,
        mock_unlink,
        mock_tempfile,
        mock_subprocess,
        mock_apply_switches,
        mock_read_config,
        mock_is_git,
        mock_format,
        mock_scan,
        test_temp_dir,
    ):
        """Test main function with default switches from .blobify."""
        with patch("sys.argv", ["bfy", str(test_temp_dir)]):
            mock_is_git.return_value = test_temp_dir
            mock_read_config.return_value = ([], [], ["debug", "clip"])
            mock_scan.return_value = {"included_files": []}
            mock_format.return_value = ("Test output", 0, 1)

            # Mock TextIOWrapper to return the original stdout
            mock_textiowrapper.return_value = sys.stdout

            # Mock apply_default_switches to return modified args
            def mock_apply(args, switches, debug):
                args.debug = True
                args.clip = True
                return args

            mock_apply_switches.side_effect = mock_apply

            # Mock temp file creation for Windows clipboard
            mock_temp_context = Mock()
            mock_temp_context.__enter__ = Mock()
            mock_temp_context.__exit__ = Mock(return_value=None)
            mock_temp_file = Mock()
            mock_temp_file.name = "mocked_temp_file.txt"
            mock_temp_context.__enter__.return_value = mock_temp_file
            mock_tempfile.return_value = mock_temp_context

            # Mock the subprocess call for clipboard
            mock_subprocess.return_value = None

            with patch("sys.platform", "win32"):
                main()

            mock_apply_switches.assert_called_once()
            # Verify subprocess was called for clipboard
            mock_subprocess.assert_called_once_with('type "mocked_temp_file.txt" | clip', shell=True, check=True)

    @patch("blobify.main.scan_files")
    @patch("blobify.main.format_output")
    @patch("blobify.main.is_git_repository")
    @patch("blobify.main.read_blobify_config")
    @patch("sys.argv", ["bfy", "test_dir", "-x", "test-context"])
    def test_main_with_context(self, mock_read_config, mock_is_git, mock_format, mock_scan, test_temp_dir):
        """Test main function with context parameter."""
        with patch("sys.argv", ["bfy", str(test_temp_dir), "-x", "test-context"]):
            mock_is_git.return_value = test_temp_dir
            mock_read_config.return_value = ([], [], [])
            mock_scan.return_value = {"included_files": []}
            mock_format.return_value = ("Test output", 0, 1)

            with patch("sys.stdout", new_callable=StringIO):
                main()

            # Check that scan_files was called with context
            mock_scan.assert_called_once_with(
                pytest.importorskip("unittest.mock").ANY, context="test-context", debug=False
            )

    @patch("blobify.main.scan_files")
    @patch("blobify.main.format_output")
    @patch("blobify.main.is_git_repository")
    @patch("blobify.main.read_blobify_config")
    @patch("sys.argv", ["bfy", "test_dir", "--debug"])
    def test_main_debug_mode(self, mock_read_config, mock_is_git, mock_format, mock_scan, test_temp_dir):
        """Test main function with debug mode."""
        with patch("sys.argv", ["bfy", str(test_temp_dir), "--debug"]):
            mock_is_git.return_value = None
            mock_read_config.return_value = ([], [], [])
            mock_scan.return_value = {"included_files": []}
            mock_format.return_value = ("Test output", 0, 1)

            with patch("sys.stdout", new_callable=StringIO):
                main()

            # Check that scan_files was called with debug=True
            mock_scan.assert_called_once_with(pytest.importorskip("unittest.mock").ANY, context=None, debug=True)

    @patch("blobify.main.scan_files")
    @patch("blobify.main.format_output")
    @patch("blobify.main.is_git_repository")
    @patch("blobify.main.read_blobify_config")
    @patch("sys.argv", ["bfy", "test_dir", "--no-line-numbers"])
    def test_main_no_line_numbers(self, mock_read_config, mock_is_git, mock_format, mock_scan, test_temp_dir):
        """Test main function with no line numbers option."""
        with patch("sys.argv", ["bfy", str(test_temp_dir), "--no-line-numbers"]):
            mock_is_git.return_value = None
            mock_read_config.return_value = ([], [], [])
            mock_scan.return_value = {"included_files": []}
            mock_format.return_value = ("Test output", 0, 1)

            with patch("sys.stdout", new_callable=StringIO):
                main()

            # Check that format_output was called with include_line_numbers=False
            mock_format.assert_called_once()
            call_args = mock_format.call_args
            assert call_args[1]["include_line_numbers"] is False

    @patch("blobify.main.scan_files")
    @patch("blobify.main.format_output")
    @patch("blobify.main.is_git_repository")
    @patch("blobify.main.read_blobify_config")
    @patch("sys.argv", ["bfy", "test_dir", "--no-index"])
    def test_main_no_index(self, mock_read_config, mock_is_git, mock_format, mock_scan, test_temp_dir):
        """Test main function with no index option."""
        with patch("sys.argv", ["bfy", str(test_temp_dir), "--no-index"]):
            mock_is_git.return_value = None
            mock_read_config.return_value = ([], [], [])
            mock_scan.return_value = {"included_files": []}
            mock_format.return_value = ("Test output", 0, 1)

            with patch("sys.stdout", new_callable=StringIO):
                main()

            # Check that format_output was called with include_index=False
            mock_format.assert_called_once()
            call_args = mock_format.call_args
            assert call_args[1]["include_index"] is False

    @patch("blobify.main.scan_files")
    @patch("blobify.main.format_output")
    @patch("blobify.main.is_git_repository")
    @patch("blobify.main.read_blobify_config")
    @patch("sys.argv", ["bfy", "test_dir", "--noclean"])
    def test_main_noclean(self, mock_read_config, mock_is_git, mock_format, mock_scan, test_temp_dir):
        """Test main function with noclean option."""
        with patch("sys.argv", ["bfy", str(test_temp_dir), "--noclean"]):
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
            assert call_args[0][3] is False  # Third positional argument is scrub_data

    @patch("blobify.main.scan_files", side_effect=Exception("Test error"))
    @patch("sys.argv", ["bfy", "test_dir"])
    def test_main_exception_handling(self, mock_scan, test_temp_dir):
        """Test main function exception handling."""
        with patch("sys.argv", ["bfy", str(test_temp_dir)]):
            with patch("sys.exit") as mock_exit:
                main()
                mock_exit.assert_called_once_with(1)

    @patch("blobify.main.scan_files")
    @patch("blobify.main.format_output")
    @patch("blobify.main.is_git_repository")
    @patch("blobify.main.read_blobify_config")
    @patch("sys.argv", ["bfy", "test_dir"])
    def test_main_bom_removal(self, mock_read_config, mock_is_git, mock_format, mock_scan, test_temp_dir):
        """Test main function removes BOM from output."""
        with patch("sys.argv", ["bfy", str(test_temp_dir)]):
            mock_is_git.return_value = None
            mock_read_config.return_value = ([], [], [])
            mock_scan.return_value = {"included_files": []}
            mock_format.return_value = ("\ufeffTest output with BOM", 0, 1)

            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                main()

            output = mock_stdout.getvalue()
            assert output == "Test output with BOM"
            assert not output.startswith("\ufeff")
