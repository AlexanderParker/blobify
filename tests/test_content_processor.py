"""Tests for content_processor.py module."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from blobify.content_processor import get_file_metadata, is_text_file, scrub_content


class TestContentProcessor:
    """Test cases for content processing functions."""

    def test_scrub_content_disabled(self):
        """Test scrub_content when disabled."""
        content = "Email: test@example.com"
        result, count = scrub_content(content, enabled=False)
        assert result == content
        assert count == 0

    @patch("blobify.content_processor.SCRUBADUB_AVAILABLE", False)
    def test_scrub_content_unavailable(self):
        """Test scrub_content when scrubadub is unavailable."""
        content = "Email: test@example.com"
        result, count = scrub_content(content, enabled=True)
        assert result == content
        assert count == 0

    @patch("blobify.content_processor.SCRUBADUB_AVAILABLE", True)
    @patch("blobify.content_processor.scrubadub")
    def test_scrub_content_with_scrubadub(self, mock_scrubadub):
        """Test scrub_content with scrubadub available."""
        mock_scrubber = Mock()
        mock_filth = Mock()
        mock_filth.type = "email"
        mock_filth.beg = 7
        mock_filth.end = 21
        mock_filth.replacement_string = "{{EMAIL}}"

        mock_scrubber.iter_filth.return_value = [mock_filth]
        mock_scrubber.clean.return_value = "Email: {{EMAIL}}"
        mock_scrubadub.Scrubber.return_value = mock_scrubber

        content = "Email: test@example.com"
        result, count = scrub_content(content, enabled=True, debug=True)

        assert result == "Email: {{EMAIL}}"
        assert count == 1
        mock_scrubber.remove_detector.assert_called_once_with("twitter")

    @patch("blobify.content_processor.SCRUBADUB_AVAILABLE", True)
    @patch("blobify.content_processor.scrubadub")
    def test_scrub_content_exception(self, mock_scrubadub):
        """Test scrub_content handles exceptions gracefully."""
        mock_scrubadub.Scrubber.side_effect = Exception("Test error")

        content = "Email: test@example.com"
        result, count = scrub_content(content, enabled=True, debug=True)

        assert result == content
        assert count == 0

    def test_is_text_file_python(self, temp_dir):
        """Test is_text_file with Python file."""
        py_file = temp_dir / "test.py"
        py_file.write_text("print('hello')")
        assert is_text_file(py_file) is True

    def test_is_text_file_text(self, temp_dir):
        """Test is_text_file with text file."""
        txt_file = temp_dir / "test.txt"
        txt_file.write_text("Hello world")
        assert is_text_file(txt_file) is True

    def test_is_text_file_security_extension(self, temp_dir):
        """Test is_text_file rejects security file extensions."""
        key_file = temp_dir / "test.key"
        key_file.write_text("-----BEGIN PRIVATE KEY-----")
        assert is_text_file(key_file) is False

    def test_is_text_file_unknown_extension(self, temp_dir):
        """Test is_text_file with unknown extension."""
        unknown_file = temp_dir / "test.unknown"
        unknown_file.write_text("Some content")
        assert is_text_file(unknown_file) is False

    def test_is_text_file_binary_content(self, temp_dir):
        """Test is_text_file with binary content."""
        bin_file = temp_dir / "test.py"
        bin_file.write_bytes(b"\x7f\x45\x4c\x46")  # ELF signature
        assert is_text_file(bin_file) is False

    def test_is_text_file_high_null_bytes(self, temp_dir):
        """Test is_text_file with high null byte concentration."""
        bin_file = temp_dir / "test.py"
        content = b"a" + b"\x00" * 1000  # > 30% nulls
        bin_file.write_bytes(content)
        assert is_text_file(bin_file) is False

    def test_is_text_file_unicode_decode_error(self, temp_dir):
        """Test is_text_file with invalid UTF-8."""
        bin_file = temp_dir / "test.py"
        bin_file.write_bytes(b"\xff\xfe\xfd")  # Invalid UTF-8
        assert is_text_file(bin_file) is False

    def test_is_text_file_io_error(self, temp_dir):
        """Test is_text_file handles IO errors."""
        nonexistent = temp_dir / "nonexistent.py"
        assert is_text_file(nonexistent) is False

    def test_get_file_metadata(self, temp_dir):
        """Test get_file_metadata returns correct structure."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("Test content")

        metadata = get_file_metadata(test_file)

        assert "size" in metadata
        assert "created" in metadata
        assert "modified" in metadata
        assert "accessed" in metadata
        assert metadata["size"] == 12  # "Test content" is 12 bytes

        # Check that timestamps are ISO format strings
        for key in ["created", "modified", "accessed"]:
            assert isinstance(metadata[key], str)
            # Should be able to parse as ISO datetime
            import datetime

            datetime.datetime.fromisoformat(metadata[key])
