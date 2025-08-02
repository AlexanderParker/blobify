"""Tests for all switch combinations - comprehensive coverage of --no-content, --no-index, --no-metadata."""

from unittest.mock import patch

from blobify.main import main


class TestSwitchCombinations:
    """Test all meaningful combinations of --no-content, --no-index, --no-metadata switches."""

    def setup_test_files(self, tmp_path):
        """Create standard test files for switch combination tests."""
        # Create git repo
        (tmp_path / ".git").mkdir()

        # Create .gitignore
        (tmp_path / ".gitignore").write_text("*.log\n")

        # Create .blobify
        (tmp_path / ".blobify").write_text("+.blobify\n+*.py\n-secret.txt\n")

        # Create various files
        (tmp_path / "app.py").write_text("print('hello world')\n# This is a comment")
        (tmp_path / "README.md").write_text("# Test Project\n\nThis is a README file.")
        (tmp_path / "debug.log").write_text("ERROR: something went wrong")
        (tmp_path / "secret.txt").write_text("password=secret123")

        return tmp_path

    def test_default_all_enabled(self, tmp_path):
        """Test default behavior: index + content + metadata all enabled."""
        self.setup_test_files(tmp_path)
        output_file = tmp_path / "output.txt"

        with patch("sys.argv", ["bfy", str(tmp_path), "-o", str(output_file)]):
            main()

        content = output_file.read_text(encoding="utf-8")

        # Should have all sections
        assert "# FILE INDEX" in content
        assert "# FILE CONTENTS" in content
        assert "START_FILE:" in content
        assert "FILE_METADATA:" in content
        assert "Size:" in content
        assert "Status:" in content
        assert "print('hello world')" in content
        assert "1: print('hello world')" in content  # Line numbers

        # Should show status labels in index
        assert "[FILE CONTENTS IGNORED BY GITIGNORE]" in content
        assert "[FILE CONTENTS INCLUDED BY .blobify]" in content

    def test_no_content_only(self, tmp_path):
        """Test --no-content: index + metadata, no content."""
        self.setup_test_files(tmp_path)
        output_file = tmp_path / "output.txt"

        with patch("sys.argv", ["bfy", str(tmp_path), "--no-content", "-o", str(output_file)]):
            main()

        content = output_file.read_text(encoding="utf-8")

        # Should have index and metadata but no content
        assert "# FILE INDEX" in content
        assert "START_FILE:" in content
        assert "FILE_METADATA:" in content
        assert "Size:" in content

        # Should NOT have content sections or status labels
        assert "# FILE CONTENTS" not in content
        assert "FILE_CONTENT:" not in content
        assert "print('hello world')" not in content
        assert "Status:" not in content  # No status when no content
        assert "[FILE CONTENTS IGNORED BY GITIGNORE]" not in content  # No status labels in index
        assert "[FILE CONTENTS INCLUDED BY .blobify]" not in content

    def test_no_index_only(self, tmp_path):
        """Test --no-index: content + metadata, no index."""
        self.setup_test_files(tmp_path)
        output_file = tmp_path / "output.txt"

        with patch("sys.argv", ["bfy", str(tmp_path), "--no-index", "-o", str(output_file)]):
            main()

        content = output_file.read_text(encoding="utf-8")

        # Should have content and metadata but no index
        assert "# FILE INDEX" not in content
        assert "# FILE CONTENTS" in content
        assert "START_FILE:" in content
        assert "FILE_METADATA:" in content
        assert "FILE_CONTENT:" in content
        assert "print('hello world')" in content
        assert "Status:" in content

    def test_no_metadata_only(self, tmp_path):
        """Test --no-metadata: index + content, no metadata."""
        self.setup_test_files(tmp_path)
        output_file = tmp_path / "output.txt"

        with patch("sys.argv", ["bfy", str(tmp_path), "--no-metadata", "-o", str(output_file)]):
            main()

        content = output_file.read_text(encoding="utf-8")

        # Should have index and content but no metadata
        assert "# FILE INDEX" in content
        assert "# FILE CONTENTS" in content
        assert "START_FILE:" in content
        assert "FILE_CONTENT:" in content
        assert "print('hello world')" in content

        # Should NOT have metadata sections
        assert "FILE_METADATA:" not in content
        assert "Size:" not in content
        assert "Created:" not in content

    def test_no_content_no_index_metadata_only(self, tmp_path):
        """Test --no-content --no-index: metadata only."""
        self.setup_test_files(tmp_path)
        output_file = tmp_path / "output.txt"

        with patch("sys.argv", ["bfy", str(tmp_path), "--no-content", "--no-index", "-o", str(output_file)]):
            main()

        content = output_file.read_text(encoding="utf-8")

        # Should only have metadata sections
        assert "# FILE INDEX" not in content
        assert "# FILE CONTENTS" not in content
        assert "START_FILE:" in content  # Still has file sections for metadata
        assert "FILE_METADATA:" in content
        assert "Size:" in content

        # Should NOT have content or status
        assert "FILE_CONTENT:" not in content
        assert "print('hello world')" not in content
        assert "Status:" not in content

        # Header should describe metadata output
        assert "This file contains metadata of all text files" in content

    def test_no_content_no_metadata_index_only(self, tmp_path):
        """Test --no-content --no-metadata: index only."""
        self.setup_test_files(tmp_path)
        output_file = tmp_path / "output.txt"

        with patch("sys.argv", ["bfy", str(tmp_path), "--no-content", "--no-metadata", "-o", str(output_file)]):
            main()

        content = output_file.read_text(encoding="utf-8")

        # Should only have index
        assert "# FILE INDEX" in content
        assert "# FILE CONTENTS" not in content
        assert "START_FILE:" not in content
        assert "FILE_METADATA:" not in content
        assert "FILE_CONTENT:" not in content
        assert "print('hello world')" not in content

    def test_no_index_no_metadata_content_only(self, tmp_path):
        """Test --no-index --no-metadata: content only."""
        self.setup_test_files(tmp_path)
        output_file = tmp_path / "output.txt"

        with patch("sys.argv", ["bfy", str(tmp_path), "--no-index", "--no-metadata", "-o", str(output_file)]):
            main()

        content = output_file.read_text(encoding="utf-8")

        # Should only have content
        assert "# FILE INDEX" not in content
        assert "# FILE CONTENTS" in content
        assert "START_FILE:" in content
        assert "FILE_CONTENT:" in content
        assert "print('hello world')" in content

        # Should NOT have metadata
        assert "FILE_METADATA:" not in content
        assert "Size:" not in content

    def test_all_disabled_no_useful_output(self, tmp_path):
        """Test --no-content --no-index --no-metadata: no useful output."""
        self.setup_test_files(tmp_path)
        output_file = tmp_path / "output.txt"

        with patch("sys.argv", ["bfy", str(tmp_path), "--no-content", "--no-index", "--no-metadata", "-o", str(output_file)]):
            main()

        content = output_file.read_text(encoding="utf-8")

        # Should have minimal output
        assert "# FILE INDEX" not in content
        assert "# FILE CONTENTS" not in content
        assert "START_FILE:" not in content
        assert "FILE_METADATA:" not in content
        assert "FILE_CONTENT:" not in content
        assert "print('hello world')" not in content

        # Header should indicate no useful output
        assert "no useful output - index, content, and metadata have all been disabled" in content

    def test_header_descriptions_accuracy(self, tmp_path):
        """Test that header descriptions accurately reflect the output contents."""
        self.setup_test_files(tmp_path)

        test_cases = [
            # (switches, expected_description)
            ([], "index and contents of all text files"),
            (["--no-metadata"], "index and contents of all text files"),  # Still has index and content
            (["--no-content"], "index and metadata of all text files"),
            (["--no-index"], "contents of all text files"),
            (["--no-content", "--no-metadata"], "index of all text files"),
            (["--no-content", "--no-index"], "metadata of all text files"),
            (["--no-index", "--no-metadata"], "contents of all text files"),
            (["--no-content", "--no-index", "--no-metadata"], "no useful output"),
        ]

        for switches, expected_desc in test_cases:
            output_file = tmp_path / f"output_{'_'.join(switches)}.txt"

            with patch("sys.argv", ["bfy", str(tmp_path)] + switches + ["-o", str(output_file)]):
                main()

            content = output_file.read_text(encoding="utf-8")
            assert expected_desc in content, f"Failed for {switches}: expected '{expected_desc}' in header"

    def test_status_labels_only_with_content(self, tmp_path):
        """Test that status labels appear only when content is enabled."""
        self.setup_test_files(tmp_path)

        # With content: should show status labels in index and metadata
        output_file = tmp_path / "with_content.txt"
        with patch("sys.argv", ["bfy", str(tmp_path), "-o", str(output_file)]):
            main()

        content = output_file.read_text(encoding="utf-8")
        assert "[FILE CONTENTS IGNORED BY GITIGNORE]" in content
        assert "[FILE CONTENTS INCLUDED BY .blobify]" in content
        assert "Status: INCLUDED BY .blobify" in content

        # Without content: should NOT show status labels anywhere
        output_file2 = tmp_path / "no_content.txt"
        with patch("sys.argv", ["bfy", str(tmp_path), "--no-content", "-o", str(output_file2)]):
            main()

        content2 = output_file2.read_text(encoding="utf-8")
        assert "[FILE CONTENTS IGNORED BY GITIGNORE]" not in content2
        assert "[FILE CONTENTS INCLUDED BY .blobify]" not in content2
        assert "Status:" not in content2

    def test_line_numbers_enabled_by_default(self, tmp_path):
        """Test that line numbers are shown by default when content is enabled."""
        self.setup_test_files(tmp_path)

        output_file = tmp_path / "with_lines.txt"
        with patch("sys.argv", ["bfy", str(tmp_path), "-o", str(output_file)]):
            main()

        content = output_file.read_text(encoding="utf-8")
        assert "1: print('hello world')" in content

    def test_no_line_numbers_flag_disables_line_numbers(self, tmp_path):
        """Test that --no-line-numbers flag disables line numbers in content."""
        self.setup_test_files(tmp_path)

        output_file = tmp_path / "no_line_numbers.txt"
        with patch("sys.argv", ["bfy", str(tmp_path), "--no-line-numbers", "-o", str(output_file)]):
            main()

        content = output_file.read_text(encoding="utf-8")
        assert "print('hello world')" in content  # Content present
        assert "1: print('hello world')" not in content  # No line numbers

    def test_no_content_flag_excludes_all_content_and_line_numbers(self, tmp_path):
        """Test that --no-content flag excludes all file content including line numbers."""
        self.setup_test_files(tmp_path)

        output_file = tmp_path / "no_content.txt"
        with patch("sys.argv", ["bfy", str(tmp_path), "--no-content", "-o", str(output_file)]):
            main()

        content = output_file.read_text(encoding="utf-8")
        assert "1: print('hello world')" not in content
        assert "print('hello world')" not in content  # No content at all


