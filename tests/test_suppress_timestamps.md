"""Tests for the --suppress-timestamps functionality."""

from unittest.mock import patch
import re

import pytest

from blobify.main import main

class TestSuppressTimestamps:
"""Test cases for the --suppress-timestamps command line option."""

    def setup_test_files(self, tmp_path):
        """Create standard test files."""
        (tmp_path / "app.py").write_text("print('hello world')")
        (tmp_path / "README.md").write_text("# Test Project")
        return tmp_path

    def test_default_behavior_includes_timestamps(self, tmp_path):
        """Test that by default, timestamps are included in output."""
        self.setup_test_files(tmp_path)
        output_file = tmp_path / "output.txt"

        with patch("sys.argv", ["bfy", str(tmp_path), "--output-filename", str(output_file)]):
            main()

        content = output_file.read_text(encoding="utf-8")

        # Should include Generated timestamp
        assert "# Generated:" in content

        # Should match ISO format timestamp pattern
        timestamp_pattern = r"# Generated: \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+"
        assert re.search(timestamp_pattern, content), "Should contain ISO format timestamp"

    def test_suppress_timestamps_true_removes_timestamps(self, tmp_path):
        """Test that --suppress-timestamps=true removes timestamps from output."""
        self.setup_test_files(tmp_path)
        output_file = tmp_path / "output.txt"

        with patch("sys.argv", ["bfy", str(tmp_path), "--suppress-timestamps=true", "--output-filename", str(output_file)]):
            main()

        content = output_file.read_text(encoding="utf-8")

        # Should NOT include Generated timestamp
        assert "# Generated:" not in content

        # Should still have other header elements
        assert "# Blobify Text File Index" in content
        assert "# Source Directory:" in content

    def test_suppress_timestamps_false_includes_timestamps(self, tmp_path):
        """Test that --suppress-timestamps=false explicitly includes timestamps."""
        self.setup_test_files(tmp_path)
        output_file = tmp_path / "output.txt"

        with patch("sys.argv", ["bfy", str(tmp_path), "--suppress-timestamps=false", "--output-filename", str(output_file)]):
            main()

        content = output_file.read_text(encoding="utf-8")

        # Should include Generated timestamp
        assert "# Generated:" in content

        # Should match ISO format timestamp pattern
        timestamp_pattern = r"# Generated: \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+"
        assert re.search(timestamp_pattern, content), "Should contain ISO format timestamp"

    def test_suppress_timestamps_as_default_switch_in_blobify(self, tmp_path):
        """Test that suppress-timestamps can be set as a default switch in .blobify."""
        # Create git repo
        (tmp_path / ".git").mkdir()

        # Create .blobify with suppress-timestamps=true as default
        (tmp_path / ".blobify").write_text(
            """

@suppress-timestamps=true +_.py +_.md
"""
)

        self.setup_test_files(tmp_path)
        output_file = tmp_path / "output.txt"

        with patch("sys.argv", ["bfy", str(tmp_path), "--output-filename", str(output_file)]):
            main()

        content = output_file.read_text(encoding="utf-8")

        # Default switch should be applied - no timestamps
        assert "# Generated:" not in content
        assert "# Blobify Text File Index" in content
        assert "# Source Directory:" in content

    def test_command_line_override_blobify_default(self, tmp_path):
        """Test that command line flag takes precedence over .blobify default."""
        # Create git repo
        (tmp_path / ".git").mkdir()

        # Create .blobify with suppress-timestamps=true as default
        (tmp_path / ".blobify").write_text("@suppress-timestamps=true\n+*.py\n")

        self.setup_test_files(tmp_path)
        output_file = tmp_path / "output.txt"

        # Command line should override .blobify default
        with patch("sys.argv", ["bfy", str(tmp_path), "--suppress-timestamps=false", "--output-filename", str(output_file)]):
            main()

        content = output_file.read_text(encoding="utf-8")

        # Command line value should take precedence - timestamps should be included
        assert "# Generated:" in content

    def test_suppress_timestamps_with_context(self, tmp_path):
        """Test suppress-timestamps works correctly with contexts."""
        # Create git repo
        (tmp_path / ".git").mkdir()

        # Create .blobify with context-specific suppress-timestamps
        (tmp_path / ".blobify").write_text(
            """

# Default context - timestamps enabled

+\*.py

[no-timestamps]
@suppress-timestamps=true +_.py +_.md
"""
)

        self.setup_test_files(tmp_path)

        # Test default context (should have timestamps)
        output_file1 = tmp_path / "output_default.txt"
        with patch("sys.argv", ["bfy", str(tmp_path), "--output-filename", str(output_file1)]):
            main()

        content1 = output_file1.read_text(encoding="utf-8")
        assert "# Generated:" in content1

        # Test no-timestamps context (should NOT have timestamps)
        output_file2 = tmp_path / "output_context.txt"
        with patch("sys.argv", ["bfy", str(tmp_path), "-x", "no-timestamps", "--output-filename", str(output_file2)]):
            main()

        content2 = output_file2.read_text(encoding="utf-8")
        assert "# Generated:" not in content2
        assert "# Blobify Text File Index" in content2

    def test_suppress_timestamps_with_inheritance(self, tmp_path):
        """Test suppress-timestamps with context inheritance."""
        # Create git repo
        (tmp_path / ".git").mkdir()

        # Create .blobify with inheritance
        (tmp_path / ".blobify").write_text(
            """

[base]
@suppress-timestamps=true
+\*.py

[extended:base]

# Inherits suppress-timestamps=true

+\*.md
"""
)

        self.setup_test_files(tmp_path)
        output_file = tmp_path / "output.txt"

        with patch("sys.argv", ["bfy", str(tmp_path), "-x", "extended", "--output-filename", str(output_file)]):
            main()

        content = output_file.read_text(encoding="utf-8")

        # Should inherit suppress-timestamps=true from base
        assert "# Generated:" not in content
        assert "# Blobify Text File Index" in content

    def test_suppress_timestamps_preserves_other_header_elements(self, tmp_path):
        """Test that suppressing timestamps doesn't affect other header elements."""
        # Create git repo
        (tmp_path / ".git").mkdir()

        # Create .blobify with filters and LLM instructions
        (tmp_path / ".blobify").write_text(
            """

## This is a test project for analysis

@filter="functions","^def"
@suppress-timestamps=true
+\*.py
"""
)

        (tmp_path / "app.py").write_text("def hello():\n    print('world')")
        output_file = tmp_path / "output.txt"

        with patch("sys.argv", ["bfy", str(tmp_path), "--output-filename", str(output_file)]):
            main()

        content = output_file.read_text(encoding="utf-8")

        # Should NOT have timestamps
        assert "# Generated:" not in content

        # Should still have all other header elements
        assert "# Blobify Text File Index" in content
        assert "# Source Directory:" in content
        assert "# Instructions for AI/LLM analysis:" in content
        assert "# * This is a test project for analysis" in content
        assert "# Content filters applied:" in content
        assert "functions: ^def" in content

    def test_suppress_timestamps_different_output_modes(self, tmp_path):
        """Test suppress-timestamps works with different output mode combinations."""
        self.setup_test_files(tmp_path)

        test_cases = [
            # (additional_flags, should_check_for_timestamps)
            ([], True),  # Default - should check timestamps are suppressed
            (["--output-content=false"], True),
            (["--output-index=false"], True),
            (["--output-metadata=false"], True),
            (["--output-content=false", "--output-index=false"], True),
            (["--output-content=false", "--output-metadata=false"], True),
            (["--output-index=false", "--output-metadata=false"], True),
            (["--output-content=false", "--output-index=false", "--output-metadata=false"], True),
        ]

        for additional_flags, should_check in test_cases:
            output_file = tmp_path / f"output_{'_'.join(flag.replace('--', '').replace('=', '_') for flag in additional_flags)}.txt"

            flags = ["bfy", str(tmp_path), "--suppress-timestamps=true", "--output-filename", str(output_file)]
            flags.extend(additional_flags)

            with patch("sys.argv", flags):
                main()

            content = output_file.read_text(encoding="utf-8")

            if should_check:
                # All modes should respect suppress-timestamps
                assert "# Generated:" not in content, f"Failed for flags: {additional_flags}"
                assert "# Blobify Text File Index" in content

    def test_config_apply_default_switches_suppress_timestamps(self):
        """Test that suppress-timestamps can be applied as a default switch."""
        import argparse
        from blobify.config import apply_default_switches

        args = argparse.Namespace(suppress_timestamps=False)
        switches = ["suppress-timestamps=true"]
        result = apply_default_switches(args, switches)
        assert result.suppress_timestamps is True

        # Test the reverse
        args = argparse.Namespace(suppress_timestamps=True)
        switches = ["suppress-timestamps=false"]
        result = apply_default_switches(args, switches)
        assert result.suppress_timestamps is False

    def test_config_apply_default_switches_precedence_suppress_timestamps(self):
        """Test that command line suppress-timestamps takes precedence over defaults."""
        import argparse
        from blobify.config import apply_default_switches

        # Command line already has --suppress-timestamps=true set
        args = argparse.Namespace(suppress_timestamps=True, debug=False)
        switches = ["suppress-timestamps=false", "debug=true"]  # Both in defaults
        result = apply_default_switches(args, switches)

        assert result.suppress_timestamps is True  # Should remain True from command line
        assert result.debug is True  # Should be set by default

    def test_suppress_timestamps_with_filters_and_context(self, tmp_path):
        """Test suppress-timestamps works with complex configurations."""
        # Create git repo
        (tmp_path / ".git").mkdir()

        # Create .blobify with complex config
        (tmp_path / ".blobify").write_text(
            """

[analysis:default]

## Analyze this code carefully

@filter="functions","^def","_.py"
@filter="classes","^class","_.py"
@suppress-timestamps=true
@debug=false +_.py +_.js
"""
)

        (tmp_path / "app.py").write_text("def hello():\n    print('world')\nclass Test:\n    pass")
        (tmp_path / "script.js").write_text("function greet() {}\nconst x = 1;")

        output_file = tmp_path / "output.txt"

        with patch("sys.argv", ["bfy", str(tmp_path), "-x", "analysis", "--output-filename", str(output_file)]):
            main()

        content = output_file.read_text(encoding="utf-8")

        # Should not have timestamps due to suppress-timestamps=true
        assert "# Generated:" not in content

        # Should have all other features working
        assert "# Instructions for AI/LLM analysis:" in content
        assert "# * Analyze this code carefully" in content
        assert "# Content filters applied:" in content
        assert "functions: ^def (files: *.py)" in content
        assert "classes: ^class (files: *.py)" in content

        # Should apply filters correctly
        assert "def hello():" in content
        assert "class Test:" in content
        assert "print('world')" not in content  # Filtered out

        # JS file should not match Python-specific filters
        assert "START_FILE: script.js" in content
        assert "function greet()" not in content  # No matching filter for JS

    def test_header_format_with_and_without_timestamps(self, tmp_path):
        """Test that header format is correct both with and without timestamps."""
        self.setup_test_files(tmp_path)

        # Test with timestamps
        output_file1 = tmp_path / "with_timestamps.txt"
        with patch("sys.argv", ["bfy", str(tmp_path), "--suppress-timestamps=false", "--output-filename", str(output_file1)]):
            main()

        content1 = output_file1.read_text(encoding="utf-8")

        # Should have proper header structure with timestamps
        lines1 = content1.split('\n')
        assert lines1[0] == "# Blobify Text File Index"
        assert lines1[1].startswith("# Generated: ")
        assert lines1[2].startswith("# Source Directory: ")

        # Test without timestamps
        output_file2 = tmp_path / "without_timestamps.txt"
        with patch("sys.argv", ["bfy", str(tmp_path), "--suppress-timestamps=true", "--output-filename", str(output_file2)]):
            main()

        content2 = output_file2.read_text(encoding="utf-8")

        # Should have proper header structure without timestamps
        lines2 = content2.split('\n')
        assert lines2[0] == "# Blobify Text File Index"
        assert lines2[1].startswith("# Source Directory: ")
        # No Generated line should be present
        assert not any(line.startswith("# Generated: ") for line in lines2[:10])

    def test_reproducible_output_with_suppress_timestamps(self, tmp_path):
        """Test that suppressing timestamps makes output reproducible."""
        self.setup_test_files(tmp_path)

        # Generate output twice with timestamps suppressed
        output_file1 = tmp_path / "output1.txt"
        with patch("sys.argv", ["bfy", str(tmp_path), "--suppress-timestamps=true", "--output-filename", str(output_file1)]):
            main()

        # Small delay to ensure different timestamps would be generated
        import time
        time.sleep(0.1)

        output_file2 = tmp_path / "output2.txt"
        with patch("sys.argv", ["bfy", str(tmp_path), "--suppress-timestamps=true", "--output-filename", str(output_file2)]):
            main()

        content1 = output_file1.read_text(encoding="utf-8")
        content2 = output_file2.read_text(encoding="utf-8")

        # Output should be identical when timestamps are suppressed
        assert content1 == content2, "Output should be identical when timestamps are suppressed"

    def test_timestamps_validation_error_handling(self):
        """Test validation of boolean values for suppress-timestamps."""
        from blobify.config import validate_boolean_value

        # Valid values
        assert validate_boolean_value("true") is True
        assert validate_boolean_value("false") is False
        assert validate_boolean_value("1") is True
        assert validate_boolean_value("0") is False

        # Invalid values should raise ValueError
        with pytest.raises(ValueError, match="Invalid boolean value"):
            validate_boolean_value("invalid")

        with pytest.raises(ValueError, match="Invalid boolean value"):
            validate_boolean_value("maybe")

if **name** == "**main**":
pytest.main([__file__, "-v"])
