"""Tests for MCP server functionality."""

import json
import os
import tempfile
import time
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Only run these tests if MCP is available
pytest_plugins = []
try:
    from blobify.mcp_server.server import (
        _act_on_contents_prompt_impl,
        _analyse_filesystem_impl,
        _generate_blobify_file_prompt_impl,
        _get_blobify_file_impl,
        _get_contexts_impl,
        _get_default_excludes_impl,
        _run_blobify_impl,
        _update_blobify_file_impl,
        _update_blobify_file_prompt_impl,
        create_mcp_server,
    )

    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False


def safe_temp_file_cleanup(temp_path):
    """Safely clean up temporary files on Windows."""
    try:
        if os.path.exists(temp_path):
            # On Windows, ensure file isn't locked
            time.sleep(0.1)  # Brief delay
            os.unlink(temp_path)
    except (OSError, PermissionError):
        # Ignore cleanup errors in tests
        pass


@pytest.fixture
def temp_project_dir():
    """Create a temporary directory with sample project files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)

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

[nothing:default]
-**

[backend:nothing]
+*.py
-tests/**

[tests:nothing]
+tests/**
"""

    (temp_project_dir / ".blobify").write_text(blobify_content)
    yield temp_project_dir


@pytest.mark.skipif(not MCP_AVAILABLE, reason="MCP dependencies not available")
class TestMCPServer:
    """Test MCP server functionality."""

    def test_server_creation(self):
        """Test that MCP server can be created."""
        mcp = create_mcp_server()
        assert mcp is not None
        assert mcp.name == "Blobify"
        assert "packages entire codebases" in mcp.instructions

    @pytest.mark.asyncio
    async def test_analyse_filesystem_implementation(self, temp_project_dir):
        """Test the analyse_filesystem implementation function."""
        # Create mock context
        mock_ctx = AsyncMock()

        # Call the implementation function directly
        result = await _analyse_filesystem_impl(str(temp_project_dir), ctx=mock_ctx)

        # Verify result structure
        assert isinstance(result, dict)
        assert "directory" in result
        assert "statistics" in result
        assert "file_types" in result
        assert "included_files" in result

        # Verify statistics
        stats = result["statistics"]
        assert stats["total_files"] >= 2  # At least main.py and utils.py
        assert stats["total_files"] >= stats["included_files"]

        # Verify mock context was used for progress reporting
        mock_ctx.info.assert_called()
        mock_ctx.report_progress.assert_called()

    @pytest.mark.asyncio
    async def test_update_blobify_file_implementation(self, temp_project_dir):
        """Test the update_blobify_file implementation function."""
        # Create mock context
        mock_ctx = AsyncMock()

        test_content = """# Test .blobify file
+*.py
-tests/**
@debug=true
"""

        # Call the implementation function directly
        result = await _update_blobify_file_impl(str(temp_project_dir), test_content, ctx=mock_ctx)

        # Verify file was created
        blobify_file = temp_project_dir / ".blobify"
        assert blobify_file.exists()
        assert blobify_file.read_text() == test_content

        # Verify result message
        assert "Created .blobify file" in result

        # Verify mock context was used
        mock_ctx.info.assert_called()

    @pytest.mark.asyncio
    async def test_run_blobify_implementation(self, temp_project_with_blobify):
        """Test the run_blobify implementation function."""
        # Create mock context
        mock_ctx = AsyncMock()

        # Mock the main function to avoid actual blobify execution
        with patch("blobify.mcp_server.server.blobify_main") as mock_main:
            # Create a temporary output file with test content
            with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as temp_file:
                test_output = "# Blobify Test Output\nSTART_FILE: main.py\nTest content\nEND_FILE: main.py"
                temp_file.write(test_output)
                temp_file.flush()
                temp_path = temp_file.name

            # File is automatically closed here
            try:
                # Mock sys.argv to capture the temp file path
                with patch("sys.argv") as mock_argv:
                    # Call the implementation function
                    result = await _run_blobify_impl(str(temp_project_with_blobify), ctx=mock_ctx)

                # Verify mock main was called
                mock_main.assert_called_once()

                # Verify result is a string
                assert isinstance(result, str)

                # Verify mock context was used
                mock_ctx.info.assert_called()
            finally:
                # Clean up temp file
                safe_temp_file_cleanup(temp_path)

    def test_get_blobify_file_implementation(self, temp_project_with_blobify):
        """Test the get_blobify_file implementation function."""
        # Call the implementation function directly
        result = _get_blobify_file_impl(str(temp_project_with_blobify))

        # Verify result contains .blobify content
        assert isinstance(result, str)
        assert ".blobify configuration" in result
        assert "backend:nothing" in result
        assert "This is a test project" in result

    def test_get_default_excludes_implementation(self):
        """Test the get_default_excludes implementation function."""
        # Call the implementation function directly
        result = _get_default_excludes_impl()

        # Verify result contains expected patterns
        assert isinstance(result, str)
        assert "Built-in exclusion patterns" in result
        assert ".git" in result
        assert "node_modules" in result
        assert "__pycache__" in result

    def test_get_contexts_implementation(self, temp_project_with_blobify):
        """Test the get_contexts implementation function."""
        # Create git repo for the test
        (temp_project_with_blobify / ".git").mkdir()

        # Call the implementation function directly
        result = _get_contexts_impl(str(temp_project_with_blobify))

        # Verify result contains context information
        assert isinstance(result, str)
        assert "Available contexts" in result
        assert "backend" in result
        assert "tests" in result

    def test_generate_blobify_file_prompt_implementation(self):
        """Test the generate_blobify_file_prompt implementation function."""
        # Test data
        filesystem_analysis = json.dumps({"directory": "/test/project", "file_types": {".py": 5, ".md": 2}, "statistics": {"total_files": 7}})
        instructions = "Focus on Python files only"

        # Call the implementation function directly
        result = _generate_blobify_file_prompt_impl(filesystem_analysis, instructions)

        # Verify result contains expected elements
        assert isinstance(result, str)
        assert ".blobify" in result
        assert "filesystem analysis" in result
        assert instructions in result
        assert "contexts" in result

    def test_update_blobify_file_prompt_implementation(self):
        """Test the update_blobify_file_prompt implementation function."""
        # Test data
        existing_config = "+*.py\n-tests/**"
        filesystem_analysis = '{"file_types": {".py": 5}}'
        instructions = "Add JavaScript support"

        # Call the implementation function directly
        result = _update_blobify_file_prompt_impl(existing_config, filesystem_analysis, instructions)

        # Verify result contains expected elements
        assert isinstance(result, str)
        assert existing_config in result
        assert instructions in result
        assert "Update" in result

    def test_act_on_contents_prompt_implementation(self):
        """Test the act_on_contents_prompt implementation function."""
        # Test data
        blobify_output = "# Blobify Output\nSTART_FILE: main.py\ntest content\nEND_FILE: main.py"
        instructions = "Review for security issues"

        # Call the implementation function directly
        result = _act_on_contents_prompt_impl(blobify_output, instructions)

        # Verify result contains expected elements
        assert isinstance(result, str)
        assert blobify_output in result
        assert instructions in result
        assert "BLOBIFIED CODEBASE CONTENT" in result

    @pytest.mark.asyncio
    async def test_error_handling_invalid_directory(self):
        """Test error handling for invalid directory paths."""
        mock_ctx = AsyncMock()

        # Test with non-existent directory
        with pytest.raises(ValueError, match="Directory does not exist"):
            await _analyse_filesystem_impl("/nonexistent/path", ctx=mock_ctx)

        # Verify error was logged to context
        mock_ctx.error.assert_called()

    @pytest.mark.asyncio
    async def test_update_blobify_file_creates_new_file(self, temp_project_dir):
        """Test that update_blobify_file creates a new file when none exists."""
        mock_ctx = AsyncMock()

        # Ensure no .blobify file exists
        blobify_file = temp_project_dir / ".blobify"
        assert not blobify_file.exists()

        test_content = "+*.py\n-*.log"
        result = await _update_blobify_file_impl(str(temp_project_dir), test_content, ctx=mock_ctx)

        # Verify file was created
        assert blobify_file.exists()
        assert blobify_file.read_text() == test_content
        assert "Created .blobify file" in result

    @pytest.mark.asyncio
    async def test_update_blobify_file_updates_existing_file(self, temp_project_with_blobify):
        """Test that update_blobify_file updates an existing file."""
        mock_ctx = AsyncMock()

        # Verify .blobify file exists
        blobify_file = temp_project_with_blobify / ".blobify"
        assert blobify_file.exists()

        new_content = "+*.js\n+*.ts\n-node_modules/**"
        result = await _update_blobify_file_impl(str(temp_project_with_blobify), new_content, ctx=mock_ctx)

        # Verify file was updated
        assert blobify_file.read_text() == new_content
        assert "Updated .blobify file" in result

    @pytest.mark.asyncio
    async def test_analyse_filesystem_with_git_repository(self, temp_project_dir):
        """Test filesystem analysis in a git repository."""
        # Create git repository
        (temp_project_dir / ".git").mkdir()

        mock_ctx = AsyncMock()
        result = await _analyse_filesystem_impl(str(temp_project_dir), ctx=mock_ctx)

        # Should detect git repository
        assert result["is_git_repository"] is True
        assert result["git_root"] is not None

    @pytest.mark.asyncio
    async def test_analyse_filesystem_without_git_repository(self, temp_project_dir):
        """Test filesystem analysis without a git repository."""
        # Ensure no .git directory exists
        mock_ctx = AsyncMock()
        result = await _analyse_filesystem_impl(str(temp_project_dir), ctx=mock_ctx)

        # Should detect no git repository
        assert result["is_git_repository"] is False
        assert result["git_root"] is None

    def test_get_blobify_file_missing_file(self, temp_project_dir):
        """Test get_blobify_file when no .blobify file exists."""
        result = _get_blobify_file_impl(str(temp_project_dir))
        assert "No .blobify file exists" in result

    def test_get_contexts_no_git_repository(self, temp_project_dir):
        """Test get_contexts when not in a git repository."""
        result = _get_contexts_impl(str(temp_project_dir))
        assert "No git repository found" in result

    def test_get_contexts_no_blobify_file(self, temp_project_dir):
        """Test get_contexts when .blobify file doesn't exist."""
        # Create git repo but no .blobify file
        (temp_project_dir / ".git").mkdir()

        result = _get_contexts_impl(str(temp_project_dir))
        assert "No contexts found" in result

    @pytest.mark.asyncio
    async def test_mcp_server_tool_registration(self):
        """Test that MCP server properly registers tools."""
        mcp = create_mcp_server()

        # Server should be created successfully
        assert mcp is not None
        assert mcp.name == "Blobify"

        # The server should have the expected configuration
        assert "packages entire codebases" in mcp.instructions

    def test_default_excludes_categories(self):
        """Test that default excludes are properly categorized."""
        result = _get_default_excludes_impl()

        # Check for expected categories
        assert "Version Control:" in result
        assert "IDEs:" in result
        assert "Package Managers:" in result
        assert "Python:" in result
        assert "Build/Output:" in result
        assert "Security:" in result

        # Check for specific patterns in categories
        assert ".git" in result
        assert ".vscode" in result
        assert "node_modules" in result
        assert "__pycache__" in result
        assert "build" in result
        assert "keys" in result

    def test_prompt_templates_contain_required_elements(self):
        """Test that prompt templates contain required instructional elements."""
        # Test generate prompt
        analysis = '{"test": "data"}'
        instructions = "Test instructions"
        result = _generate_blobify_file_prompt_impl(analysis, instructions)

        assert "syntax:" in result.lower()
        assert "+pattern" in result
        assert "-pattern" in result
        assert "@option=value" in result
        assert "[context-name]" in result

        # Test update prompt
        existing = "+*.py"
        result = _update_blobify_file_prompt_impl(existing, analysis, instructions)

        assert "Update" in result
        assert existing in result
        assert instructions in result

        # Test act on contents prompt
        blobify_output = "test output"
        result = _act_on_contents_prompt_impl(blobify_output, instructions)

        assert instructions in result
        assert blobify_output in result
        assert "BLOBIFIED CODEBASE CONTENT:" in result
