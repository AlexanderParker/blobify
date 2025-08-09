"""Tests for LLM instructions functionality (double-hash comments)."""

from unittest.mock import patch

import pytest

from blobify.config import read_blobify_config
from blobify.main import main


class TestLLMInstructions:
    """Test cases for LLM instructions functionality using double-hash comments."""

    def test_read_blobify_config_with_llm_instructions(self, tmp_path):
        """Test reading LLM instructions from .blobify file."""
        blobify_file = tmp_path / ".blobify"
        blobify_file.write_text(
            """
# Regular comment
## This is an LLM instruction
+*.py
## Another instruction for the AI
-*.log
## Focus on security issues
@debug=true
"""
        )

        includes, excludes, switches, llm_instructions = read_blobify_config(tmp_path)

        assert includes == ["*.py"]
        assert excludes == ["*.log"]
        assert switches == ["debug=true"]
        assert llm_instructions == [
            "This is an LLM instruction",
            "Another instruction for the AI",
            "Focus on security issues",
        ]

    def test_llm_instructions_with_context(self, tmp_path):
        """Test LLM instructions in specific contexts."""
        blobify_file = tmp_path / ".blobify"
        blobify_file.write_text(
            """
# Default context
## General analysis instruction
+*.py

[security-review]
## Focus on security vulnerabilities
## Check for SQL injection and XSS
## Analyze authentication mechanisms
+*.py
+*.js
"""
        )

        # Test default context
        includes, excludes, switches, llm_instructions = read_blobify_config(tmp_path)
        assert llm_instructions == ["General analysis instruction"]

        # Test security-review context
        includes, excludes, switches, llm_instructions = read_blobify_config(tmp_path, "security-review")
        assert llm_instructions == [
            "Focus on security vulnerabilities",
            "Check for SQL injection and XSS",
            "Analyze authentication mechanisms",
        ]

    def test_llm_instructions_with_inheritance(self, tmp_path):
        """Test that LLM instructions are inherited from parent contexts."""
        blobify_file = tmp_path / ".blobify"
        blobify_file.write_text(
            """
# Default context
## Base instruction from default
+*.py

[base]
## Instruction from base context
+*.js

[extended:base]
## Additional instruction from extended
+*.md
"""
        )

        includes, excludes, switches, llm_instructions = read_blobify_config(tmp_path, "extended")

        # Should inherit instructions from base context
        assert llm_instructions == ["Instruction from base context", "Additional instruction from extended"]

    def test_llm_instructions_with_multiple_inheritance(self, tmp_path):
        """Test LLM instructions with multiple inheritance."""
        blobify_file = tmp_path / ".blobify"
        blobify_file.write_text(
            """
[parent1]
## Instruction from parent1
+*.py

[parent2]
## Instruction from parent2
+*.js

[child:parent1,parent2]
## Instruction from child
+*.md
"""
        )

        includes, excludes, switches, llm_instructions = read_blobify_config(tmp_path, "child")

        # Should inherit from both parents in order
        assert llm_instructions == ["Instruction from parent1", "Instruction from parent2", "Instruction from child"]

    def test_llm_instructions_empty_and_whitespace(self, tmp_path):
        """Test handling of empty and whitespace-only LLM instructions."""
        blobify_file = tmp_path / ".blobify"
        blobify_file.write_text(
            """
##
##
## Valid instruction
##
## Another valid instruction
+*.py
"""
        )

        includes, excludes, switches, llm_instructions = read_blobify_config(tmp_path)

        # Should only include non-empty instructions
        assert llm_instructions == ["Valid instruction", "Another valid instruction"]

    def test_llm_instructions_mixed_with_comments(self, tmp_path):
        """Test that single-hash comments are ignored while double-hash are processed."""
        blobify_file = tmp_path / ".blobify"
        blobify_file.write_text(
            """
# This is a regular comment - should be ignored
## This is an LLM instruction
# Another regular comment
## Another LLM instruction
# This starts with single hash - should be ignored as regular comment
+*.py
""",
            encoding="utf-8",
        )

        includes, excludes, switches, llm_instructions = read_blobify_config(tmp_path)

        assert llm_instructions == ["This is an LLM instruction", "Another LLM instruction"]

    def test_llm_instructions_debug_output(self, tmp_path, capsys):
        """Test debug output for LLM instruction parsing."""
        blobify_file = tmp_path / ".blobify"
        blobify_file.write_text(
            """
## Debug test instruction
+*.py

[context1]
## Context specific instruction
+*.js
"""
        )

        # Test with debug enabled
        read_blobify_config(tmp_path, debug=True)

        captured = capsys.readouterr()
        assert "LLM instruction 'Debug test instruction' (context: default)" in captured.err

        # Test context-specific debug
        capsys.readouterr()  # Clear previous output
        read_blobify_config(tmp_path, "context1", debug=True)

        captured = capsys.readouterr()
        assert "LLM instruction 'Context specific instruction' (context: context1)" in captured.err

    def test_llm_instructions_in_output_header(self, tmp_path):
        """Test that LLM instructions appear in the output header."""
        # Create git repo
        (tmp_path / ".git").mkdir()

        # Create .blobify with LLM instructions
        blobify_file = tmp_path / ".blobify"
        blobify_file.write_text(
            """
## This codebase represents a Python web application
## Focus on security vulnerabilities and performance issues
## Provide recommendations for improvements
+*.py
"""
        )

        # Create test file
        (tmp_path / "app.py").write_text("print('hello')")

        output_file = tmp_path / "output.txt"
        with patch("sys.argv", ["bfy", str(tmp_path), "--output-filename", str(output_file)]):
            main()

        content = output_file.read_text(encoding="utf-8")

        # Should have LLM instructions section in header
        assert "# Instructions for AI/LLM analysis:" in content
        assert "# * This codebase represents a Python web application" in content
        assert "# * Focus on security vulnerabilities and performance issues" in content
        assert "# * Provide recommendations for improvements" in content

    def test_llm_instructions_with_context_in_output(self, tmp_path):
        """Test LLM instructions from specific context appear in output."""
        # Create git repo
        (tmp_path / ".git").mkdir()

        # Create .blobify with context-specific instructions
        blobify_file = tmp_path / ".blobify"
        blobify_file.write_text(
            """
# Default context
+*.py

[code-review]
## Review this code for best practices
## Check for potential bugs and edge cases
## Suggest performance optimizations
+*.py
+*.js
"""
        )

        # Create test files
        (tmp_path / "app.py").write_text("print('hello')")
        (tmp_path / "script.js").write_text("console.log('world');")

        output_file = tmp_path / "output.txt"
        with patch("sys.argv", ["bfy", str(tmp_path), "-x", "code-review", "--output-filename", str(output_file)]):
            main()

        content = output_file.read_text(encoding="utf-8")

        # Should have context-specific LLM instructions
        assert "# Instructions for AI/LLM analysis:" in content
        assert "# * Review this code for best practices" in content
        assert "# * Check for potential bugs and edge cases" in content
        assert "# * Suggest performance optimizations" in content

    def test_llm_instructions_inheritance_in_output(self, tmp_path):
        """Test that inherited LLM instructions appear correctly in output."""
        # Create git repo
        (tmp_path / ".git").mkdir()

        # Create .blobify with inheritance
        blobify_file = tmp_path / ".blobify"
        blobify_file.write_text(
            """
[base]
## Base instruction for analysis
+*.py

[extended:base]
## Additional specific instruction
+*.js
"""
        )

        # Create test files
        (tmp_path / "app.py").write_text("print('hello')")
        (tmp_path / "script.js").write_text("console.log('world');")

        output_file = tmp_path / "output.txt"
        with patch("sys.argv", ["bfy", str(tmp_path), "-x", "extended", "--output-filename", str(output_file)]):
            main()

        content = output_file.read_text(encoding="utf-8")

        # Should have both inherited and own instructions
        assert "# Instructions for AI/LLM analysis:" in content
        assert "# * Base instruction for analysis" in content
        assert "# * Additional specific instruction" in content

    def test_no_llm_instructions_no_section(self, tmp_path):
        """Test that when no LLM instructions exist, no section is added to header."""
        # Create git repo
        (tmp_path / ".git").mkdir()

        # Create .blobify without LLM instructions
        blobify_file = tmp_path / ".blobify"
        blobify_file.write_text(
            """
# Regular comment only
+*.py
"""
        )

        # Create test file
        (tmp_path / "app.py").write_text("print('hello')")

        output_file = tmp_path / "output.txt"
        with patch("sys.argv", ["bfy", str(tmp_path), "--output-filename", str(output_file)]):
            main()

        content = output_file.read_text(encoding="utf-8")

        # Should NOT have LLM instructions section
        assert "# Instructions for AI/LLM analysis:" not in content

    def test_llm_instructions_special_characters(self, tmp_path):
        """Test LLM instructions with special characters and formatting."""
        blobify_file = tmp_path / ".blobify"
        blobify_file.write_text(
            """
## Instruction with "quotes" and 'apostrophes'
## Instruction with special chars: !@#$%^&*()
## Instruction with Unicode: français and émojis
+*.py
""",
            encoding="utf-8",
        )

        includes, excludes, switches, llm_instructions = read_blobify_config(tmp_path)

        assert llm_instructions == [
            "Instruction with \"quotes\" and 'apostrophes'",
            "Instruction with special chars: !@#$%^&*()",
            "Instruction with Unicode: français and émojis",
        ]

    def test_get_context_descriptions_ignores_llm_instructions(self, tmp_path):
        """Test that context descriptions ignore double-hash comments."""
        from blobify.config import get_context_descriptions

        blobify_file = tmp_path / ".blobify"
        blobify_file.write_text(
            """
# This should be the description
## This is an LLM instruction - should be ignored for descriptions
[test-context]
+*.py
"""
        )

        descriptions = get_context_descriptions(tmp_path)

        # Should use single-hash comment, not double-hash
        assert descriptions["test-context"] == "This should be the description"

    def test_get_available_contexts_ignores_llm_instructions(self, tmp_path):
        """Test that context discovery ignores double-hash comments."""
        from blobify.config import get_available_contexts

        blobify_file = tmp_path / ".blobify"
        blobify_file.write_text(
            """
## LLM instruction in default
[context1]
## LLM instruction in context1
+*.py

[context2]
+*.js
"""
        )

        contexts = get_available_contexts(tmp_path)

        # Should find contexts regardless of LLM instructions
        assert set(contexts) == {"context1", "context2"}

    def test_llm_instructions_integration_with_filters_and_options(self, tmp_path):
        """Test LLM instructions work with other blobify features."""
        # Create git repo
        (tmp_path / ".git").mkdir()

        # Create .blobify with LLM instructions, filters, and options
        blobify_file = tmp_path / ".blobify"
        blobify_file.write_text(
            """
## Analyze this Python code for functions and classes
## Pay special attention to error handling
@filter="functions","^def"
@filter="classes","^class"
@debug=true
+*.py
"""
        )

        # Create test file
        (tmp_path / "app.py").write_text("def hello():\n    print('world')\nclass Test:\n    pass")

        output_file = tmp_path / "output.txt"
        with patch("sys.argv", ["bfy", str(tmp_path), "--output-filename", str(output_file)]):
            main()

        content = output_file.read_text(encoding="utf-8")

        # Should have both LLM instructions and filter info
        assert "# Instructions for AI/LLM analysis:" in content
        assert "# * Analyze this Python code for functions and classes" in content
        assert "# * Pay special attention to error handling" in content
        assert "# Content filters applied:" in content
        assert "functions: ^def" in content
        assert "classes: ^class" in content

        # Should apply filters to content
        assert "def hello():" in content
        assert "class Test:" in content
        assert "print('world')" not in content  # Filtered out


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
