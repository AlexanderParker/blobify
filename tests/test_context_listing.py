"""Tests for context listing functionality."""

from unittest.mock import patch

import pytest

from blobify.config import get_available_contexts, get_context_descriptions, list_available_contexts
from blobify.main import main


class TestContextListing:
    """Test cases for context listing functionality."""

    def test_get_available_contexts_basic(self, tmp_path):
        """Test extracting basic context names from .blobify file."""
        blobify_file = tmp_path / ".blobify"
        blobify_file.write_text(
            """
# Default patterns
+*.py

[docs-only]
# Documentation context
+*.md

[signatures]
# Function signatures context
@filter="sigs","^def"
+*.py

[test-context]
# Testing context
-**
+tests/**
"""
        )

        contexts = get_available_contexts(tmp_path)
        assert set(contexts) == {"docs-only", "signatures", "test-context"}

    def test_get_available_contexts_no_file(self, tmp_path):
        """Test get_available_contexts when no .blobify file exists."""
        contexts = get_available_contexts(tmp_path)
        assert contexts == []

    def test_get_available_contexts_no_contexts(self, tmp_path):
        """Test get_available_contexts with .blobify file but no contexts."""
        blobify_file = tmp_path / ".blobify"
        blobify_file.write_text(
            """
# Default patterns only
+*.py
-*.log
@debug=true
"""
        )

        contexts = get_available_contexts(tmp_path)
        assert contexts == []

    def test_get_available_contexts_duplicate_contexts(self, tmp_path):
        """Test that duplicate context names are not returned."""
        blobify_file = tmp_path / ".blobify"
        blobify_file.write_text(
            """
[test]
+*.py

# Some other content

[test]
# This is a duplicate - should not create duplicate entry
+*.md
"""
        )

        contexts = get_available_contexts(tmp_path)
        assert contexts == ["test"]  # Should appear only once

    def test_get_context_descriptions(self, tmp_path):
        """Test extracting context descriptions from comments."""
        blobify_file = tmp_path / ".blobify"
        blobify_file.write_text(
            """
# Default patterns
+*.py

# Documentation files only
[docs-only]
+*.md

# Extract function signatures and imports
# This context is useful for code analysis
[signatures]
@filter="sigs","^def"
+*.py

[no-description]
+*.txt
"""
        )

        descriptions = get_context_descriptions(tmp_path)

        assert descriptions["docs-only"] == "Documentation files only"
        assert descriptions["signatures"] == "This context is useful for code analysis"
        assert "no-description" not in descriptions

    def test_get_context_descriptions_empty_comments(self, tmp_path):
        """Test that empty comments are ignored."""
        blobify_file = tmp_path / ".blobify"
        blobify_file.write_text(
            """
#
#
# Real description here
[test-context]
+*.py
"""
        )

        descriptions = get_context_descriptions(tmp_path)
        assert descriptions["test-context"] == "Real description here"

    def test_get_context_descriptions_comments_cleared_by_patterns(self, tmp_path):
        """Test that comments are cleared when patterns are encountered."""
        blobify_file = tmp_path / ".blobify"
        blobify_file.write_text(
            """
# This comment belongs to default context
+*.py

# This comment should not belong to test-context
-*.log
# But this one should
[test-context]
+*.md
"""
        )

        descriptions = get_context_descriptions(tmp_path)
        assert descriptions["test-context"] == "But this one should"

    def test_list_available_contexts_with_contexts(self, tmp_path, capsys):
        """Test list_available_contexts with available contexts."""
        # Create git repo
        (tmp_path / ".git").mkdir()

        # Create .blobify with contexts and descriptions
        blobify_file = tmp_path / ".blobify"
        blobify_file.write_text(
            """
# Default patterns
+*.py

# Documentation review context
[docs-only]
-**
+*.md

# Code structure analysis
[signatures]
@filter="sigs","^(def|class)"
+*.py

[minimal]
+*.py
"""
        )

        list_available_contexts(tmp_path)

        captured = capsys.readouterr()
        assert "Available contexts:" in captured.out
        assert "docs-only: Documentation review context" in captured.out
        assert "signatures: Code structure analysis" in captured.out
        assert "minimal" in captured.out  # Should appear even without description
        assert "Use with: bfy -x <context-name>" in captured.out

    def test_list_available_contexts_no_contexts(self, tmp_path, capsys):
        """Test list_available_contexts when no contexts exist."""
        # Create git repo
        (tmp_path / ".git").mkdir()

        # Create .blobify with no contexts
        blobify_file = tmp_path / ".blobify"
        blobify_file.write_text(
            """
# Default patterns only
+*.py
-*.log
"""
        )

        list_available_contexts(tmp_path)

        captured = capsys.readouterr()
        assert "No contexts found in .blobify file." in captured.out
        assert "To create contexts, add sections like this" in captured.out
        assert "[docs-only]" in captured.out
        assert "[signatures]" in captured.out
        # Should show new CSV filter format in examples
        assert '@filter="signatures","^(def|class)\\s+"' in captured.out

    def test_list_available_contexts_no_git_repo(self, tmp_path, capsys):
        """Test list_available_contexts when not in git repository."""
        list_available_contexts(tmp_path)

        captured = capsys.readouterr()
        assert "No git repository found" in captured.out

    def test_list_available_contexts_no_blobify_file(self, tmp_path, capsys):
        """Test list_available_contexts when .blobify file doesn't exist."""
        # Create git repo
        (tmp_path / ".git").mkdir()

        list_available_contexts(tmp_path)

        captured = capsys.readouterr()
        assert "No contexts found in .blobify file." in captured.out

    def test_context_flag_without_value_lists_contexts(self, tmp_path, capsys):
        """Test that -x without value lists available contexts."""
        # Create git repo
        (tmp_path / ".git").mkdir()

        # Create .blobify with contexts
        blobify_file = tmp_path / ".blobify"
        blobify_file.write_text(
            """
# Test context
[test-ctx]
+*.py
"""
        )

        with patch("sys.argv", ["bfy", str(tmp_path), "-x"]):
            main()

        captured = capsys.readouterr()
        assert "Available contexts:" in captured.out
        assert "test-ctx" in captured.out

    def test_context_flag_without_value_current_directory(self, tmp_path, monkeypatch, capsys):
        """Test that -x without value works in current directory with .blobify file."""
        # Change to temp directory
        monkeypatch.chdir(tmp_path)

        # Create git repo
        (tmp_path / ".git").mkdir()

        # Create .blobify with contexts
        blobify_file = tmp_path / ".blobify"
        blobify_file.write_text(
            """
# Current directory test
[current-test]
+*.py
"""
        )

        with patch("sys.argv", ["bfy", "-x"]):
            main()

        captured = capsys.readouterr()
        assert "Available contexts:" in captured.out
        assert "current-test" in captured.out

    def test_context_flag_without_value_no_blobify_current_dir(self, tmp_path, monkeypatch, capsys):
        """Test that -x without value handles missing .blobify in current directory."""
        # Change to temp directory
        monkeypatch.chdir(tmp_path)

        with patch("sys.argv", ["bfy", "-x"]):
            main()

        captured = capsys.readouterr()
        assert "No .blobify file found in current directory." in captured.out

    def test_long_context_flag_without_value(self, tmp_path, capsys):
        """Test that --context without value also works."""
        # Create git repo
        (tmp_path / ".git").mkdir()

        # Create .blobify with contexts
        blobify_file = tmp_path / ".blobify"
        blobify_file.write_text(
            """
[long-flag-test]
+*.py
"""
        )

        with patch("sys.argv", ["bfy", str(tmp_path), "--context"]):
            main()

        captured = capsys.readouterr()
        assert "Available contexts:" in captured.out
        assert "long-flag-test" in captured.out

    def test_context_sorting_in_output(self, tmp_path, capsys):
        """Test that contexts are sorted alphabetically in output."""
        # Create git repo
        (tmp_path / ".git").mkdir()

        # Create .blobify with contexts in non-alphabetical order
        blobify_file = tmp_path / ".blobify"
        blobify_file.write_text(
            """
[zebra]
+*.py

[apple]
+*.md

[banana]
+*.txt
"""
        )

        list_available_contexts(tmp_path)

        captured = capsys.readouterr()
        output_lines = captured.out.split("\n")

        # Find the context lines
        context_lines = [line for line in output_lines if line.strip().startswith("apple") or line.strip().startswith("banana") or line.strip().startswith("zebra")]

        # Should be in alphabetical order
        assert len(context_lines) == 3
        assert "apple" in context_lines[0]
        assert "banana" in context_lines[1]
        assert "zebra" in context_lines[2]

    def test_context_flag_with_specific_context_still_works(self, tmp_path):
        """Test that existing functionality with specific context names still works."""
        # Create git repo
        (tmp_path / ".git").mkdir()

        # Create .blobify with contexts
        blobify_file = tmp_path / ".blobify"
        blobify_file.write_text(
            """
[test-ctx]
+*.py
@debug=true
"""
        )

        # Create test file
        (tmp_path / "test.py").write_text("print('hello')")
        output_file = tmp_path / "output.txt"

        with patch("sys.argv", ["bfy", str(tmp_path), "-x", "test-ctx", "--output-filename", str(output_file)]):
            main()

        # Should process files normally, not list contexts
        content = output_file.read_text(encoding="utf-8")
        assert "print('hello')" in content
        assert "Available contexts:" not in content

    def test_context_flag_nonexistent_directory_error(self, capsys):
        """Test that -x with nonexistent directory shows error."""
        with patch("sys.argv", ["bfy", "/nonexistent/path", "-x"]):
            with pytest.raises(SystemExit):
                main()

        captured = capsys.readouterr()
        assert "Directory does not exist" in captured.err

    def test_context_descriptions_with_special_characters(self, tmp_path, capsys):
        """Test context descriptions with special characters."""
        # Create git repo
        (tmp_path / ".git").mkdir()

        # Create .blobify with special characters in descriptions
        blobify_file = tmp_path / ".blobify"
        blobify_file.write_text(
            """
# Context with: colons, semicolons; and other special chars!
[special-chars]
+*.py

# Context with "quotes" and 'apostrophes'
[quoted-desc]
+*.md
"""
        )

        list_available_contexts(tmp_path)

        captured = capsys.readouterr()
        assert "special-chars: Context with: colons, semicolons; and other special chars!" in captured.out
        assert "quoted-desc: Context with \"quotes\" and 'apostrophes'" in captured.out

    def test_context_debug_output(self, tmp_path, capsys):
        """Test that debug output works for context discovery."""
        blobify_file = tmp_path / ".blobify"
        blobify_file.write_text(
            """
[test-context]
+*.py
"""
        )

        contexts = get_available_contexts(tmp_path, debug=True)

        captured = capsys.readouterr()
        assert contexts == ["test-context"]
        # Debug output should contain the context name
        assert "test-context" in captured.err


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
