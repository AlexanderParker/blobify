"""Tests for console.py module."""

import sys
import unittest
from io import StringIO
from unittest.mock import Mock, patch

from blobify.console import (
    print_debug,
    print_error,
    print_file_processing,
    print_phase,
    print_status,
    print_success,
    print_warning,
)


class TestConsoleOutput(unittest.TestCase):
    """Test cases for console output functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.stderr_backup = sys.stderr
        self.stderr_capture = StringIO()
        sys.stderr = self.stderr_capture

    def tearDown(self):
        """Clean up test fixtures."""
        sys.stderr = self.stderr_backup

    @patch("blobify.console.console", None)
    def test_print_status_no_rich(self):
        """Test print_status without rich console."""
        print_status("Test message")
        output = self.stderr_capture.getvalue()
        self.assertIn("Test message", output)

    @patch("blobify.console.console")
    def test_print_status_with_rich(self, mock_console):
        """Test print_status with rich console."""
        print_status("Test message", "bold")
        mock_console.print.assert_called_once_with("Test message", style="bold")

    @patch("blobify.console.console", None)
    def test_print_debug_no_rich(self):
        """Test print_debug without rich console."""
        print_debug("Debug message")
        output = self.stderr_capture.getvalue()
        self.assertIn("Debug message", output)

    @patch("blobify.console.console")
    def test_print_debug_with_rich(self, mock_console):
        """Test print_debug with rich console."""
        print_debug("Debug message")
        mock_console.print.assert_called_once_with("Debug message", style="dim cyan")

    @patch("blobify.console.console", None)
    def test_print_phase_no_rich(self):
        """Test print_phase without rich console."""
        print_phase("test phase")
        output = self.stderr_capture.getvalue()
        self.assertIn("=== TEST PHASE ===", output)

    @patch("blobify.console.console")
    def test_print_phase_with_rich(self, mock_console):
        """Test print_phase with rich console."""
        print_phase("test phase")
        expected = "\n[bold magenta]──── TEST PHASE ────[/bold magenta]"
        mock_console.print.assert_called_once_with(expected)

    @patch("blobify.console.console", None)
    def test_print_warning_no_rich(self):
        """Test print_warning without rich console."""
        print_warning("Warning message")
        output = self.stderr_capture.getvalue()
        self.assertIn("Warning message", output)

    @patch("blobify.console.console")
    def test_print_warning_with_rich(self, mock_console):
        """Test print_warning with rich console."""
        print_warning("Warning message")
        mock_console.print.assert_called_once_with("Warning message", style="yellow")

    @patch("blobify.console.console", None)
    def test_print_error_no_rich(self):
        """Test print_error without rich console."""
        print_error("Error message")
        output = self.stderr_capture.getvalue()
        self.assertIn("Error message", output)

    @patch("blobify.console.console")
    def test_print_error_with_rich(self, mock_console):
        """Test print_error with rich console."""
        print_error("Error message")
        mock_console.print.assert_called_once_with("Error message", style="bold red")

    @patch("blobify.console.console", None)
    def test_print_success_no_rich(self):
        """Test print_success without rich console."""
        print_success("Success message")
        output = self.stderr_capture.getvalue()
        self.assertIn("Success message", output)

    @patch("blobify.console.console")
    def test_print_success_with_rich(self, mock_console):
        """Test print_success with rich console."""
        print_success("Success message")
        mock_console.print.assert_called_once_with("Success message", style="green")

    @patch("blobify.console.console", None)
    def test_print_file_processing_no_rich(self):
        """Test print_file_processing without rich console."""
        print_file_processing("Processing file")
        output = self.stderr_capture.getvalue()
        self.assertIn("Processing file", output)

    @patch("blobify.console.console")
    def test_print_file_processing_with_rich(self, mock_console):
        """Test print_file_processing with rich console."""
        print_file_processing("Processing file")
        mock_console.print.assert_called_once_with(
            "Processing file", style="bold yellow"
        )


if __name__ == "__main__":
    unittest.main()
