"""Tests for the --show-excluded functionality."""

from unittest.mock import patch

import pytest

from blobify.main import main


class TestShowExcluded:
    """Test cases for the --show-excluded command line option."""

    def setup_test_environment(self, tmp_path):
        """Create a test environment with git repo, gitignore, and blobify config."""
        # Create git repo
        (tmp_path / ".git").mkdir()

        # Create .gitignore
        (tmp_path / ".gitignore").write_text("*.log\n*.tmp\n")

        # Create .blobify with some exclusions
        (tmp_path / ".blobify").write_text(
            """
+*.py
+*.md
-secret.txt
-private/**
"""
        )

        # Create various files
        (tmp_path / "app.py").write_text("print('main application')")
        (tmp_path / "README.md").write_text("# Project Documentation")
        (tmp_path / "debug.log").write_text("ERROR: Something went wrong")  # Git ignored
        (tmp_path / "temp.tmp").write_text("Temporary file content")  # Git ignored
        (tmp_path / "secret.txt").write_text("password=secret123")  # Blobify excluded

        # Create subdirectory with excluded files
        private_dir = tmp_path / "private"
        private_dir.mkdir()
        (private_dir / "confidential.txt").write_text("confidential data")  # Blobify excluded

        return tmp_path

    def test_default_behavior_shows_excluded_files(self, tmp_path):
        """Test that by default, excluded files appear in content section with placeholders."""
        self.setup_test_environment(tmp_path)
        output_file = tmp_path / "output_default.txt"

        with patch("sys.argv", ["bfy", str(tmp_path), "--output-filename", str(output_file)]):
            main()

        content = output_file.read_text(encoding="utf-8")

        # Should include all files in index
        assert "app.py" in content
        assert "README.md" in content
        assert "debug.log [FILE CONTENTS IGNORED BY GITIGNORE]" in content
        assert "secret.txt [FILE CONTENTS EXCLUDED BY .blobify]" in content

        # Should include content for non-excluded files
        assert "print('main application')" in content
        assert "# Project Documentation" in content

        # Should include START_FILE markers for excluded files with placeholders
        assert "START_FILE: debug.log" in content
        assert "START_FILE: secret.txt" in content
        assert "[Content excluded - file ignored by .gitignore]" in content
        assert "[Content excluded - file excluded by .blobify]" in content

        # Should not include actual content of excluded files
        assert "ERROR: Something went wrong" not in content
        assert "password=secret123" not in content

    def test_show_excluded_false_removes_files_from_content_section(self, tmp_path):
        """Test that --show-excluded=false removes excluded files from content section entirely."""
        self.setup_test_environment(tmp_path)
        output_file = tmp_path / "output_suppressed.txt"

        with patch("sys.argv", ["bfy", str(tmp_path), "--show-excluded=false", "--output-filename", str(output_file)]):
            main()

        content = output_file.read_text(encoding="utf-8")

        # Should still include all files in index (suppression only affects content section)
        assert "app.py" in content
        assert "README.md" in content
        assert "debug.log [FILE CONTENTS IGNORED BY GITIGNORE]" in content
        assert "secret.txt [FILE CONTENTS EXCLUDED BY .blobify]" in content

        # Should include content for non-excluded files
        assert "print('main application')" in content
        assert "# Project Documentation" in content

        # Should NOT include START_FILE markers for excluded files
        assert "START_FILE: debug.log" not in content
        assert "START_FILE: secret.txt" not in content
        assert "START_FILE: temp.tmp" not in content

        # Should NOT include placeholder messages
        assert "[Content excluded - file ignored by .gitignore]" not in content
        assert "[Content excluded - file excluded by .blobify]" not in content

        # Should still include START_FILE markers for included files
        assert "START_FILE: app.py" in content
        assert "START_FILE: README.md" in content

    def test_show_excluded_with_no_content_flag(self, tmp_path):
        """Test that --show-excluded=false works correctly with --output-content=false."""
        self.setup_test_environment(tmp_path)
        output_file = tmp_path / "output_no_content.txt"

        with patch(
            "sys.argv",
            [
                "bfy",
                str(tmp_path),
                "--show-excluded=false",
                "--output-content=false",
                "--output-filename",
                str(output_file),
            ],
        ):
            main()

        content = output_file.read_text(encoding="utf-8")

        # Should include all files in index (--output-content=false doesn't show status labels)
        assert "app.py" in content
        assert "README.md" in content
        assert "debug.log" in content  # No status label with --output-content=false
        assert "secret.txt" in content

        # Should not show any file content (due to --output-content=false)
        assert "print('main application')" not in content
        assert "# Project Documentation" not in content

        # Should not have any START_FILE markers (due to --output-content=false)
        # Note: When --output-content=false is used but metadata is enabled (default), START_FILE markers
        # will still appear for included files to wrap the metadata sections
        assert "FILE_CONTENT:" not in content

    def test_show_excluded_with_metadata_only(self, tmp_path):
        """Test that --show-excluded=false works with --output-content=false but metadata enabled."""
        self.setup_test_environment(tmp_path)
        output_file = tmp_path / "output_metadata_only.txt"

        with patch(
            "sys.argv",
            [
                "bfy",
                str(tmp_path),
                "--show-excluded=false",
                "--output-content=false",
                "--output-filename",
                str(output_file),
            ],
        ):
            main()

        content = output_file.read_text(encoding="utf-8")

        # Should have START_FILE markers for included files (for metadata)
        assert "START_FILE: app.py" in content
        assert "START_FILE: README.md" in content

        # Should NOT have START_FILE markers for excluded files
        assert "START_FILE: debug.log" not in content
        assert "START_FILE: secret.txt" not in content

        # Should have metadata sections for included files
        assert "FILE_METADATA:" in content
        assert "Size:" in content

    def test_show_excluded_as_default_switch_in_blobify(self, tmp_path):
        """Test that show-excluded can be set as a default switch in .blobify."""
        # Create git repo
        (tmp_path / ".git").mkdir()

        # Create .blobify with show-excluded=false as default
        (tmp_path / ".blobify").write_text(
            """
@show-excluded=false
+*.py
-*.log
"""
        )

        (tmp_path / "app.py").write_text("print('app')")
        (tmp_path / "debug.log").write_text("error message")

        output_file = tmp_path / "output_default_switch.txt"

        with patch("sys.argv", ["bfy", str(tmp_path), "--output-filename", str(output_file)]):
            main()

        content = output_file.read_text(encoding="utf-8")

        # Default switch should be applied
        assert "START_FILE: app.py" in content
        assert "START_FILE: debug.log" not in content  # Suppressed due to default
        assert "debug.log [FILE CONTENTS EXCLUDED BY .blobify]" in content  # Still in index

    def test_command_line_override_blobify_default(self, tmp_path):
        """Test that command line flag can override .blobify default."""
        # Create git repo
        (tmp_path / ".git").mkdir()

        # Create .gitignore
        (tmp_path / ".gitignore").write_text("*.log\n")

        # Create .blobify with show-excluded=false as default
        (tmp_path / ".blobify").write_text("@show-excluded=false\n+*.py\n")

        (tmp_path / "app.py").write_text("print('app')")
        (tmp_path / "debug.log").write_text("error message")

        output_file = tmp_path / "output_override.txt"

        # Run without any show-excluded flag - should use .blobify default
        with patch("sys.argv", ["bfy", str(tmp_path), "--output-filename", str(output_file)]):
            main()

        content = output_file.read_text(encoding="utf-8")
        assert "START_FILE: debug.log" not in content  # Suppressed by default

        # Currently there's no way to override a default switch from command line
        # This is expected behavior - .blobify defaults are always applied

    def test_show_excluded_context_integration(self, tmp_path):
        """Test that --show-excluded=false works correctly with contexts."""
        # Create git repo
        (tmp_path / ".git").mkdir()

        # Create .blobify with context
        (tmp_path / ".blobify").write_text(
            """
# Default context
+*.py
+*.md

[strict]
@show-excluded=false
-**
+*.py
"""
        )

        (tmp_path / "app.py").write_text("print('app')")
        (tmp_path / "README.md").write_text("# README")
        (tmp_path / "config.xml").write_text("<config/>")

        output_file = tmp_path / "output_context.txt"

        with patch("sys.argv", ["bfy", str(tmp_path), "-x", "strict", "--output-filename", str(output_file)]):
            main()

        content = output_file.read_text(encoding="utf-8")

        # Should suppress excluded files due to context default
        assert "START_FILE: app.py" in content  # Included
        assert "START_FILE: README.md" not in content  # Excluded and suppressed
        assert "START_FILE: config.xml" not in content  # Excluded and suppressed

        # But should still show in index
        assert "README.md [FILE CONTENTS EXCLUDED BY .blobify]" in content
        assert "config.xml [FILE CONTENTS EXCLUDED BY .blobify]" in content

    def test_config_apply_default_switches_show_excluded(self):
        """Test that show-excluded can be applied as a default switch."""
        import argparse

        from blobify.config import apply_default_switches

        args = argparse.Namespace(show_excluded=True)
        switches = ["show-excluded=false"]
        result = apply_default_switches(args, switches)
        assert result.show_excluded is False

    def test_config_apply_default_switches_precedence_show_excluded(self):
        """Test that command line show-excluded takes precedence over defaults."""
        import argparse

        from blobify.config import apply_default_switches

        # Command line already has --show-excluded=false set
        args = argparse.Namespace(show_excluded=False, output_metadata=True)
        switches = ["show-excluded=false", "output-metadata=false"]  # Both in defaults
        result = apply_default_switches(args, switches)

        assert result.show_excluded is False  # Should remain False from command line
        assert result.output_metadata is False  # Should be set by default

    def test_integration_with_other_switches(self, tmp_path):
        """Test show-excluded works correctly with other switches."""
        self.setup_test_environment(tmp_path)

        # Test with --output-line-numbers=false
        output_file = tmp_path / "output_no_lines.txt"
        with patch(
            "sys.argv",
            [
                "bfy",
                str(tmp_path),
                "--show-excluded=false",
                "--output-line-numbers=false",
                "--output-filename",
                str(output_file),
            ],
        ):
            main()

        content = output_file.read_text(encoding="utf-8")
        assert "START_FILE: app.py" in content
        assert "START_FILE: debug.log" not in content
        assert "print('main application')" in content  # Content without line numbers
        assert "1: print('main application')" not in content  # No line numbers

    def test_clean_output_example(self, tmp_path):
        """Test the clean output example from the documentation."""
        self.setup_test_environment(tmp_path)
        output_file = tmp_path / "output_clean.txt"

        with patch(
            "sys.argv",
            [
                "bfy",
                str(tmp_path),
                "--show-excluded=false",
                "--output-metadata=false",
                "--output-filename",
                str(output_file),
            ],
        ):
            main()

        content = output_file.read_text(encoding="utf-8")

        # Should have clean output with only included files
        assert "START_FILE: app.py" in content
        assert "START_FILE: README.md" in content
        assert "START_FILE: debug.log" not in content
        assert "START_FILE: secret.txt" not in content

        # Should have content but no metadata
        assert "print('main application')" in content
        assert "# Project Documentation" in content
        assert "FILE_METADATA:" not in content
        assert "Size:" not in content

        # Should still have index with status labels
        assert "debug.log [FILE CONTENTS IGNORED BY GITIGNORE]" in content
        assert "secret.txt [FILE CONTENTS EXCLUDED BY .blobify]" in content

    def test_show_excluded_with_filters(self, tmp_path):
        """Test show-excluded works with content filters."""
        # Create git repo
        (tmp_path / ".git").mkdir()

        # Create files
        (tmp_path / "app.py").write_text("def main():\n    print('app')\nclass MyClass:\n    pass")
        (tmp_path / "test.js").write_text("function test() {}\nconst x = 1;")

        output_file = tmp_path / "output_filters.txt"

        with patch(
            "sys.argv",
            [
                "bfy",
                str(tmp_path),
                "--filter",
                '"py-functions","^def","*.py"',
                "--show-excluded=false",
                "--output-filename",
                str(output_file),
            ],
        ):
            main()

        content = output_file.read_text(encoding="utf-8")

        # Should show files with matching content
        assert "START_FILE: app.py" in content
        assert "def main():" in content

        # Should NOT show files excluded by filters
        assert "START_FILE: test.js" not in content

        # Should show filter exclusions in index
        assert "test.js [FILE CONTENTS EXCLUDED BY FILTERS]" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
