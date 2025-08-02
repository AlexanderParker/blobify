"""Tests for output_formatter.py module - focused on unit tests only."""

from pathlib import Path
from unittest.mock import patch

from blobify.output_formatter import (
    generate_content,
    generate_index,
)


class TestGenerateIndex:
    """Unit tests for generate_index function."""

    def test_generate_index_with_content_shows_status_labels(self):
        """Test generate_index shows status labels when content is enabled."""
        all_files = [
            {
                "relative_path": Path("normal.py"),
                "is_git_ignored": False,
                "is_blobify_excluded": False,
                "is_blobify_included": False,
            },
            {
                "relative_path": Path("ignored.log"),
                "is_git_ignored": True,
                "is_blobify_excluded": False,
                "is_blobify_included": False,
            },
            {
                "relative_path": Path("included.txt"),
                "is_git_ignored": False,
                "is_blobify_excluded": False,
                "is_blobify_included": True,
            },
            {
                "relative_path": Path("excluded.md"),
                "is_git_ignored": False,
                "is_blobify_excluded": True,
                "is_blobify_included": False,
            },
        ]

        gitignored_directories = [Path("node_modules"), Path("build")]

        # Test with content enabled (should show status labels)
        index = generate_index(all_files, gitignored_directories, include_content=True)

        # Check structure
        assert "# FILE INDEX" in index
        assert "# FILE CONTENTS" in index
        assert "#" * 80 in index

        # Check directory entries with labels
        assert "node_modules [IGNORED BY GITIGNORE]" in index
        assert "build [IGNORED BY GITIGNORE]" in index

        # Check file entries with correct labels
        lines = index.split("\n")
        assert any("normal.py" in line and "[" not in line for line in lines)  # Normal file, no label
        assert "ignored.log [IGNORED BY GITIGNORE]" in index
        assert "included.txt [INCLUDED BY .blobify]" in index
        assert "excluded.md [EXCLUDED BY .blobify]" in index

    def test_generate_index_without_content_clean_listing(self):
        """Test generate_index shows clean listing when content is disabled."""
        all_files = [
            {
                "relative_path": Path("test.py"),
                "is_git_ignored": True,
                "is_blobify_excluded": False,
                "is_blobify_included": False,
            },
            {
                "relative_path": Path("app.js"),
                "is_git_ignored": False,
                "is_blobify_excluded": False,
                "is_blobify_included": True,
            },
        ]

        gitignored_directories = [Path("node_modules")]

        # Test with content disabled (should show clean listing)
        index = generate_index(all_files, gitignored_directories, include_content=False)

        # Should have file index but no file contents header
        assert "# FILE INDEX" in index
        assert "# FILE CONTENTS" not in index

        # Should show files and directories without status labels
        assert "test.py" in index
        assert "app.js" in index
        assert "node_modules" in index

        # Should NOT show any status labels
        assert "[IGNORED BY GITIGNORE]" not in index
        assert "[INCLUDED BY .blobify]" not in index
        assert "[EXCLUDED BY .blobify]" not in index

    def test_generate_index_empty_lists(self):
        """Test generate_index handles empty file and directory lists."""
        index = generate_index([], [], include_content=True)

        assert "# FILE INDEX" in index
        assert "# FILE CONTENTS" in index
        assert "#" * 80 in index

    def test_generate_index_sorting_behavior(self):
        """Test that index entries are properly sorted."""
        all_files = [
            {
                "relative_path": Path("z_last.py"),
                "is_git_ignored": False,
                "is_blobify_excluded": False,
                "is_blobify_included": False,
            },
            {
                "relative_path": Path("a_first.py"),
                "is_git_ignored": False,
                "is_blobify_excluded": False,
                "is_blobify_included": False,
            },
            {
                "relative_path": Path("middle.py"),
                "is_git_ignored": False,
                "is_blobify_excluded": False,
                "is_blobify_included": False,
            },
        ]

        gitignored_directories = [Path("z_dir"), Path("a_dir")]

        index = generate_index(all_files, gitignored_directories, include_content=False)

        # Should include all files and directories
        assert "z_last.py" in index
        assert "a_first.py" in index
        assert "middle.py" in index
        assert "z_dir" in index
        assert "a_dir" in index


