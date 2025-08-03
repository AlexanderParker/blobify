"""Tests for all switch combinations - comprehensive coverage of configuration options."""

from unittest.mock import patch

from blobify.main import main


class TestConfigurationOptionCombinations:
    """Test all meaningful combinations of configuration options."""

    def setup_test_files(self, tmp_path):
        """Create standard test files for configuration option tests."""
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

        with patch("sys.argv", ["bfy", str(tmp_path), "--output-filename", str(output_file)]):
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

    def test_output_content_false_only(self, tmp_path):
        """Test --output-content=false: index + metadata, no content."""
        self.setup_test_files(tmp_path)
        output_file = tmp_path / "output.txt"

        with patch("sys.argv", ["bfy", str(tmp_path), "--output-content=false", "--output-filename", str(output_file)]):
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

    def test_output_index_false_only(self, tmp_path):
        """Test --output-index=false: content + metadata, no index."""
        self.setup_test_files(tmp_path)
        output_file = tmp_path / "output.txt"

        with patch("sys.argv", ["bfy", str(tmp_path), "--output-index=false", "--output-filename", str(output_file)]):
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

    def test_output_metadata_false_only(self, tmp_path):
        """Test --output-metadata=false: index + content, no metadata."""
        self.setup_test_files(tmp_path)
        output_file = tmp_path / "output.txt"

        with patch("sys.argv", ["bfy", str(tmp_path), "--output-metadata=false", "--output-filename", str(output_file)]):
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

    def test_output_content_false_output_index_false_metadata_only(self, tmp_path):
        """Test --output-content=false --output-index=false: metadata only."""
        self.setup_test_files(tmp_path)
        output_file = tmp_path / "output.txt"

        with patch(
            "sys.argv",
            [
                "bfy",
                str(tmp_path),
                "--output-content=false",
                "--output-index=false",
                "--output-filename",
                str(output_file),
            ],
        ):
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

    def test_output_content_false_output_metadata_false_index_only(self, tmp_path):
        """Test --output-content=false --output-metadata=false: index only."""
        self.setup_test_files(tmp_path)
        output_file = tmp_path / "output.txt"

        with patch(
            "sys.argv",
            [
                "bfy",
                str(tmp_path),
                "--output-content=false",
                "--output-metadata=false",
                "--output-filename",
                str(output_file),
            ],
        ):
            main()

        content = output_file.read_text(encoding="utf-8")

        # Should only have index
        assert "# FILE INDEX" in content
        assert "# FILE CONTENTS" not in content
        assert "START_FILE:" not in content
        assert "FILE_METADATA:" not in content
        assert "FILE_CONTENT:" not in content
        assert "print('hello world')" not in content

    def test_output_index_false_output_metadata_false_content_only(self, tmp_path):
        """Test --output-index=false --output-metadata=false: content only."""
        self.setup_test_files(tmp_path)
        output_file = tmp_path / "output.txt"

        with patch(
            "sys.argv",
            [
                "bfy",
                str(tmp_path),
                "--output-index=false",
                "--output-metadata=false",
                "--output-filename",
                str(output_file),
            ],
        ):
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
        """Test --output-content=false --output-index=false --output-metadata=false: no useful output."""
        self.setup_test_files(tmp_path)
        output_file = tmp_path / "output.txt"

        with patch(
            "sys.argv",
            [
                "bfy",
                str(tmp_path),
                "--output-content=false",
                "--output-index=false",
                "--output-metadata=false",
                "--output-filename",
                str(output_file),
            ],
        ):
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
            (["--output-metadata=false"], "index and contents of all text files"),  # Still has index and content
            (["--output-content=false"], "index and metadata of all text files"),
            (["--output-index=false"], "contents of all text files"),
            (["--output-content=false", "--output-metadata=false"], "index of all text files"),
            (["--output-content=false", "--output-index=false"], "metadata of all text files"),
            (["--output-index=false", "--output-metadata=false"], "contents of all text files"),
            (["--output-content=false", "--output-index=false", "--output-metadata=false"], "no useful output"),
        ]

        for switches, expected_desc in test_cases:
            output_file = tmp_path / f"output_{'_'.join(s.replace('--', '').replace('=', '_') for s in switches)}.txt"

            with patch("sys.argv", ["bfy", str(tmp_path)] + switches + ["--output-filename", str(output_file)]):
                main()

            content = output_file.read_text(encoding="utf-8")
            assert expected_desc in content, f"Failed for {switches}: expected '{expected_desc}' in header"

    def test_status_labels_only_with_content(self, tmp_path):
        """Test that status labels appear only when content is enabled."""
        self.setup_test_files(tmp_path)

        # With content: should show status labels in index and metadata
        output_file = tmp_path / "with_content.txt"
        with patch("sys.argv", ["bfy", str(tmp_path), "--output-filename", str(output_file)]):
            main()

        content = output_file.read_text(encoding="utf-8")
        assert "[FILE CONTENTS IGNORED BY GITIGNORE]" in content
        assert "[FILE CONTENTS INCLUDED BY .blobify]" in content
        assert "Status: INCLUDED BY .blobify" in content

        # Without content: should NOT show status labels anywhere
        output_file2 = tmp_path / "no_content.txt"
        with patch("sys.argv", ["bfy", str(tmp_path), "--output-content=false", "--output-filename", str(output_file2)]):
            main()

        content2 = output_file2.read_text(encoding="utf-8")
        assert "[FILE CONTENTS IGNORED BY GITIGNORE]" not in content2
        assert "[FILE CONTENTS INCLUDED BY .blobify]" not in content2
        assert "Status:" not in content2

    def test_line_numbers_enabled_by_default(self, tmp_path):
        """Test that line numbers are shown by default when content is enabled."""
        self.setup_test_files(tmp_path)

        output_file = tmp_path / "with_lines.txt"
        with patch("sys.argv", ["bfy", str(tmp_path), "--output-filename", str(output_file)]):
            main()

        content = output_file.read_text(encoding="utf-8")
        assert "1: print('hello world')" in content

    def test_output_line_numbers_false_disables_line_numbers(self, tmp_path):
        """Test that --output-line-numbers=false flag disables line numbers in content."""
        self.setup_test_files(tmp_path)

        output_file = tmp_path / "no_line_numbers.txt"
        with patch("sys.argv", ["bfy", str(tmp_path), "--output-line-numbers=false", "--output-filename", str(output_file)]):
            main()

        content = output_file.read_text(encoding="utf-8")
        assert "print('hello world')" in content  # Content present
        assert "1: print('hello world')" not in content  # No line numbers

    def test_output_content_false_excludes_all_content_and_line_numbers(self, tmp_path):
        """Test that --output-content=false flag excludes all file content including line numbers."""
        self.setup_test_files(tmp_path)

        output_file = tmp_path / "no_content.txt"
        with patch("sys.argv", ["bfy", str(tmp_path), "--output-content=false", "--output-filename", str(output_file)]):
            main()

        content = output_file.read_text(encoding="utf-8")
        assert "1: print('hello world')" not in content
        assert "print('hello world')" not in content  # No content at all


