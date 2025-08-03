"""Tests for console.py module."""

import sys
from io import StringIO
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

    def test_print_status_without_style(self, capsys):
        """Test print_status without style parameter."""
        print_status("Test message")
        captured = capsys.readouterr()
        assert "Test message" in captured.err

    def test_print_status_with_style(self, capsys):
        """Test print_status with style parameter (should work with or without rich)."""
        print_status("Test message", "bold")
        captured = capsys.readouterr()
        assert "Test message" in captured.err

    def test_print_debug_output(self, capsys):
        """Test print_debug produces output to stderr."""
        print_debug("Debug message")
        captured = capsys.readouterr()
        assert "Debug message" in captured.err

    def test_print_phase_output(self, capsys):
        """Test print_phase produces formatted output."""
        print_phase("test phase")
        captured = capsys.readouterr()
        # Should contain the phase name in some form (with or without rich formatting)
        assert "TEST PHASE" in captured.err.upper()

    def test_print_warning_output(self, capsys):
        """Test print_warning produces output to stderr."""
        print_warning("Warning message")
        captured = capsys.readouterr()
        assert "Warning message" in captured.err

    def test_print_error_output(self, capsys):
        """Test print_error produces output to stderr."""
        print_error("Error message")
        captured = capsys.readouterr()
        assert "Error message" in captured.err

    def test_print_success_output(self, capsys):
        """Test print_success produces output to stderr."""
        print_success("Success message")
        captured = capsys.readouterr()
        assert "Success message" in captured.err

    def test_print_file_processing_output(self, capsys):
        """Test print_file_processing produces output to stderr."""
        print_file_processing("Processing file")
        captured = capsys.readouterr()
        assert "Processing file" in captured.err

    def test_console_output_goes_to_stderr(self, capsys):
        """Test that all console output goes to stderr, not stdout."""
        print_status("status")
        print_debug("debug")
        print_warning("warning")
        print_error("error")
        print_success("success")

        captured = capsys.readouterr()

        # All output should be in stderr
        assert "status" in captured.err
        assert "debug" in captured.err
        assert "warning" in captured.err
        assert "error" in captured.err
        assert "success" in captured.err

        # Nothing should be in stdout
        assert captured.out == ""

    def test_console_functions_with_no_rich(self, capsys):
        """Test console functions work when rich is not available."""
        # Temporarily mock rich as unavailable
        with patch("blobify.console.RICH_AVAILABLE", False):
            with patch("blobify.console.console", None):
                print_status("No rich message")
                print_debug("No rich debug")
                print_phase("no rich phase")

        captured = capsys.readouterr()
        assert "No rich message" in captured.err
        assert "No rich debug" in captured.err
        # Phase should show some form of the phase name
        assert "NO RICH PHASE" in captured.err.upper()

    def test_console_functions_preserve_message_content(self, capsys):
        """Test that console functions preserve the exact message content."""
        test_message = "Special chars: éñ中文 and symbols: !@#$%^&*()"

        print_status(test_message)
        print_debug(test_message)
        print_warning(test_message)
        print_error(test_message)
        print_success(test_message)

        captured = capsys.readouterr()

        # The exact message should appear multiple times (once for each function call)
        assert captured.err.count(test_message) == 5

    def test_stderr_redirection_compatibility(self):
        """Test that console functions work when stderr is redirected."""
        # Capture stderr using StringIO to simulate redirection
        original_stderr = sys.stderr
        captured_stderr = StringIO()

        try:
            sys.stderr = captured_stderr

            print_status("Redirected status")
            print_error("Redirected error")

            output = captured_stderr.getvalue()
            assert "Redirected status" in output
            assert "Redirected error" in output

        finally:
            sys.stderr = original_stderr