class TestGenerateContent:
    """Unit tests for generate_content function."""

    def test_generate_content_with_real_files_all_enabled(self, tmp_path):
        """Test generate_content with all sections enabled."""
        # Create real test files
        py_file = tmp_path / "test.py"
        py_content = "def hello():\n    print('world')\n    return 42"
        py_file.write_text(py_content)

        all_files = [
            {
                "path": py_file,
                "relative_path": Path("test.py"),
                "is_git_ignored": False,
                "is_blobify_excluded": False,
                "is_blobify_included": False,
            },
        ]

        content, substitutions = generate_content(
            all_files,
            scrub_data=False,
            include_line_numbers=True,
            include_content=True,
            include_metadata=True,
            debug=False,
        )

        # Verify complete structure
        assert "START_FILE: test.py" in content
        assert "END_FILE: test.py" in content
        assert "FILE_METADATA:" in content
        assert "FILE_CONTENT:" in content

        # Check metadata
        expected_size = py_file.stat().st_size
        assert f"Size: {expected_size} bytes" in content

        # Verify line numbers
        assert "1: def hello():" in content
        assert "2:     print('world')" in content
        assert "3:     return 42" in content

        assert substitutions == 0

    def test_generate_content_line_numbers_control(self, tmp_path):
        """Test line number inclusion/exclusion independently."""
        test_file = tmp_path / "simple.py"
        test_file.write_text("print('test line')")

        all_files = [
            {
                "path": test_file,
                "relative_path": Path("simple.py"),
                "is_git_ignored": False,
                "is_blobify_excluded": False,
                "is_blobify_included": False,
            }
        ]

        # Without line numbers
        content_no_lines, *_ = generate_content(
            all_files,
            scrub_data=False,
            include_line_numbers=False,
            include_content=True,
            include_metadata=False,
            debug=False,
        )
        assert "print('test line')" in content_no_lines
        assert "1: print('test line')" not in content_no_lines

        # With line numbers
        content_with_lines, *_ = generate_content(
            all_files,
            scrub_data=False,
            include_line_numbers=True,
            include_content=True,
            include_metadata=False,
            debug=False,
        )
        assert "1: print('test line')" in content_with_lines

    def test_generate_content_exclusion_scenarios(self, tmp_path):
        """Test different file exclusion scenarios produce correct messages."""
        # Git ignored file
        git_file = tmp_path / "git_ignored.log"
        git_file.write_text("git content")

        # Blobify excluded file
        blobify_file = tmp_path / "blobify_excluded.txt"
        blobify_file.write_text("blobify content")

        all_files = [
            {
                "path": git_file,
                "relative_path": Path("git_ignored.log"),
                "is_git_ignored": True,
                "is_blobify_excluded": False,
                "is_blobify_included": False,
            },
            {
                "path": blobify_file,
                "relative_path": Path("blobify_excluded.txt"),
                "is_git_ignored": False,
                "is_blobify_excluded": True,
                "is_blobify_included": False,
            },
        ]

        content, *_ = generate_content(
            all_files,
            scrub_data=False,
            include_line_numbers=False,
            include_content=True,
            include_metadata=True,
            debug=False,
        )

        # Check exclusion messages
        assert "[Content excluded - file ignored by .gitignore]" in content
        assert "[Content excluded - file excluded by .blobify]" in content

        # Check actual content is not present
        assert "git content" not in content
        assert "blobify content" not in content

        # Check status in metadata
        assert "Status: IGNORED BY GITIGNORE" in content
        assert "Status: EXCLUDED BY .blobify" in content

    def test_generate_content_file_read_error_handling(self, tmp_path):
        """Test error handling when files cannot be read."""
        # Reference non-existent file
        missing_file = tmp_path / "missing.py"

        all_files = [
            {
                "path": missing_file,
                "relative_path": Path("missing.py"),
                "is_git_ignored": False,
                "is_blobify_excluded": False,
                "is_blobify_included": False,
            }
        ]

        content, *_ = generate_content(
            all_files,
            scrub_data=False,
            include_line_numbers=False,
            include_content=True,
            include_metadata=True,
            debug=False,
        )

        assert "START_FILE: missing.py" in content
        assert "[Error reading file:" in content

    def test_generate_content_both_sections_disabled(self, tmp_path):
        """Test generate_content returns empty when both content and metadata disabled."""
        test_file = tmp_path / "test.py"
        test_file.write_text("print('test')")

        all_files = [
            {
                "path": test_file,
                "relative_path": Path("test.py"),
                "is_git_ignored": False,
                "is_blobify_excluded": False,
                "is_blobify_included": False,
            }
        ]

        content, substitutions = generate_content(
            all_files,
            scrub_data=False,
            include_line_numbers=True,
            include_content=False,
            include_metadata=False,
            debug=False,
        )

        assert content == ""
        assert substitutions == 0

    @patch("blobify.output_formatter.scrub_content")
    def test_generate_content_scrubbing_integration(self, mock_scrub, tmp_path):
        """Test that scrubbing function is called and results integrated properly."""
        mock_scrub.return_value = ("scrubbed content", 3)

        test_file = tmp_path / "test.py"
        test_file.write_text("original content with email@example.com")

        all_files = [
            {
                "path": test_file,
                "relative_path": Path("test.py"),
                "is_git_ignored": False,
                "is_blobify_excluded": False,
                "is_blobify_included": False,
            }
        ]

        content, substitutions = generate_content(
            all_files,
            scrub_data=True,
            include_line_numbers=False,
            include_content=True,
            include_metadata=False,
            debug=False,
        )

        # Should call scrub_content with correct parameters
        mock_scrub.assert_called_once_with("original content with email@example.com", True, False)

        # Should use scrubbed result
        assert "scrubbed content" in content
        assert substitutions == 3

    def test_generate_content_multiline_line_numbering(self, tmp_path):
        """Test line numbering formatting with multi-line content."""
        test_file = tmp_path / "multiline.py"
        # Create content with 10+ lines to test number alignment
        lines = [f"line{i}" for i in range(1, 12)]  # line1 through line11
        test_file.write_text("\n".join(lines))

        all_files = [
            {
                "path": test_file,
                "relative_path": Path("multiline.py"),
                "is_git_ignored": False,
                "is_blobify_excluded": False,
                "is_blobify_included": False,
            }
        ]

        content, *_ = generate_content(
            all_files,
            scrub_data=False,
            include_line_numbers=True,
            include_content=True,
            include_metadata=False,
            debug=False,
        )

        # Check that line numbers are right-aligned properly
        assert " 1: line1" in content  # Single digit with space
        assert " 9: line9" in content  # Single digit with space
        assert "10: line10" in content  # Double digit no extra space
        assert "11: line11" in content  # Double digit no extra space

    def test_generate_content_empty_file_list(self):
        """Test generate_content handles empty file list gracefully."""
        content, substitutions = generate_content([], scrub_data=False, include_line_numbers=True, include_content=True, include_metadata=True, debug=False)

        assert content == ""
        assert substitutions == 0