class TestSwitchCombinationsWithContext:
    """Test switch combinations work correctly with .blobify contexts."""

    def test_context_with_no_content(self, tmp_path):
        """Test that contexts work with --no-content."""
        # Create git repo
        (tmp_path / ".git").mkdir()

        # Create .blobify with context
        (tmp_path / ".blobify").write_text(
            """
# Default context
+*.py

[docs-only]
-**
+*.md
+docs/**
"""
        )

        (tmp_path / "app.py").write_text("print('app')")
        (tmp_path / "README.md").write_text("# README")

        output_file = tmp_path / "output.txt"
        with patch("sys.argv", ["bfy", str(tmp_path), "-x", "docs-only", "--no-content", "-o", str(output_file)]):
            main()

        content = output_file.read_text(encoding="utf-8")

        # Should include ALL files in index (contexts don't filter the file discovery)
        assert "README.md" in content
        assert "app.py" in content  # All files appear in index

        # Should not show content (due to --no-content) or status labels
        assert "# README" not in content
        assert "print('app')" not in content
        assert "[FILE CONTENTS EXCLUDED BY .blobify]" not in content  # No status labels when --no-content

    def test_context_with_all_switches(self, tmp_path):
        """Test context works with various switch combinations."""
        # Create git repo
        (tmp_path / ".git").mkdir()

        # Create .blobify with context and default switches
        (tmp_path / ".blobify").write_text(
            """
[minimal]
@no-content
@no-metadata
-**
+*.py
+*.md
"""
        )

        (tmp_path / "app.py").write_text("print('app')")
        (tmp_path / "README.md").write_text("# README")
        (tmp_path / "config.xml").write_text("<config/>")

        output_file = tmp_path / "output.txt"
        with patch("sys.argv", ["bfy", str(tmp_path), "-x", "minimal", "-o", str(output_file)]):
            main()

        content = output_file.read_text(encoding="utf-8")

        # Should include ALL discovered files in index (contexts don't filter discovery)
        assert "app.py" in content
        assert "README.md" in content
        assert "config.xml" in content  # All files appear in index

        # Default switches should apply
        assert "# FILE CONTENTS" not in content  # no-content applied
        assert "FILE_METADATA:" not in content  # no-metadata applied
        assert "# FILE INDEX" in content  # Index still enabled

    def test_context_with_content_filtering(self, tmp_path):
        """Test that context patterns control content inclusion when content is enabled."""
        # Create git repo
        (tmp_path / ".git").mkdir()

        # Create .blobify with context that excludes everything then includes specific files
        (tmp_path / ".blobify").write_text(
            """
[docs-only]
-**
+*.md
"""
        )

        (tmp_path / "app.py").write_text("print('app code')")
        (tmp_path / "README.md").write_text("# README content")

        output_file = tmp_path / "output.txt"
        with patch("sys.argv", ["bfy", str(tmp_path), "-x", "docs-only", "-o", str(output_file)]):
            main()

        content = output_file.read_text(encoding="utf-8")

        # All files should appear in index
        assert "app.py" in content
        assert "README.md" in content

        # But content should be filtered by context patterns
        assert "# README content" in content  # .md file content included
        assert "print('app code')" not in content  # .py file content excluded

        # Should show appropriate exclusion status
        assert "[FILE CONTENTS EXCLUDED BY .blobify]" in content  # For the excluded files


