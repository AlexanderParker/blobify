"""Integration tests for MCP server functionality."""

import json
import tempfile
from pathlib import Path

import pytest

from blobify.mcp_server import create_mcp_server
from blobify.mcp_server.server import (
    _analyse_filesystem_impl,
    _update_blobify_file_impl,
    _run_blobify_impl,
    _get_blobify_file_impl,
    _get_default_excludes_impl,
    _get_contexts_impl,
)


@pytest.fixture
def temp_project_dir():
    """Create a temporary directory with sample project files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)

        # Create git repository
        (project_dir / ".git").mkdir()

        # Create sample files
        (project_dir / "main.py").write_text(
            """#!/usr/bin/env python3
def main():
    print("Hello, world!")

if __name__ == "__main__":
    main()
"""
        )

        (project_dir / "utils.py").write_text(
            """def helper_function():
    return "helper"

class UtilityClass:
    def method(self):
        pass
"""
        )

        (project_dir / "tests").mkdir(exist_ok=True)
        (project_dir / "tests" / "test_main.py").write_text(
            """import unittest
from main import main

class TestMain(unittest.TestCase):
    def test_main(self):
        # Test implementation
        pass
"""
        )

        # Create .gitignore
        (project_dir / ".gitignore").write_text(
            """*.pyc
__pycache__/
.env
"""
        )

        yield project_dir


@pytest.fixture
def temp_project_with_blobify(temp_project_dir):
    """Create a temporary directory with .blobify configuration."""
    blobify_content = """# Test configuration
@copy-to-clipboard=false
@debug=true

## This is a test project
## Focus on code quality

