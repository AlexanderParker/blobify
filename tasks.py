"""Development tasks for blobify using invoke."""

from invoke import task
from pathlib import Path
import shutil


@task
def install_dev(c):
    """Install development dependencies."""
    c.run("pip install -e .[scrubbing]")
    c.run(
        "pip install invoke black isort flake8 coverage unittest-xml-reporting pre-commit"
    )
    c.run("pre-commit install")


@task
def test(c):
    """Run tests."""
    c.run("python test_runner.py")


@task
def test_verbose(c):
    """Run tests with verbose output."""
    c.run("python test_runner.py --verbosity=2")


@task
def coverage(c):
    """Run tests with coverage."""
    c.run("coverage run test_runner.py")
    c.run("coverage report -m")
    c.run("coverage html")


@task
def lint(c):
    """Run linting checks."""
    c.run("flake8 blobify/ tests/", warn=True)
    c.run("black --check blobify/ tests/", warn=True)
    c.run("isort --check-only blobify/ tests/", warn=True)


@task
def format(c):
    """Format code."""
    c.run("black blobify/ tests/")
    c.run("isort blobify/ tests/")


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
    dirs_to_remove = ["build", "dist", "htmlcov", ".pytest_cache"]
    for dir_name in dirs_to_remove:
        path = Path(dir_name)
        if path.exists() and path.is_dir():
            shutil.rmtree(path)
            print(f"Removed {path}")

    files_to_remove = [".coverage", "test-results.xml"]
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
