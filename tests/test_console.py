"""Tests for console.py module."""

from unittest.mock import patch

from blobify.console import (
    print_debug,
    print_error,
    print_file_processing,
    print_phase,
    print_status,
    print_success,
    print_warning,
)


class TestConsoleOutput:
    """Test cases for console output functions."""

    @patch("blobify.console.console", None)
    def test_print_status_no_rich(self, capsys):
        """Test print_status without rich console."""
        print_status("Test message")
        captured = capsys.readouterr()
        assert "Test message" in captured.err

    @patch("blobify.console.console")
    def test_print_status_with_rich(self, mock_console):
        """Test print_status with rich console."""
        print_status("Test message", "bold")
        mock_console.print.assert_called_once_with("Test message", style="bold")

    @patch("blobify.console.console", None)
    def test_print_debug_no_rich(self, capsys):
        """Test print_debug without rich console."""
        print_debug("Debug message")
        captured = capsys.readouterr()
        assert "Debug message" in captured.err

    @patch("blobify.console.console")
    def test_print_debug_with_rich(self, mock_console):
        """Test print_debug with rich console."""
        print_debug("Debug message")
        mock_console.print.assert_called_once_with("Debug message", style="dim cyan")

    @patch("blobify.console.console", None)
    def test_print_phase_no_rich(self, capsys):
        """Test print_phase without rich console."""
        print_phase("test phase")
        captured = capsys.readouterr()
        assert "=== TEST PHASE ===" in captured.err

    @patch("blobify.console.console")
    def test_print_phase_with_rich(self, mock_console):
        """Test print_phase with rich console."""
        print_phase("test phase")
        # The actual characters used are em dash (—) which is \u2500
        expected = "\n[bold magenta]──── TEST PHASE ────[/bold magenta]"
        mock_console.print.assert_called_once_with(expected)

    @patch("blobify.console.console", None)
    def test_print_warning_no_rich(self, capsys):
        """Test print_warning without rich console."""
        print_warning("Warning message")
        captured = capsys.readouterr()
        assert "Warning message" in captured.err

    @patch("blobify.console.console")
    def test_print_warning_with_rich(self, mock_console):
        """Test print_warning with rich console."""
        print_warning("Warning message")
        mock_console.print.assert_called_once_with("Warning message", style="yellow")

    @patch("blobify.console.console", None)
    def test_print_error_no_rich(self, capsys):
        """Test print_error without rich console."""
        print_error("Error message")
        captured = capsys.readouterr()
        assert "Error message" in captured.err

    @patch("blobify.console.console")
    def test_print_error_with_rich(self, mock_console):
        """Test print_error with rich console."""
        print_error("Error message")
        mock_console.print.assert_called_once_with("Error message", style="bold red")

    @patch("blobify.console.console", None)
    def test_print_success_no_rich(self, capsys):
        """Test print_success without rich console."""
        print_success("Success message")
        captured = capsys.readouterr()
        assert "Success message" in captured.err

    @patch("blobify.console.console")
    def test_print_success_with_rich(self, mock_console):
        """Test print_success with rich console."""
        print_success("Success message")
        mock_console.print.assert_called_once_with("Success message", style="green")

    @patch("blobify.console.console", None)
    def test_print_file_processing_no_rich(self, capsys):
        """Test print_file_processing without rich console."""
        print_file_processing("Processing file")
        captured = capsys.readouterr()
        assert "Processing file" in captured.err

    @patch("blobify.console.console")
    def test_print_file_processing_with_rich(self, mock_console):
        """Test print_file_processing with rich console."""
        print_file_processing("Processing file")
        mock_console.print.assert_called_once_with("Processing file", style="bold yellow")
