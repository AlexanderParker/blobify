"""Development tasks for blobify using invoke."""

import shutil
from pathlib import Path

from invoke import task


@task
def test_to_clip(c):
    """Run tests and copy output to clipboard."""
    import subprocess
    import sys

    # Capture both stdout and stderr
    result = c.run("pytest -v", hide=True, warn=True)
    output = result.stdout + result.stderr

    # Copy to clipboard
    if sys.platform == "win32":
        subprocess.run("clip", input=output, text=True, shell=True)
    elif sys.platform == "darwin":
        subprocess.run("pbcopy", input=output, text=True)
    else:
        subprocess.run(["xclip", "-selection", "clipboard"], input=output, text=True)

    print("Test output copied to clipboard")


@task
def install_dev(c):
    """Install development dependencies."""
    c.run("pip install -e .[dev,scrubbing]")
    c.run("pre-commit install")


@task
def test(c):
    """Run tests."""
    c.run("pytest")


@task
def test_verbose(c):
    """Run tests with verbose output."""
    c.run("pytest -v")


@task
def test_xunit(c):
    """Run tests with xunit XML output."""
    c.run("pytest --junitxml=test-results.xml")


@task
def coverage(c):
    """Run tests with coverage."""
    c.run("pytest --cov=blobify --cov-report=term-missing --cov-report=html")


@task
def lint(c):
    """Run linting checks."""
    import subprocess
    import sys

    c.run("flake8 blobify/ tests/", warn=True)

    # Run black with proper UTF-8 handling
    try:
        result = subprocess.run(["black", "--check", "blobify/", "tests/"], capture_output=True, text=True, encoding="utf-8", check=False)
        # Print output directly to avoid invoke's encoding issues
        if result.stdout:
            sys.stdout.write(result.stdout)
        if result.stderr:
            sys.stderr.write(result.stderr)
    except subprocess.CalledProcessError:
        pass  # Black will return non-zero if formatting needed

    c.run("isort --check-only blobify/ tests/", warn=True)


@task
def format(c):
    """Format code."""
    # Set encoding environment for subprocess
    import os

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONLEGACYWINDOWSSTDIO"] = "0"

    c.run("black blobify/ tests/", env=env)
    c.run("isort blobify/ tests/", env=env)


@task
def clean(c):
    """Clean temporary files."""
    # Remove Python cache
    for path in Path(".").rglob("__pycache__"):
        if path.is_dir():
            shutil.rmtree(path)
            print(f"Removed {path}")

    for path in Path(".").rglob("*.pyc"):
        path.unlink()
        print(f"Removed {path}")

    # Remove build artifacts
    dirs_to_remove = ["build", "dist", "htmlcov", ".pytest_cache", ".coverage"]
    for dir_name in dirs_to_remove:
        path = Path(dir_name)
        if path.exists():
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            print(f"Removed {path}")

    files_to_remove = ["test-results.xml"]
    for file_name in files_to_remove:
        path = Path(file_name)
        if path.exists():
            path.unlink()
            print(f"Removed {path}")

    for path in Path(".").glob("TEST-*.xml"):
        path.unlink()
        print(f"Removed {path}")


@task
def all_checks(c):
    """Run all checks (format, lint, test)."""
    format(c)
    lint(c)
    test(c)
