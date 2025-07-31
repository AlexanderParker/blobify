"""Pytest configuration and shared fixtures for blobify tests."""

import sys
import tempfile
from pathlib import Path

import pytest

# Add the project root to Python path so we can import blobify modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    # Cleanup
    for file in temp_dir.rglob("*"):
        if file.is_file():
            file.unlink()
    for dir in sorted(temp_dir.rglob("*"), reverse=True):
        if dir.is_dir():
            dir.rmdir()
    temp_dir.rmdir()


@pytest.fixture
def sample_files(temp_dir):
    """Create sample test files in the temporary directory."""
    files = {}

    # Python file
    py_file = temp_dir / "test.py"
    py_file.write_text("print('hello')")
    files["py_file"] = py_file

    # Text file
    txt_file = temp_dir / "README.md"
    txt_file.write_text("# Test Project")
    files["txt_file"] = txt_file

    # Log file
    log_file = temp_dir / "test.log"
    log_file.write_text("Log entry")
    files["log_file"] = log_file

    # Create subdirectory with files
    sub_dir = temp_dir / "src"
    sub_dir.mkdir()
    sub_file = sub_dir / "module.py"
    sub_file.write_text("def hello(): pass")
    files["sub_file"] = sub_file

    return files


@pytest.fixture
def mock_git_repo(temp_dir):
    """Create a mock git repository structure."""
    git_dir = temp_dir / ".git"
    git_dir.mkdir()

    gitignore = temp_dir / ".gitignore"
    gitignore.write_text("*.log\n__pycache__/\n")

    return {"git_root": temp_dir, "git_dir": git_dir, "gitignore": gitignore}
