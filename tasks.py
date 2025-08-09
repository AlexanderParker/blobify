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
    c.run("pip install -e .[dev]")
    c.run("pre-commit install")


def run_with_formatting(cmd, capture_output=False, env=None):
    """Run subprocess with proper terminal formatting preserved."""
    import os
    import shutil
    import subprocess
    import sys

    if env is None:
        env = os.environ.copy()

    # Resolve full path for the command if it's just a command name
    if cmd and not os.path.isabs(cmd[0]):
        full_path = shutil.which(cmd[0], path=env.get("PATH"))
        if full_path:
            cmd = [full_path] + cmd[1:]

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
def clean_dist(c):
    """Clean distribution artifacts."""
    dist_path = Path("dist")
    if dist_path.exists():
        shutil.rmtree(dist_path)
        print(f"Removed {dist_path}")


@task
def build(c):
    """Build the package."""
    import sys

    returncode = run_with_formatting(["python", "-m", "build"])
    if returncode != 0:
        print("Build failed")
        sys.exit(returncode)
    print("Package built successfully")


@task
def publish_test(c):
    """Upload to TestPyPI."""
    import sys

    dist_path = Path("dist")
    if not dist_path.exists() or not list(dist_path.glob("*")):
        print("No distribution files found. Run 'invoke build' first.")
        sys.exit(1)

    returncode = run_with_formatting(["python", "-m", "twine", "upload", "--repository", "testpypi", "dist/*"])
    if returncode != 0:
        print("TestPyPI upload failed")
        sys.exit(returncode)
    print("Successfully uploaded to TestPyPI")


@task
def publish(c):
    """Upload to production PyPI."""
    import sys

    dist_path = Path("dist")
    if not dist_path.exists() or not list(dist_path.glob("*")):
        print("No distribution files found. Run 'invoke build' first.")
        sys.exit(1)

    # Confirm production upload
    response = input("Upload to production PyPI? This cannot be undone. (y/N): ")
    if response.lower() != "y":
        print("Upload cancelled")
        return

    returncode = run_with_formatting(["python", "-m", "twine", "upload", "dist/*"])
    if returncode != 0:
        print("PyPI upload failed")
        sys.exit(returncode)
    print("Successfully uploaded to production PyPI")


@task
def test_install(c):
    """Install from TestPyPI to verify the package."""
    import sys

    returncode = run_with_formatting(
        [
            "pip",
            "install",
            "--index-url",
            "https://test.pypi.org/simple/",
            "--extra-index-url",
            "https://pypi.org/simple/",
            "blobify",
        ]
    )
    if returncode != 0:
        print("TestPyPI installation failed")
        sys.exit(returncode)
    print("Successfully installed from TestPyPI")


@task
def get_version(c):
    """Get current version from pyproject.toml."""
    import tomllib

    with open("pyproject.toml", "rb") as f:
        data = tomllib.load(f)

    version = data["project"]["version"]
    print(f"Current version: v{version}")
    return version


@task
def tag_release(c):
    """Tag the current release and push to remote."""
    import sys

    version = get_version(c)
    tag = f"v{version}"

    # Check if tag already exists
    result = c.run(f"git tag -l {tag}", hide=True)
    if result.stdout.strip():
        print(f"Tag {tag} already exists")
        return

    # Create and push tag
    returncode1 = run_with_formatting(["git", "tag", tag])
    if returncode1 != 0:
        print("Failed to create tag")
        sys.exit(returncode1)

    returncode2 = run_with_formatting(["git", "push", "origin", tag])
    if returncode2 != 0:
        print("Failed to push tag")
        sys.exit(returncode2)

    print(f"Successfully created and pushed tag {tag}")


@task
def bump_patch(c):
    """Bump patch version (x.x.X)."""
    _bump_version(c, "patch")


@task
def bump_minor(c):
    """Bump minor version (x.X.0)."""
    _bump_version(c, "minor")


@task
def bump_major(c):
    """Bump major version (X.0.0)."""
    _bump_version(c, "major")


def _bump_version(c, bump_type):
    """Bump version in both pyproject.toml and blobify/main.py."""
    import re
    import tomllib

    import tomli_w

    # Read current version from pyproject.toml
    with open("pyproject.toml", "rb") as f:
        data = tomllib.load(f)

    current_version = data["project"]["version"]
    print(f"Current version: {current_version}")

    # Parse version
    version_parts = current_version.split(".")
    if len(version_parts) != 3:
        print(f"Invalid version format: {current_version}")
        return

    major, minor, patch = map(int, version_parts)

    # Bump version
    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    elif bump_type == "patch":
        patch += 1

    new_version = f"{major}.{minor}.{patch}"
    print(f"New version: {new_version}")

    # Update pyproject.toml
    data["project"]["version"] = new_version
    with open("pyproject.toml", "wb") as f:
        tomli_w.dump(data, f)

    # Update blobify/main.py
    main_py_path = Path("blobify/main.py")
    if main_py_path.exists():
        content = main_py_path.read_text()

        # Find and replace __version__ line
        version_pattern = r'__version__\s*=\s*["\']([^"\']+)["\']'
        new_content = re.sub(version_pattern, f'__version__ = "{new_version}"', content)

        if new_content != content:
            main_py_path.write_text(new_content)
            print(f"Updated version in {main_py_path}")
        else:
            print(f"Warning: Could not find __version__ in {main_py_path}")
    else:
        print(f"Warning: {main_py_path} not found")

    print(f"Version bumped from {current_version} to {new_version}")


@task
def set_version(c, version):
    """Set specific version (e.g., invoke set-version 1.2.3)."""
    import re
    import tomllib

    import tomli_w

    # Validate version format
    if not re.match(r"^\d+\.\d+\.\d+$", version):
        print(f"Invalid version format: {version}. Use format: major.minor.patch")
        return

    # Read current version from pyproject.toml
    with open("pyproject.toml", "rb") as f:
        data = tomllib.load(f)

    current_version = data["project"]["version"]
    print(f"Current version: {current_version}")
    print(f"Setting version to: {version}")

    # Update pyproject.toml
    data["project"]["version"] = version
    with open("pyproject.toml", "wb") as f:
        tomli_w.dump(data, f)

    # Update blobify/main.py
    main_py_path = Path("blobify/main.py")
    if main_py_path.exists():
        content = main_py_path.read_text()

        # Find and replace __version__ line
        version_pattern = r'__version__\s*=\s*["\']([^"\']+)["\']'
        new_content = re.sub(version_pattern, f'__version__ = "{version}"', content)

        if new_content != content:
            main_py_path.write_text(new_content)
            print(f"Updated version in {main_py_path}")
        else:
            print(f"Warning: Could not find __version__ in {main_py_path}")
    else:
        print(f"Warning: {main_py_path} not found")

    print(f"Version updated from {current_version} to {version}")


@task
def api_reference(c):
    """Generate API reference documentation using blobify."""
    import sys

    returncode = run_with_formatting(["python", "-m", "blobify", ".", "--context=api-reference", "--output-filename=API_REFERENCE.md", "--copy-to-clipboard=false"])
    if returncode != 0:
        print("API reference generation failed")
        sys.exit(returncode)
    print("API reference generated successfully as API_REFERENCE.md")


@task
def all(c):
    """Run all checks (format, lint, test)."""
    format(c)
    lint(c)
    test(c)
