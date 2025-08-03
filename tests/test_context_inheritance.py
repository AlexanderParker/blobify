"""Tests for context inheritance functionality."""

from unittest.mock import patch

import pytest

from blobify.config import get_available_contexts, list_available_contexts, read_blobify_config
from blobify.main import main


class TestContextInheritance:
    """Test cases for context inheritance functionality."""

    def test_default_context_behavior(self, tmp_path):
        """Test that default context works correctly."""
        blobify_file = tmp_path / ".blobify"
        blobify_file.write_text(
            """
# Default context patterns
@clip
+*.py
-*.log
"""
        )

        # Test default context (no context specified)
        includes, excludes, switches = read_blobify_config(tmp_path)
        assert includes == ["*.py"]
        assert excludes == ["*.log"]
        assert switches == ["clip"]

        # Test explicitly requesting default context
        includes, excludes, switches = read_blobify_config(tmp_path, "default")
        assert includes == ["*.py"]
        assert excludes == ["*.log"]
        assert switches == ["clip"]

    def test_single_level_inheritance(self, tmp_path):
        """Test basic single-level inheritance."""
        blobify_file = tmp_path / ".blobify"
        blobify_file.write_text(
            """
# Default context
@clip
+*.py
-*.log

[extended:default]
# Inherits from default
+*.md
-secret.txt
"""
        )

        # Test default context
        includes, excludes, switches = read_blobify_config(tmp_path, "default")
        assert includes == ["*.py"]
        assert excludes == ["*.log"]
        assert switches == ["clip"]

        # Test extended context (should inherit from default)
        includes, excludes, switches = read_blobify_config(tmp_path, "extended")
        assert includes == ["*.py", "*.md"]  # Inherited + own
        assert excludes == ["*.log", "secret.txt"]  # Inherited + own
        assert switches == ["clip"]  # Inherited

    def test_multi_level_inheritance(self, tmp_path):
        """Test multi-level inheritance chain."""
        blobify_file = tmp_path / ".blobify"
        blobify_file.write_text(
            """
# Default context
@clip
+*.py

[base:default]
@debug
+*.js

[extended:base]
@no-metadata
+*.md

[final:extended]
+*.txt
-*.log
"""
        )

        # Test final context should inherit from entire chain
        includes, excludes, switches = read_blobify_config(tmp_path, "final")

        # Should have patterns from entire inheritance chain
        assert includes == ["*.py", "*.js", "*.md", "*.txt"]
        assert excludes == ["*.log"]
        assert switches == ["clip", "debug", "no-metadata"]

    def test_context_without_inheritance(self, tmp_path):
        """Test context that doesn't inherit from anything."""
        blobify_file = tmp_path / ".blobify"
        blobify_file.write_text(
            """
# Default context
@clip
+*.py

[standalone]
# No inheritance
+*.md
@debug
"""
        )

        # Test standalone context (should not inherit from default)
        includes, excludes, switches = read_blobify_config(tmp_path, "standalone")
        assert includes == ["*.md"]  # Only own patterns
        assert excludes == []
        assert switches == ["debug"]  # Only own switches

    def test_missing_parent_context(self, tmp_path, capsys):
        """Test handling when parent context doesn't exist."""
        blobify_file = tmp_path / ".blobify"
        blobify_file.write_text(
            """
[child:nonexistent]
+*.py
@debug
"""
        )

        includes, excludes, switches = read_blobify_config(tmp_path, "child", debug=True)

        # Should still process child's own patterns
        assert includes == ["*.py"]
        assert switches == ["debug"]

        # Check warning was issued
        captured = capsys.readouterr()
        assert "Parent context 'nonexistent' not found" in captured.err

    def test_inheritance_preserves_pattern_order(self, tmp_path):
        """Test that inheritance preserves the order of patterns."""
        blobify_file = tmp_path / ".blobify"
        blobify_file.write_text(
            """
# Default has exclusions first
-*.log
+*.py
@clip

[child:default]
# Child adds more patterns
+*.md
-secret.txt
@debug
"""
        )

        includes, excludes, switches = read_blobify_config(tmp_path, "child")

        # Order should be: parent patterns first, then child patterns
        assert includes == ["*.py", "*.md"]
        assert excludes == ["*.log", "secret.txt"]
        assert switches == ["clip", "debug"]

    def test_context_inheritance_with_blobify_patterns_file_order(self, tmp_path):
        """Test that inherited patterns maintain the file order for pattern application."""
        # Create git repo
        (tmp_path / ".git").mkdir()

        blobify_file = tmp_path / ".blobify"
        blobify_file.write_text(
            """
# Default: exclude all, then include Python
-**
+*.py

[docs:default]
# Inherit exclusion, add markdown
+*.md
"""
        )

        # Create test files
        (tmp_path / "app.py").write_text("print('app')")
        (tmp_path / "README.md").write_text("# README")
        (tmp_path / "config.xml").write_text("<config/>")

        output_file = tmp_path / "output.txt"
        with patch("sys.argv", ["bfy", str(tmp_path), "-x", "docs", "-o", str(output_file)]):
            main()

        content = output_file.read_text(encoding="utf-8")

        # Should include Python and Markdown files (from inheritance + own patterns)
        assert "print('app')" in content
        assert "# README" in content

        # Should exclude XML file (from inherited -** pattern)
        assert "<config/>" not in content
        assert "config.xml [FILE CONTENTS EXCLUDED BY .blobify]" in content

    def test_get_available_contexts_with_inheritance(self, tmp_path):
        """Test that get_available_contexts correctly parses inheritance syntax."""
        blobify_file = tmp_path / ".blobify"
        blobify_file.write_text(
            """
[base]
+*.py

[extended:base]
+*.md

[complex:extended]
+*.txt
"""
        )

        contexts = get_available_contexts(tmp_path)
        assert set(contexts) == {"base", "extended", "complex"}

    def test_list_available_contexts_shows_inheritance(self, tmp_path, capsys):
        """Test that list_available_contexts shows inheritance relationships."""
        # Create git repo
        (tmp_path / ".git").mkdir()

        blobify_file = tmp_path / ".blobify"
        blobify_file.write_text(
            """
# Base context for Python files
[base]
+*.py

# Extended context inherits base
[extended:base]
+*.md

# Complex context inherits extended
[complex:extended]
+*.txt
"""
        )

        list_available_contexts(tmp_path)

        captured = capsys.readouterr()
        assert "base" in captured.out
        assert "extended (inherits from base)" in captured.out
        assert "complex (inherits from extended)" in captured.out

    def test_context_inheritance_help_text(self, tmp_path, capsys):
        """Test that help text includes inheritance examples when no contexts exist."""
        # Create git repo
        (tmp_path / ".git").mkdir()

        # Create empty .blobify
        (tmp_path / ".blobify").write_text("")

        list_available_contexts(tmp_path)

        captured = capsys.readouterr()
        assert "Context inheritance:" in captured.out
        assert "[extended:base]" in captured.out
        assert "# Inherits @clip and +*.py from base" in captured.out

    def test_context_inheritance_with_filter_defaults(self, tmp_path):
        """Test that filter defaults are properly inherited."""
        # Create git repo
        (tmp_path / ".git").mkdir()

        blobify_file = tmp_path / ".blobify"
        blobify_file.write_text(
            """
# Default with filter
@filter=functions:^def
+*.py

[enhanced:default]
@filter=classes:^class
+*.js
"""
        )

        # Create test files
        py_file = tmp_path / "test.py"
        py_file.write_text("def hello():\n    pass\nclass Test:\n    pass")

        js_file = tmp_path / "test.js"
        js_file.write_text("function greet() {}\nclass Component {}")

        output_file = tmp_path / "output.txt"
        with patch("sys.argv", ["bfy", str(tmp_path), "-x", "enhanced", "-o", str(output_file)]):
            main()

        content = output_file.read_text(encoding="utf-8")

        # Should show both inherited and own filters
        assert "functions: ^def" in content
        assert "classes: ^class" in content

        # Should apply both filters
        assert "def hello():" in content
        assert "class Test:" in content
        assert "class Component" in content

    def test_nonexistent_context_inheritance(self, tmp_path):
        """Test requesting a context that doesn't exist."""
        blobify_file = tmp_path / ".blobify"
        blobify_file.write_text(
            """
[existing]
+*.py
"""
        )

        includes, excludes, switches = read_blobify_config(tmp_path, "nonexistent")

        # Should return empty configuration
        assert includes == []
        assert excludes == []
        assert switches == []

    def test_empty_inheritance_syntax(self, tmp_path):
        """Test handling of malformed inheritance syntax."""
        blobify_file = tmp_path / ".blobify"
        blobify_file.write_text(
            """
[empty:]
+*.py

[normal:base]
+*.txt

[base]
+*.md
"""
        )

        # Should handle malformed syntax gracefully
        contexts = get_available_contexts(tmp_path)
        assert "empty" in contexts
        assert "normal" in contexts
        assert "base" in contexts

        # Test that empty parent is treated as no inheritance
        includes, excludes, switches = read_blobify_config(tmp_path, "empty")
        assert includes == ["*.py"]

    def test_context_inheritance_integration_example(self, tmp_path):
        """Test the complete example from the task description."""
        # Create git repo
        (tmp_path / ".git").mkdir()

        blobify_file = tmp_path / ".blobify"
        blobify_file.write_text(
            """
-**
@clip

[code:default]
# "code" inherits -** and @clip
+code

[all:code]
# "all" inherits -**, @clip, and +code
+**
"""
        )

        # Test that "all" context gets the expected final configuration
        includes, excludes, switches = read_blobify_config(tmp_path, "all")

        # Final "all" context should be evaluated as: -**, @clip, +code, +**
        assert excludes == ["**"]
        assert switches == ["clip"]
        assert includes == ["code", "**"]

    def test_inheritance_with_complex_patterns(self, tmp_path):
        """Test inheritance with complex pattern combinations."""
        blobify_file = tmp_path / ".blobify"
        blobify_file.write_text(
            """
# Default excludes everything, includes Python
-**
+*.py
+src/**/*.py

[docs:default]
# Add documentation
+*.md
+docs/**
-docs/private/**

[full:docs]
# Add everything else
+**
@suppress-excluded
"""
        )

        includes, excludes, switches = read_blobify_config(tmp_path, "full")

        # Should have all patterns from inheritance chain
        expected_includes = ["*.py", "src/**/*.py", "*.md", "docs/**", "**"]
        expected_excludes = ["**", "docs/private/**"]
        expected_switches = ["suppress-excluded"]

        assert includes == expected_includes
        assert excludes == expected_excludes
        assert switches == expected_switches

    def test_contexts_processed_in_file_order(self, tmp_path):
        """Test that contexts can only inherit from contexts defined earlier in the file."""
        blobify_file = tmp_path / ".blobify"
        blobify_file.write_text(
            """
[first]
+*.py
@clip

[second:first]
# Can inherit from first (defined above)
+*.md

[third:first]
# Can also inherit from first
+*.txt
"""
        )

        # Test that second inherits from first
        includes, excludes, switches = read_blobify_config(tmp_path, "second")
        assert includes == ["*.py", "*.md"]
        assert switches == ["clip"]

        # Test that third also inherits from first
        includes, excludes, switches = read_blobify_config(tmp_path, "third")
        assert includes == ["*.py", "*.txt"]
        assert switches == ["clip"]

    def test_debug_output_inheritance(self, tmp_path, capsys):
        """Test debug output shows inheritance information."""
        blobify_file = tmp_path / ".blobify"
        blobify_file.write_text(
            """
+*.py
@clip

[child:default]
+*.md
"""
        )

        read_blobify_config(tmp_path, "child", debug=True)

        captured = capsys.readouterr()
        assert "Created context 'child' inheriting from 'default'" in captured.err
        assert "Final context 'child'" in captured.err


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
