"""Tests for config.py module."""

import argparse
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from blobify.config import apply_default_switches, read_blobify_config


class TestBlobifyConfig:
    """Test cases for .blobify configuration handling."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for tests."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        # Cleanup
        for file in temp_dir.rglob("*"):
            if file.is_file():
                file.unlink()
        temp_dir.rmdir()

    @pytest.fixture
    def blobify_file(self, temp_dir):
        """Create a .blobify file fixture."""
        return temp_dir / ".blobify"

    def test_read_blobify_config_no_file(self, temp_dir):
        """Test reading config when no .blobify file exists."""
        includes, excludes, switches = read_blobify_config(temp_dir)
        assert includes == []
        assert excludes == []
        assert switches == []

    def test_read_blobify_config_basic_patterns(self, blobify_file):
        """Test reading basic include/exclude patterns."""
        blobify_file.write_text(
            """
# Test config
+*.py
+docs/**
-*.log
-temp/
@debug=true
@output-filename=test.txt
"""
        )
        includes, excludes, switches = read_blobify_config(blobify_file.parent)
        assert includes == ["*.py", "docs/**"]
        assert excludes == ["*.log", "temp/"]
        assert switches == ["debug=true", "output-filename=test.txt"]

    def test_read_blobify_config_legacy_boolean_switches(self, blobify_file):
        """Test reading legacy boolean switches (converted to key=true)."""
        blobify_file.write_text(
            """
# Test config with legacy boolean switches
+*.py
@debug
@copy-to-clipboard
"""
        )
        includes, excludes, switches = read_blobify_config(blobify_file.parent)
        assert includes == ["*.py"]
        assert excludes == []
        assert switches == ["debug=true", "copy-to-clipboard=true"]

    def test_read_blobify_config_with_context(self, blobify_file):
        """Test reading config with specific context."""
        blobify_file.write_text(
            """
+default.txt
-default.log

[test-context]
+context.py
-context.log
@copy-to-clipboard=true
"""
        )
        # Default context
        includes, excludes, switches = read_blobify_config(blobify_file.parent)
        assert includes == ["default.txt"]
        assert excludes == ["default.log"]
        assert switches == []

        # Specific context
        includes, excludes, switches = read_blobify_config(blobify_file.parent, "test-context")
        assert includes == ["context.py"]
        assert excludes == ["context.log"]
        assert switches == ["copy-to-clipboard=true"]

    def test_read_blobify_config_last_value_wins(self, blobify_file):
        """Test that last value wins for duplicate keys."""
        blobify_file.write_text(
            """
# Test duplicate keys - last value should win
@debug=false
@copy-to-clipboard=false
@debug=true
@copy-to-clipboard=true
+*.py
"""
        )
        includes, excludes, switches = read_blobify_config(blobify_file.parent)
        assert includes == ["*.py"]
        assert excludes == []
        assert switches == ["debug=true", "copy-to-clipboard=true"]

    def test_read_blobify_config_csv_filters(self, blobify_file):
        """Test reading CSV format filters from .blobify file."""
        blobify_file.write_text(
            """
@filter="functions","^def","*.py"
@filter="imports","^import"
+*.py
"""
        )
        includes, excludes, switches = read_blobify_config(blobify_file.parent)
        assert includes == ["*.py"]
        assert excludes == []
        assert switches == ['filter="functions","^def","*.py"', 'filter="imports","^import"']

    def test_read_blobify_config_invalid_patterns(self, blobify_file):
        """Test handling of invalid patterns."""
        blobify_file.write_text(
            """
+valid.py
invalid_line
-valid.log
"""
        )
        includes, excludes, switches = read_blobify_config(blobify_file.parent, debug=True)
        assert includes == ["valid.py"]
        assert excludes == ["valid.log"]

    def test_read_blobify_config_file_read_error(self, temp_dir):
        """Test handling of file read errors."""
        with patch("builtins.open", side_effect=IOError("Read error")):
            includes, excludes, switches = read_blobify_config(temp_dir, debug=True)
            assert includes == []
            assert excludes == []
            assert switches == []

    def test_apply_default_switches_no_switches(self):
        """Test applying empty default switches."""
        args = argparse.Namespace(debug=False, output_filename=None)
        result = apply_default_switches(args, [])
        assert result.debug is False
        assert result.output_filename is None

    def test_apply_default_switches_boolean_switches(self):
        """Test applying boolean default switches."""
        args = argparse.Namespace(debug=False, enable_scrubbing=True, copy_to_clipboard=False)
        switches = ["debug=true", "enable-scrubbing=false", "copy-to-clipboard=true"]
        result = apply_default_switches(args, switches)
        assert result.debug is True
        assert result.enable_scrubbing is False
        assert result.copy_to_clipboard is True

    def test_apply_default_switches_key_value_switches(self):
        """Test applying key=value default switches."""
        args = argparse.Namespace(output_filename=None)
        switches = ["output-filename=default.txt"]
        result = apply_default_switches(args, switches)
        assert result.output_filename == "default.txt"

    def test_apply_default_switches_precedence(self):
        """Test that command line args take precedence over defaults."""
        args = argparse.Namespace(debug=True, output_filename="cmdline.txt")
        switches = ["debug=false", "output-filename=default.txt"]
        result = apply_default_switches(args, switches)
        assert result.debug is True  # Should remain True
        assert result.output_filename == "cmdline.txt"  # Should remain cmdline value

    def test_apply_default_switches_unknown_switches(self):
        """Test handling of unknown default switches."""
        args = argparse.Namespace(debug=False)
        switches = ["unknown-switch=true", "unknown=value"]
        result = apply_default_switches(args, switches, debug=True)
        assert result.debug is False

    def test_apply_default_switches_dash_underscore_conversion(self):
        """Test handling of dash/underscore conversion in switches."""
        args = argparse.Namespace(output_line_numbers=True, output_index=True)
        switches = ["output-line-numbers=false", "output-index=false"]
        result = apply_default_switches(args, switches)
        assert result.output_line_numbers is False
        assert result.output_index is False

    def test_apply_default_switches_filter_handling_csv(self):
        """Test handling of CSV format filter options."""
        args = argparse.Namespace(filter=None)
        switches = ['filter="functions","^def"', 'filter="classes","^class","*.py"']
        result = apply_default_switches(args, switches)
        assert result.filter == ['"functions","^def"', '"classes","^class","*.py"']

    def test_apply_default_switches_filter_handling_legacy(self):
        """Test handling of legacy format filter options."""
        args = argparse.Namespace(filter=None)
        switches = ["filter=functions:^def", "filter=classes:^class"]
        result = apply_default_switches(args, switches)
        assert result.filter == ["functions:^def", "classes:^class"]

    def test_apply_default_switches_list_patterns(self):
        """Test handling of list-patterns option."""
        args = argparse.Namespace(list_patterns="none")
        switches = ["list-patterns=ignored"]
        result = apply_default_switches(args, switches)
        assert result.list_patterns == "ignored"

    def test_apply_default_switches_invalid_boolean_value(self):
        """Test handling of invalid boolean values in defaults."""
        args = argparse.Namespace(debug=False)
        switches = ["debug=invalid"]
        result = apply_default_switches(args, switches, debug=True)
        assert result.debug is False  # Should remain unchanged due to invalid value

    def test_apply_default_switches_invalid_list_patterns_value(self):
        """Test handling of invalid list-patterns values in defaults."""
        args = argparse.Namespace(list_patterns="none")
        switches = ["list-patterns=invalid"]
        result = apply_default_switches(args, switches, debug=True)
        assert result.list_patterns == "none"  # Should remain unchanged due to invalid value