class TestConfigSwitchDefaults:
    """Test configuration handling for switch defaults in .blobify files."""

    def test_apply_default_switches_no_content(self):
        """Test applying no-content default switch."""
        import argparse

        from blobify.config import apply_default_switches

        args = argparse.Namespace(no_content=False)
        switches = ["no-content"]
        result = apply_default_switches(args, switches)
        assert result.no_content is True

    def test_apply_default_switches_no_metadata(self):
        """Test applying no-metadata default switch."""
        import argparse

        from blobify.config import apply_default_switches

        args = argparse.Namespace(no_metadata=False)
        switches = ["no-metadata"]
        result = apply_default_switches(args, switches)
        assert result.no_metadata is True

    def test_apply_default_switches_no_index(self):
        """Test applying no-index default switch."""
        import argparse

        from blobify.config import apply_default_switches

        args = argparse.Namespace(no_index=False)
        switches = ["no-index"]
        result = apply_default_switches(args, switches)
        assert result.no_index is True

    def test_apply_default_switches_precedence(self):
        """Test that command line switches take precedence over defaults."""
        import argparse

        from blobify.config import apply_default_switches

        # Command line already has --no-content set
        args = argparse.Namespace(no_content=True, no_metadata=False)
        switches = ["no-content", "no-metadata"]  # Both in defaults
        result = apply_default_switches(args, switches)

        assert result.no_content is True  # Should remain True from command line
        assert result.no_metadata is True  # Should be set by default

    def test_blobify_default_switches_integration(self, tmp_path):
        """Test that default switches from .blobify file are applied."""
        # Create git repo
        (tmp_path / ".git").mkdir()

        # Create .blobify with default switches
        (tmp_path / ".blobify").write_text("@no-content\n@no-metadata\n+*.py\n")
        (tmp_path / "test.py").write_text("print('should not appear')")

        output_file = tmp_path / "output.txt"
        with patch("sys.argv", ["bfy", str(tmp_path), "-o", str(output_file)]):
            main()

        content = output_file.read_text(encoding="utf-8")

        # Default switches should be applied
        assert "# FILE INDEX" in content  # Index still enabled
        assert "FILE_METADATA:" not in content  # no-metadata applied
        assert "FILE_CONTENT:" not in content  # no-content applied
        assert "print('should not appear')" not in content