class TestConfigurationOptionsWithContext:
    """Test configuration options work correctly with .blobify contexts."""

    def test_context_with_output_content_false(self, tmp_path):
        """Test that contexts work with --output-content=false."""
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
        with patch(
            "sys.argv",
            ["bfy", str(tmp_path), "-x", "docs-only", "--output-content=false", "--output-filename", str(output_file)],
        ):
            main()

        content = output_file.read_text(encoding="utf-8")

        # Should include ALL files in index (contexts don't filter the file discovery)
        assert "README.md" in content
        assert "app.py" in content  # All files appear in index

        # Should not show content (due to --output-content=false) or status labels
        assert "# README" not in content
        assert "print('app')" not in content
        assert "[FILE CONTENTS EXCLUDED BY .blobify]" not in content  # No status labels when --output-content=false

    def test_context_with_all_options(self, tmp_path):
        """Test context works with various configuration option combinations."""
        # Create git repo
        (tmp_path / ".git").mkdir()

        # Create .blobify with context and default options
        (tmp_path / ".blobify").write_text(
            """
[minimal]
@output-content=false
@output-metadata=false
-**
+*.py
+*.md
"""
        )

        (tmp_path / "app.py").write_text("print('app')")
        (tmp_path / "README.md").write_text("# README")
        (tmp_path / "config.xml").write_text("<config/>")

        output_file = tmp_path / "output.txt"
        with patch("sys.argv", ["bfy", str(tmp_path), "-x", "minimal", "--output-filename", str(output_file)]):
            main()

        content = output_file.read_text(encoding="utf-8")

        # Should include ALL discovered files in index (contexts don't filter discovery)
        assert "app.py" in content
        assert "README.md" in content
        assert "config.xml" in content  # All files appear in index

        # Default options should apply
        assert "# FILE CONTENTS" not in content  # output-content=false applied
        assert "FILE_METADATA:" not in content  # output-metadata=false applied
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
        with patch("sys.argv", ["bfy", str(tmp_path), "-x", "docs-only", "--output-filename", str(output_file)]):
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

    def test_context_with_filters_csv_format(self, tmp_path):
        """Test context with filters using new CSV format."""
        # Create git repo
        (tmp_path / ".git").mkdir()

        # Create .blobify with context using CSV filter format
        (tmp_path / ".blobify").write_text(
            """
[filtered]
@filter="functions","^(def|function)"
@filter="py-only","^def","*.py"
+*.py
+*.js
"""
        )

        (tmp_path / "test.py").write_text("def python_func():\n    print('py')\nclass PyClass:\n    pass")
        (tmp_path / "test.js").write_text("function js_func() {\n    console.log('js');\n}\nconst x = 1;")

        output_file = tmp_path / "output.txt"
        with patch("sys.argv", ["bfy", str(tmp_path), "-x", "filtered", "--output-filename", str(output_file)]):
            main()

        content = output_file.read_text(encoding="utf-8")

        # Should apply filters from context
        assert "functions: ^(def|function)" in content
        assert "py-only: ^def (files: *.py)" in content

        # Should include content matching filters
        assert "def python_func():" in content  # Matches both filters
        assert "function js_func() {" in content  # Matches first filter only

        # Should exclude non-matching content
        assert "print('py')" not in content
        assert "console.log('js')" not in content
        assert "const x = 1;" not in content


