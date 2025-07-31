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
@debug
@output=test.txt
"""
        )
        includes, excludes, switches = read_blobify_config(blobify_file.parent)
        assert includes == ["*.py", "docs/**"]
        assert excludes == ["*.log", "temp/"]
        assert switches == ["debug", "output=test.txt"]

    def test_read_blobify_config_with_context(self, blobify_file):
        """Test reading config with specific context."""
        blobify_file.write_text(
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
        includes, excludes, switches = read_blobify_config(blobify_file.parent)
        assert includes == ["default.txt"]
        assert excludes == ["default.log"]
        assert switches == []

        # Specific context
        includes, excludes, switches = read_blobify_config(blobify_file.parent, "test-context")
        assert includes == ["context.py"]
        assert excludes == ["context.log"]
        assert switches == ["clip"]

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
        args = argparse.Namespace(debug=False, output=None)
        result = apply_default_switches(args, [])
        assert result.debug is False
        assert result.output is None

    def test_apply_default_switches_boolean_switches(self):
        """Test applying boolean default switches."""
        args = argparse.Namespace(debug=False, noclean=False, clip=False)
        switches = ["debug", "noclean", "clip"]
        result = apply_default_switches(args, switches)
        assert result.debug is True
        assert result.noclean is True
        assert result.clip is True

    def test_apply_default_switches_key_value_switches(self):
        """Test applying key=value default switches."""
        args = argparse.Namespace(output=None)
        switches = ["output=default.txt"]
        result = apply_default_switches(args, switches)
        assert result.output == "default.txt"

    def test_apply_default_switches_precedence(self):
        """Test that command line args take precedence over defaults."""
        args = argparse.Namespace(debug=True, output="cmdline.txt")
        switches = ["debug", "output=default.txt"]
        result = apply_default_switches(args, switches)
        assert result.debug is True  # Should remain True
        assert result.output == "cmdline.txt"  # Should remain cmdline value

    def test_apply_default_switches_unknown_switches(self):
        """Test handling of unknown default switches."""
        args = argparse.Namespace(debug=False)
        switches = ["unknown-switch", "unknown=value"]
        result = apply_default_switches(args, switches, debug=True)
        assert result.debug is False

    def test_apply_default_switches_dash_underscore_conversion(self):
        """Test handling of dash/underscore conversion in switches."""
        args = argparse.Namespace(no_line_numbers=False, no_index=False)
        switches = ["no-line-numbers", "no-index"]
        result = apply_default_switches(args, switches)
        assert result.no_line_numbers is True
        assert result.no_index is True
