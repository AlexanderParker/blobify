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


def run_with_formatting(cmd, capture_output=False, env=None):
    """Run subprocess with proper terminal formatting preserved."""
    import os
    import subprocess
    import sys

    if env is None:
        env = os.environ.copy()

    try:
        if capture_output:
            result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", check=False, env=env)
            if result.stdout:
                sys.stdout.write(result.stdout)
            if result.stderr:
                sys.stderr.write(result.stderr)
            return result.returncode
        else:
            result = subprocess.run(cmd, encoding="utf-8", check=False, env=env)
            return result.returncode
    except subprocess.CalledProcessError as e:
        return e.returncode


@task
def test(c):
    """Run tests."""
    import sys

    returncode = run_with_formatting(["pytest"])
    sys.exit(returncode)


@task
def test_verbose(c):
    """Run tests with verbose output."""
    import sys

    returncode = run_with_formatting(["pytest", "-v"])
    sys.exit(returncode)


@task
def test_xunit(c):
    """Run tests with xunit XML output."""
    import sys

    returncode = run_with_formatting(["pytest", "--junitxml=test-results.xml"])
    sys.exit(returncode)


@task
def coverage(c):
    """Run tests with coverage."""
    import sys

    returncode = run_with_formatting(["pytest", "--cov=blobify", "--cov-report=term-missing", "--cov-report=html"])
    sys.exit(returncode)


@task
def lint(c):
    """Run linting checks."""
    import os

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONLEGACYWINDOWSSTDIO"] = "0"

    # Run flake8
    returncode1 = run_with_formatting(["flake8", "blobify/", "tests/"], capture_output=True, env=env)
    if returncode1 != 0:
        print("flake8 failed")

    # Run black
    returncode2 = run_with_formatting(["black", "--check", "blobify/", "tests/"], capture_output=True, env=env)
    if returncode2 != 0:
        print("black formatting check failed")

    # Run isort
    returncode3 = run_with_formatting(["isort", "--check-only", "blobify/", "tests/"], capture_output=True, env=env)
    if returncode3 != 0:
        print("isort check failed")


@task
def format(c):
    """Format code."""
    import os
    import sys

    # Set encoding environment for subprocess
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONLEGACYWINDOWSSTDIO"] = "0"

    # Run black
    returncode1 = run_with_formatting(["black", "blobify/", "tests/"], env=env)
    # Run isort
    returncode2 = run_with_formatting(["isort", "blobify/", "tests/"], env=env)

    # Exit with error if either command failed
    if returncode1 != 0:
        sys.exit(returncode1)
    if returncode2 != 0:
        sys.exit(returncode2)


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
def all(c):
    """Run all checks (format, lint, test)."""
    format(c)
    lint(c)
    test(c)