class TestConfigurationOptionDefaults:
    """Test configuration handling for option defaults in .blobify files."""

    def test_apply_default_options_output_content_false(self):
        """Test applying output-content=false default option."""
        import argparse

        from blobify.config import apply_default_switches

        args = argparse.Namespace(output_content=True)
        switches = ["output-content=false"]
        result = apply_default_switches(args, switches)
        assert result.output_content is False

    def test_apply_default_options_output_metadata_false(self):
        """Test applying output-metadata=false default option."""
        import argparse

        from blobify.config import apply_default_switches

        args = argparse.Namespace(output_metadata=True)
        switches = ["output-metadata=false"]
        result = apply_default_switches(args, switches)
        assert result.output_metadata is False

    def test_apply_default_options_output_index_false(self):
        """Test applying output-index=false default option."""
        import argparse

        from blobify.config import apply_default_switches

        args = argparse.Namespace(output_index=True)
        switches = ["output-index=false"]
        result = apply_default_switches(args, switches)
        assert result.output_index is False

    def test_apply_default_options_precedence(self):
        """Test that command line options take precedence over defaults."""
        import argparse

        from blobify.config import apply_default_switches

        # Command line already has --output-content=false set
        args = argparse.Namespace(output_content=False, output_metadata=True)
        switches = ["output-content=false", "output-metadata=false"]  # Both in defaults
        result = apply_default_switches(args, switches)

        assert result.output_content is False  # Should remain False from command line
        assert result.output_metadata is False  # Should be set by default

    def test_blobify_default_options_integration(self, tmp_path):
        """Test that default options from .blobify file are applied."""
        # Create git repo
        (tmp_path / ".git").mkdir()

        # Create .blobify with default options
        (tmp_path / ".blobify").write_text("@output-content=false\n@output-metadata=false\n+*.py\n")
        (tmp_path / "test.py").write_text("print('should not appear')")

        output_file = tmp_path / "output.txt"
        with patch("sys.argv", ["bfy", str(tmp_path), "--output-filename", str(output_file)]):
            main()

        content = output_file.read_text(encoding="utf-8")

        # Default options should be applied
        assert "# FILE INDEX" in content  # Index still enabled
        assert "FILE_METADATA:" not in content  # output-metadata=false applied
        assert "FILE_CONTENT:" not in content  # output-content=false applied
        assert "print('should not appear')" not in content

    def test_blobify_filter_defaults_csv_format(self, tmp_path):
        """Test that filter defaults in .blobify use CSV format."""
        # Create git repo
        (tmp_path / ".git").mkdir()

        # Create .blobify with filter defaults in CSV format
        (tmp_path / ".blobify").write_text(
            """
@filter="functions","^def"
@filter="py-functions","^def","*.py"
+*.py
+*.js
"""
        )

        (tmp_path / "test.py").write_text("def python_func():\n    print('hello')")
        (tmp_path / "test.js").write_text("function js_func() {\n    console.log('hello');\n}")

        output_file = tmp_path / "output.txt"
        with patch("sys.argv", ["bfy", str(tmp_path), "--output-filename", str(output_file)]):
            main()

        content = output_file.read_text(encoding="utf-8")

        # Should apply filter defaults
        assert "functions: ^def" in content
        assert "py-functions: ^def (files: *.py)" in content
        assert "def python_func():" in content
        assert "print('hello')" not in content
        assert "function js_func()" not in content  # Excluded by py-functions filter
        assert "console.log('hello')" not in content
