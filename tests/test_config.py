"""Tests for config.py module."""

import argparse
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from blobify.config import read_blobify_config, apply_default_switches


class TestBlobifyConfig(unittest.TestCase):
    """Test cases for .blobify configuration handling."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.blobify_file = self.temp_dir / ".blobify"

    def tearDown(self):
        """Clean up test fixtures."""
        if self.blobify_file.exists():
            self.blobify_file.unlink()
        self.temp_dir.rmdir()

    def test_read_blobify_config_no_file(self):
        """Test reading config when no .blobify file exists."""
        includes, excludes, switches = read_blobify_config(self.temp_dir)
        self.assertEqual(includes, [])
        self.assertEqual(excludes, [])
        self.assertEqual(switches, [])

    def test_read_blobify_config_basic_patterns(self):
        """Test reading basic include/exclude patterns."""
        self.blobify_file.write_text(
            """
# Test config
+*.py
+docs/**
-*.log
-temp/
@debug
@output=test.txt
"""
        )
        includes, excludes, switches = read_blobify_config(self.temp_dir)
        self.assertEqual(includes, ["*.py", "docs/**"])
        self.assertEqual(excludes, ["*.log", "temp/"])
        self.assertEqual(switches, ["debug", "output=test.txt"])

    def test_read_blobify_config_with_context(self):
        """Test reading config with specific context."""
        self.blobify_file.write_text(
            """
+default.txt
-default.log

[test-context]
+context.py
-context.log
@clip
"""
        )
        # Default context
        includes, excludes, switches = read_blobify_config(self.temp_dir)
        self.assertEqual(includes, ["default.txt"])
        self.assertEqual(excludes, ["default.log"])
        self.assertEqual(switches, [])

        # Specific context
        includes, excludes, switches = read_blobify_config(
            self.temp_dir, "test-context"
        )
        self.assertEqual(includes, ["context.py"])
        self.assertEqual(excludes, ["context.log"])
        self.assertEqual(switches, ["clip"])

    def test_read_blobify_config_invalid_patterns(self):
        """Test handling of invalid patterns."""
        self.blobify_file.write_text(
            """
+valid.py
invalid_line
-valid.log
"""
        )
        includes, excludes, switches = read_blobify_config(self.temp_dir, debug=True)
        self.assertEqual(includes, ["valid.py"])
        self.assertEqual(excludes, ["valid.log"])

    def test_read_blobify_config_file_read_error(self):
        """Test handling of file read errors."""
        with patch("builtins.open", side_effect=IOError("Read error")):
            includes, excludes, switches = read_blobify_config(
                self.temp_dir, debug=True
            )
            self.assertEqual(includes, [])
            self.assertEqual(excludes, [])
            self.assertEqual(switches, [])

    def test_apply_default_switches_no_switches(self):
        """Test applying empty default switches."""
        args = argparse.Namespace(debug=False, output=None)
        result = apply_default_switches(args, [])
        self.assertEqual(result.debug, False)
        self.assertEqual(result.output, None)

    def test_apply_default_switches_boolean_switches(self):
        """Test applying boolean default switches."""
        args = argparse.Namespace(debug=False, noclean=False, clip=False)
        switches = ["debug", "noclean", "clip"]
        result = apply_default_switches(args, switches)
        self.assertEqual(result.debug, True)
        self.assertEqual(result.noclean, True)
        self.assertEqual(result.clip, True)

    def test_apply_default_switches_key_value_switches(self):
        """Test applying key=value default switches."""
        args = argparse.Namespace(output=None)
        switches = ["output=default.txt"]
        result = apply_default_switches(args, switches)
        self.assertEqual(result.output, "default.txt")

    def test_apply_default_switches_precedence(self):
        """Test that command line args take precedence over defaults."""
        args = argparse.Namespace(debug=True, output="cmdline.txt")
        switches = ["debug", "output=default.txt"]
        result = apply_default_switches(args, switches)
        self.assertEqual(result.debug, True)  # Should remain True
        self.assertEqual(result.output, "cmdline.txt")  # Should remain cmdline value

    def test_apply_default_switches_unknown_switches(self):
        """Test handling of unknown default switches."""
        args = argparse.Namespace(debug=False)
        switches = ["unknown-switch", "unknown=value"]
        result = apply_default_switches(args, switches, debug=True)
        self.assertEqual(result.debug, False)

    def test_apply_default_switches_dash_underscore_conversion(self):
        """Test handling of dash/underscore conversion in switches."""
        args = argparse.Namespace(no_line_numbers=False, no_index=False)
        switches = ["no-line-numbers", "no-index"]
        result = apply_default_switches(args, switches)
        self.assertEqual(result.no_line_numbers, True)
        self.assertEqual(result.no_index, True)


if __name__ == "__main__":
    unittest.main()
