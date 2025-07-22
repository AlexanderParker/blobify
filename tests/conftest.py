"""Pytest configuration and shared fixtures for blobify tests."""

import sys
from pathlib import Path

# Add the project root to Python path so we can import blobify modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
