"""Tests for the --no-content feature."""

from unittest.mock import patch

from blobify.main import main


class TestNoContentFeature:
    """Test cases for the --no-content command line option."""

    def test_no_content_short_flag(self, tmp_path):
        """Test --no-content with short flag -k."""
        # Create test files
        (tmp_path / "test.py").write_text("print('this content should not appear')")
        (tmp_path / "README.md").write_text("# This content should not appear")

        # Use file output to avoid capture issues
        output_file = tmp_path / "output.txt"
        with patch("sys.argv", ["bfy", str(tmp_path), "-k", "-o", str(output_file)]):
            main()

        content = output_file.read_text(encoding="utf-8")

        # Should have file index but no file content sections
        assert "# Blobify Text File Index" in content
        assert "# FILE INDEX" in content
        assert "test.py" in content
        assert "README.md" in content

        # Should indicate content is disabled
        assert "# File contents DISABLED (--no-content flag used)" in content

        # Should NOT have any file content sections
        assert "# FILE CONTENTS" not in content
        assert "START_FILE:" not in content
        assert "FILE_METADATA:" not in content

        # Should NOT contain actual file contents
        assert "print('this content should not appear')" not in content
        assert "# This content should not appear" not in content

    def test_no_content_long_flag(self, tmp_path):
        """Test --no-content with long flag."""
        (tmp_path / "script.js").write_text("console.log('secret content');")

        output_file = tmp_path / "output.txt"
        with patch("sys.argv", ["bfy", str(tmp_path), "--no-content", "-o", str(output_file)]):
            main()

        content = output_file.read_text(encoding="utf-8")
        assert "# File contents DISABLED (--no-content flag used)" in content
        assert "# FILE CONTENTS" not in content
        assert "START_FILE:" not in content
        assert "console.log('secret content');" not in content

    def test_no_content_with_gitignore(self, tmp_path):
        """Test --no-content respects gitignore status in metadata."""
        # Create git repo with .gitignore
        (tmp_path / ".git").mkdir()
        (tmp_path / ".gitignore").write_text("*.log\n")

        # Create files
        (tmp_path / "app.py").write_text("print('app code')")
        (tmp_path / "debug.log").write_text("log content")

        output_file = tmp_path / "output.txt"
        with patch("sys.argv", ["bfy", str(tmp_path), "--no-content", "-o", str(output_file)]):
            main()

        content = output_file.read_text(encoding="utf-8")

        # Should show both files in index with correct status
        assert "app.py" in content
        assert "debug.log [IGNORED BY GITIGNORE]" in content

        # Should not have any file content sections
        assert "# FILE CONTENTS" not in content
        assert "START_FILE:" not in content

        # Should not show any actual content
        assert "print('app code')" not in content
        assert "log content" not in content

    def test_no_content_with_blobify_config(self, tmp_path):
        """Test --no-content with .blobify configuration."""
        # Create git repo with .blobify config
        (tmp_path / ".git").mkdir()
        (tmp_path / ".blobify").write_text("+*.py\n-*.log\n")

        # Create files
        (tmp_path / "app.py").write_text("print('included')")
        (tmp_path / "debug.log").write_text("excluded log")
        (tmp_path / "README.md").write_text("# Normal file")

        output_file = tmp_path / "output.txt"
        with patch("sys.argv", ["bfy", str(tmp_path), "--no-content", "-o", str(output_file)]):
            main()

        content = output_file.read_text(encoding="utf-8")

        # Should show correct statuses
        assert "app.py" in content
        assert "debug.log [EXCLUDED BY .blobify]" in content
        assert "README.md" in content

        # Should not show any content
        assert "print('included')" not in content
        assert "excluded log" not in content
        assert "# Normal file" not in content

    def test_no_content_default_from_blobify(self, tmp_path):
        """Test --no-content can be set as default in .blobify."""
        # Create git repo
        (tmp_path / ".git").mkdir()

        # Create .blobify with no-content default
        (tmp_path / ".blobify").write_text("@no-content\n+*.py\n")
        (tmp_path / "test.py").write_text("print('should not appear')")

        output_file = tmp_path / "output.txt"
        with patch("sys.argv", ["bfy", str(tmp_path), "-o", str(output_file)]):
            main()

        content = output_file.read_text(encoding="utf-8")
        assert "[Content excluded - --no-content flag used]" in content
        assert "print('should not appear')" not in content

    def test_no_content_summary_message(self, tmp_path, capsys):
        """Test that summary message indicates index-only mode."""
        (tmp_path / "test.py").write_text("test content")

        with patch("sys.argv", ["bfy", str(tmp_path), "--no-content"]):
            main()

        # Check that summary indicates index-only
        captured = capsys.readouterr()
        assert "(index only)" in captured.err

    def test_no_content_with_context(self, tmp_path):
        """Test --no-content works with contexts."""
        # Create git repo with context
        (tmp_path / ".git").mkdir()
        (tmp_path / ".blobify").write_text(
            """
[overview]
@no-content
+*.py
+*.md
"""
        )

        (tmp_path / "app.py").write_text("python code")
        (tmp_path / "README.md").write_text("# Documentation")
        (tmp_path / "config.xml").write_text("<config/>")  # Should be excluded

        output_file = tmp_path / "output.txt"
        with patch("sys.argv", ["bfy", str(tmp_path), "-x", "overview", "-o", str(output_file)]):
            main()

        content = output_file.read_text(encoding="utf-8")

        # Should include files matched by context in the index
        assert "app.py" in content
        assert "README.md" in content

        # Should not have any file content sections
        assert "# FILE CONTENTS" not in content
        assert "START_FILE:" not in content

        # Should not include content or non-matching files
        assert "python code" not in content
        assert "# Documentation" not in content
        assert "config.xml" not in content  # File not matched by context patterns

    def test_no_content_overrides_line_numbers(self, tmp_path):
        """Test that --no-content makes line numbers irrelevant."""
        (tmp_path / "test.py").write_text("line1\nline2\nline3")

        output_file = tmp_path / "output.txt"
        # Even with line numbers enabled, shouldn't matter with no-content
        with patch("sys.argv", ["bfy", str(tmp_path), "--no-content", "-o", str(output_file)]):
            main()

        content = output_file.read_text(encoding="utf-8")
        assert "[Content excluded - --no-content flag used]" in content
        assert "1: line1" not in content
        assert "line1" not in content

    def test_no_content_still_processes_metadata(self, tmp_path):
        """Test that --no-content produces clean index-only output."""
        test_file = tmp_path / "test.py"
        test_content = "def hello():\n    return 'world'"
        test_file.write_text(test_content)

        output_file = tmp_path / "output.txt"
        with patch("sys.argv", ["bfy", str(tmp_path), "--no-content", "-o", str(output_file)]):
            main()

        content = output_file.read_text(encoding="utf-8")

        # Should have the file in the index
        assert "test.py" in content
        assert "# FILE INDEX" in content

        # Should not have any file content sections
        assert "# FILE CONTENTS" not in content
        assert "START_FILE:" not in content
        assert "FILE_METADATA:" not in content

        # Should indicate content is disabled in header
        assert "# File contents DISABLED (--no-content flag used)" in content

    def test_no_content_with_no_index_combination(self, tmp_path):
        """Test --no-content with --no-index combination."""
        (tmp_path / "test.py").write_text("some_file_content")

        output_file = tmp_path / "output.txt"
        with patch("sys.argv", ["bfy", str(tmp_path), "--no-content", "--no-index", "-o", str(output_file)]):
            main()

        content = output_file.read_text(encoding="utf-8")

        # Should not have index or content sections
        assert "# FILE INDEX" not in content
        assert "# FILE CONTENTS" not in content
        assert "START_FILE:" not in content

        # Should have header indicating both are disabled
        assert "# File contents DISABLED (--no-content flag used)" in content

        # Should not have any file content
        assert "some_file_content" not in content