[backend]
+*.py
-tests/**

[tests]
+tests/**

[nothing]
-**
"""

    (temp_project_dir / ".blobify").write_text(blobify_content)
    yield temp_project_dir


@pytest.mark.mcp
@pytest.mark.integration
class TestMCPServerIntegration:
    """Integration tests for MCP server."""

    def test_server_creation(self):
        """Test that MCP server can be created."""
        mcp = create_mcp_server()
        assert mcp is not None
        assert mcp.name == "Blobify"
        assert "packages entire codebases" in mcp.instructions

    @pytest.mark.asyncio
    async def test_analyse_filesystem_tool(self, temp_project_dir):
        """Test filesystem analysis tool."""
        from unittest.mock import AsyncMock

        # Create mock context
        mock_ctx = AsyncMock()

        # Test the implementation function directly
        result = await _analyse_filesystem_impl(str(temp_project_dir), ctx=mock_ctx)

        # Verify result structure
        assert isinstance(result, dict)
        assert "directory" in result
        assert "is_git_repository" in result
        assert "statistics" in result
        assert "file_types" in result

        # Verify statistics
        stats = result["statistics"]
        assert stats["total_files"] >= 3  # main.py, utils.py, test_main.py
        assert stats["included_files"] >= 3
        assert result["is_git_repository"] is True

        # Verify mock context was called
        mock_ctx.info.assert_called()
        mock_ctx.report_progress.assert_called()

    @pytest.mark.asyncio
    async def test_update_blobify_file_tool(self, temp_project_dir):
        """Test .blobify file creation/update tool."""
        from unittest.mock import AsyncMock

        # Create mock context
        mock_ctx = AsyncMock()

        # Test creating new .blobify file
        test_content = """# Test configuration
+*.py
-*.log
"""

        result = await _update_blobify_file_impl(str(temp_project_dir), test_content, ctx=mock_ctx)

        # Verify file was created
        blobify_file = temp_project_dir / ".blobify"
        assert blobify_file.exists()
        assert blobify_file.read_text() == test_content
        assert "Created .blobify file" in result

        # Verify mock context was called
        mock_ctx.info.assert_called()

    @pytest.mark.asyncio
    async def test_run_blobify_tool(self, temp_project_with_blobify):
        """Test running blobify tool with real execution."""
        from unittest.mock import AsyncMock

        # Create mock context
        mock_ctx = AsyncMock()

        # Test running blobify with real execution - no mocking
        result = await _run_blobify_impl(str(temp_project_with_blobify), ctx=mock_ctx)

        # Verify result is a string containing blobify output
        assert isinstance(result, str)
        assert "# Blobify Text File Index" in result
        assert "START_FILE:" in result
        # Should contain some actual project files
        assert any(filename in result for filename in ["main.py", "utils.py", "test_main.py"])

        # Verify mock context was called
        mock_ctx.info.assert_called()

    @pytest.mark.asyncio
    async def test_run_blobify_with_context(self, temp_project_with_blobify):
        """Test running blobify with specific context."""
        from unittest.mock import AsyncMock

        # Create mock context
        mock_ctx = AsyncMock()

        # Test running blobify with backend context - real execution
        result = await _run_blobify_impl(str(temp_project_with_blobify), context="backend", ctx=mock_ctx)

        # Verify result contains expected content
        assert isinstance(result, str)
        assert "# Blobify Text File Index" in result
        assert "START_FILE:" in result

        # Backend context should include .py files but exclude tests
        assert "main.py" in result
        assert "utils.py" in result

        # Backend context pattern order: +*.py then -tests/**
        # So test files should be excluded
        if "test_main.py" in result:
            # Should appear in index but be marked as excluded
            assert "[FILE CONTENTS EXCLUDED BY .blobify]" in result
        # Verify test file content is not included
        assert "class TestMain" not in result

    def test_get_blobify_file_resource(self, temp_project_with_blobify):
        """Test getting .blobify file resource."""
        # Test getting existing .blobify file
        result = _get_blobify_file_impl(str(temp_project_with_blobify))

        assert isinstance(result, str)
        assert ".blobify configuration" in result
        assert "Test configuration" in result
        assert "[backend]" in result
        assert "+*.py" in result
        assert "-tests/**" in result

    def test_get_default_excludes_resource(self):
        """Test getting default excludes resource."""
        # Test getting default excludes
        result = _get_default_excludes_impl()

        assert isinstance(result, str)
        assert "Built-in exclusion patterns" in result
        assert ".git" in result
        assert "node_modules" in result
        assert "__pycache__" in result

    def test_get_contexts_resource(self, temp_project_with_blobify):
        """Test getting contexts resource."""
        # Test getting contexts
        result = _get_contexts_impl(str(temp_project_with_blobify))

        assert isinstance(result, str)
        assert "Available contexts" in result
        assert "backend" in result
        assert "tests" in result

    def test_generate_blobify_file_prompt(self):
        """Test generate .blobify file prompt."""
        from blobify.mcp_server.server import _generate_blobify_file_prompt_impl

        # Test prompt generation
        filesystem_analysis = json.dumps({"test": "data"})
        instructions = "Create a configuration for a Python web application"

        result = _generate_blobify_file_prompt_impl(filesystem_analysis, instructions)

        assert isinstance(result, str)
        assert "generate a comprehensive .blobify configuration" in result
        assert filesystem_analysis in result
        assert instructions in result
        assert ".blobify file uses this syntax" in result

    def test_update_blobify_file_prompt(self):
        """Test update .blobify file prompt."""
        from blobify.mcp_server.server import _update_blobify_file_prompt_impl

        # Test prompt generation
        existing_config = "+*.py\n-*.log"
        filesystem_analysis = json.dumps({"test": "data"})
        instructions = "Add support for JavaScript files"

        result = _update_blobify_file_prompt_impl(existing_config, filesystem_analysis, instructions)

        assert isinstance(result, str)
        assert "Update the existing .blobify configuration" in result
        assert existing_config in result
        assert filesystem_analysis in result
        assert instructions in result

    def test_act_on_contents_prompt(self):
        """Test act on contents prompt."""
        from blobify.mcp_server.server import _act_on_contents_prompt_impl

        # Test prompt generation
        blobify_output = "# Blobify Text File Index\nSample content..."
        instructions = "Review for security vulnerabilities"

        result = _act_on_contents_prompt_impl(blobify_output, instructions)

        assert isinstance(result, str)
        assert instructions in result
        assert blobify_output in result
        assert "BLOBIFIED CODEBASE CONTENT:" in result

    @pytest.mark.asyncio
    async def test_full_workflow_new_project(self, temp_project_dir):
        """Test complete workflow for new project setup."""
        from unittest.mock import AsyncMock

        # Create mock context
        mock_ctx = AsyncMock()

        # Step 1: Analyze filesystem
        analysis_result = await _analyse_filesystem_impl(str(temp_project_dir), ctx=mock_ctx)
        assert isinstance(analysis_result, dict)
        assert analysis_result["statistics"]["total_files"] > 0

        # Step 2: Generate .blobify configuration (simulate with prompt)
        from blobify.mcp_server.server import _generate_blobify_file_prompt_impl

        prompt_result = _generate_blobify_file_prompt_impl(
            json.dumps(analysis_result), "Create a Python project configuration"
        )
        assert isinstance(prompt_result, str)

        # Step 3: Create .blobify file
        config_content = """# Generated configuration
@copy-to-clipboard=false
+*.py
-tests/**
"""
        update_result = await _update_blobify_file_impl(str(temp_project_dir), config_content, ctx=mock_ctx)
        assert "Created .blobify file" in update_result

        # Step 4: Run blobify with real execution - no mocking
        run_result = await _run_blobify_impl(str(temp_project_dir), ctx=mock_ctx)

        assert isinstance(run_result, str)
        assert "# Blobify Text File Index" in run_result
        assert "START_FILE:" in run_result
        # Should contain main.py or utils.py content but exclude test files
        assert any(filename in run_result for filename in ["main.py", "utils.py"])
        # Tests should be excluded by the .blobify configuration
        if "test_main.py" in run_result:
            assert "[FILE CONTENTS EXCLUDED BY .blobify]" in run_result

    @pytest.mark.asyncio
    async def test_error_handling(self, temp_project_dir):
        """Test error handling in MCP tools."""
        from unittest.mock import AsyncMock

        # Create mock context
        mock_ctx = AsyncMock()

        # Test with non-existent directory
        with pytest.raises(ValueError, match="Directory does not exist"):
            await _analyse_filesystem_impl("/nonexistent/path", ctx=mock_ctx)

        with pytest.raises(ValueError, match="Directory does not exist"):
            await _update_blobify_file_impl("/nonexistent/path", "content", ctx=mock_ctx)

        with pytest.raises(ValueError, match="Directory does not exist"):
            await _run_blobify_impl("/nonexistent/path", ctx=mock_ctx)

    def test_resource_error_handling(self):
        """Test error handling in resource functions."""
        # Test with non-existent directory for contexts
        result = _get_contexts_impl("/nonexistent/path")
        assert "No git repository found" in result

        # Test with non-existent .blobify file
        result = _get_blobify_file_impl("/nonexistent/path")
        assert "No .blobify file exists" in result

    def test_integration_with_real_filesystem_structure(self, temp_project_dir):
        """Test integration with realistic project structure."""
        # Create a more complex project structure
        (temp_project_dir / "src").mkdir()
        (temp_project_dir / "src" / "app.py").write_text("# Main application")
        (temp_project_dir / "src" / "utils.py").write_text("# Utilities")

        (temp_project_dir / "docs").mkdir()
        (temp_project_dir / "docs" / "README.md").write_text("# Documentation")

        (temp_project_dir / "tests").mkdir(exist_ok=True)
        (temp_project_dir / "tests" / "test_app.py").write_text("# Tests")

        # Create a complex .blobify file
        blobify_content = """# Complex project configuration
@copy-to-clipboard=false
@debug=true

## This is a complex Python project
## Focus on architecture and maintainability

[src-only]
-**
+src/**
+*.py

[docs-only]
-**
+docs/**
+*.md

[full:src-only,docs-only]
# Combines both src and docs
@output-metadata=false
"""
        (temp_project_dir / ".blobify").write_text(blobify_content)

        # Test filesystem analysis on complex structure
        async def test_complex_analysis():
            from unittest.mock import AsyncMock

            mock_ctx = AsyncMock()
            result = await _analyse_filesystem_impl(str(temp_project_dir), ctx=mock_ctx)

            # Should detect multiple file types
            assert ".py" in result["file_types"]
            assert ".md" in result["file_types"]

            # Should have proper directory structure
            assert "src" in result["directories"]
            assert "docs" in result["directories"]
            assert "tests" in result["directories"]

            return result

        import asyncio

        result = asyncio.run(test_complex_analysis())

        # Test contexts resource on complex configuration
        contexts_result = _get_contexts_impl(str(temp_project_dir))
        assert "src-only" in contexts_result
        assert "docs-only" in contexts_result
        assert "full" in contexts_result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
