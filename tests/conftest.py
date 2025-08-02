"""Pytest configuration and shared fixtures for blobify tests."""

import sys
from pathlib import Path

import pytest

# Add the project root to Python path so we can import blobify modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def sample_files(tmp_path):
    """Create sample test files in the temporary directory."""
    files = {}

    # Python file
    py_file = tmp_path / "test.py"
    py_file.write_text("print('hello')")
    files["py_file"] = py_file

    # Text file
    txt_file = tmp_path / "README.md"
    txt_file.write_text("# Test Project")
    files["txt_file"] = txt_file

    # Log file
    log_file = tmp_path / "test.log"
    log_file.write_text("Log entry")
    files["log_file"] = log_file

    # Create subdirectory with files
    sub_dir = tmp_path / "src"
    sub_dir.mkdir()
    sub_file = sub_dir / "module.py"
    sub_file.write_text("def hello(): pass")
    files["sub_file"] = sub_file

    return files


@pytest.fixture
def mock_git_repo(tmp_path):
    """Create a mock git repository structure."""
    git_dir = tmp_path / ".git"
    git_dir.mkdir()

    gitignore = tmp_path / ".gitignore"
    gitignore.write_text("*.log\n__pycache__/\n")

    return {"git_root": tmp_path, "git_dir": git_dir, "gitignore": gitignore}