# Additional tests for config.py
class TestConfigNoContent:
    """Test configuration handling for no-content switch."""

    def test_apply_default_switches_no_content(self):
        """Test applying no-content default switch."""
        import argparse

        from blobify.config import apply_default_switches

        args = argparse.Namespace(no_content=False)
        switches = ["no-content"]
        result = apply_default_switches(args, switches)
        assert result.no_content is True

    def test_apply_default_switches_no_content_precedence(self):
        """Test that command line --no-content takes precedence over default."""
        import argparse

        from blobify.config import apply_default_switches

        args = argparse.Namespace(no_content=True)  # Already set via command line
        switches = ["no-content"]  # Also in defaults
        result = apply_default_switches(args, switches)
        assert result.no_content is True  # Should remain True


# Additional tests for output_formatter.py
class TestOutputFormatterNoContent:
    """Test output formatter no-content functionality."""

    def test_generate_header_no_content(self, tmp_path):
        """Test header generation with no-content flag."""
        from blobify.output_formatter import generate_header

        header = generate_header(tmp_path, None, None, False, ([], [], []), include_index=True, include_content=False)

        assert "# File contents DISABLED (--no-content flag used)" in header
        assert "File contents are excluded due to --no-content flag" in header

    def test_generate_content_no_content(self, tmp_path):
        """Test content generation with no-content flag."""

        from blobify.output_formatter import generate_content

        test_file = tmp_path / "test.py"
        test_file.write_text("print('secret')")

        all_files = [
            {
                "path": test_file,
                "relative_path": test_file.relative_to(tmp_path),
                "is_git_ignored": False,
                "is_blobify_excluded": False,
                "is_blobify_included": False,
            }
        ]

        content, substitutions = generate_content(all_files, scrub_data=False, include_line_numbers=True, include_content=False, debug=False)

        # When content is disabled, should return empty string
        assert content == ""
        assert substitutions == 0
