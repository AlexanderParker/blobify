"""Tests for version consistency across the project."""

import re
from pathlib import Path

import pytest


class TestVersionConsistency:
    """Test cases for version consistency across project files."""

    def test_main_version_matches_pyproject_toml(self):
        """Test that __version__ in main.py matches version in pyproject.toml."""
        # Get project root (assuming tests are in tests/ directory)
        project_root = Path(__file__).parent.parent

        # Read version from main.py
        main_py_path = project_root / "blobify" / "main.py"
        assert main_py_path.exists(), f"main.py not found at {main_py_path}"

        main_content = main_py_path.read_text(encoding="utf-8")
        main_version_match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', main_content)
        assert main_version_match, "Could not find __version__ in main.py"
        main_version = main_version_match.group(1)

        # Read version from pyproject.toml
        pyproject_path = project_root / "pyproject.toml"
        assert pyproject_path.exists(), f"pyproject.toml not found at {pyproject_path}"

        pyproject_content = pyproject_path.read_text(encoding="utf-8")
        pyproject_version_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', pyproject_content)
        assert pyproject_version_match, "Could not find version in pyproject.toml"
        pyproject_version = pyproject_version_match.group(1)

        # Versions should match
        assert main_version == pyproject_version, (
            f"Version mismatch: main.py has '{main_version}' but pyproject.toml has '{pyproject_version}'. " "Please update both files to have the same version."
        )

    def test_version_format_is_valid(self):
        """Test that the version follows semantic versioning format."""
        from blobify.main import __version__

        # Check that version follows semantic versioning pattern (major.minor.patch)
        # Optionally with pre-release or build metadata
        semver_pattern = r"^\d+\.\d+\.\d+(?:-[a-zA-Z0-9]+(?:\.[a-zA-Z0-9]+)*)?(?:\+[a-zA-Z0-9]+(?:\.[a-zA-Z0-9]+)*)?$"
        assert re.match(semver_pattern, __version__), (
            f"Version '{__version__}' does not follow semantic versioning format. " "Expected format: major.minor.patch (e.g., '1.0.0', '1.2.3-alpha', '2.0.0+build.1')"
        )

    def test_imported_version_accessible(self):
        """Test that version can be imported from main module."""
        from blobify.main import __version__

        # Should be a non-empty string
        assert isinstance(__version__, str)
        assert len(__version__) > 0
        assert __version__.strip() == __version__  # No leading/trailing whitespace

    def test_version_exposed_in_package_init(self):
        """Test that version is properly exposed in package __init__.py."""
        # This ensures the version is accessible via blobify.__version__
        import blobify

        # Should have __version__ attribute
        assert hasattr(blobify, "__version__")

        # Should match the version in main.py
        from blobify.main import __version__ as main_version

        assert blobify.__version__ == main_version


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
