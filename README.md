# Blobify

Package your entire codebase into a single text file for AI consumption. Feed your project to Claude, ChatGPT, or other AI assistants for code analysis, debugging, refactoring, documentation, or feature development.

## Quick Start

Install (basic):

```bash
pip install git+https://github.com/AlexanderParker/blobify.git
```

Install (with sensitive data scrubbing):

```bash
pip install "blobify[scrubbing] @ git+https://github.com/AlexanderParker/blobify.git"
```

Run (packages current directory and copies to clipboard):

```bash
bfy . --clip
```

Or simply run without arguments if you have a `.blobify` configuration file:

```bash
bfy --clip
```

Then paste into AI with prompts like "Review this code and suggest improvements" or "Add oauth authentication to this app".

**Key features:** Respects `.gitignore`, optional sensitive data scrubbing (see important notice below), includes line numbers, supports custom filtering via `.blobify` configuration, cross-platform clipboard support. Automatically excludes common build/cache directories (`.git`, `node_modules`, `__pycache__`, etc.) and binary files.

**⚠️ Important Notice:** The scrubbing feature is not guaranteed to work at all, it may not detect some sensitive data and it may find false positives; it is a best-effort helper feature only. It can be disabled with --noclean or not installed at all if you do not use the [scrubbing] option when installing. You should review the output of this utility to check for and clean up sensitive data before you use it anywhere.

## Command Line Options

```
bfy [directory] [options]
```

- `directory` - Directory to scan (optional, defaults to current directory if .blobify file exists)
- `-o, --output <file>` - Output file path (optional, defaults to stdout)
- `-x, --context <name>` - Use specific context from .blobify file
- `--clip` - Copy to clipboard (Windows/macOS/Linux support)
- `--noclean` - Disable sensitive data scrubbing
- `--no-line-numbers` - Disable line numbers in output
- `--no-index` - Disable file index section
- `--debug` - Show detailed processing information

## Examples

Output current directory to stdout (requires .blobify file):

```bash
bfy
```

Output specific directory to stdout:

```bash
bfy .
```

Copy to clipboard:

```bash
bfy . --clip
```

Copy to clipboard using .blobify defaults:

```bash
bfy --clip
```

Save to file:

```bash
bfy /path/to/project -o output.txt
```

Use context (if configured in .blobify):

```bash
bfy . -x docs-only --clip
```

Use context with .blobify defaults:

```bash
bfy -x docs-only --clip
```

## .blobify Configuration

The `.blobify` file lets you customise which files are included and set default command-line options. Blobify applies filters in this order: default exclusions → gitignore → .blobify excludes → .blobify includes. This means you can override gitignore rules when needed.

Create a `.blobify` file in your git root:

```
# Default switches (applied automatically)
@debug
@clip
@output=blob.txt

# Include files that would normally be excluded
+.pre-commit-config.yaml
+.github/**

# Exclude additional files
-*.log
-temp/**

[docs-only]
# Context for documentation review (use with -x docs-only or --context=docs-only)
-**
+*.md
+docs/**
```

**Syntax:**

- `@switch` - Set default boolean option (`@debug`, `@clip`, `@noclean`, `@no-line-numbers`, `@no-index`)
- `@key=value` - Set default option with value (`@output=filename.txt`)
- `+pattern` - Include files (overrides gitignore/default exclusions)
- `-pattern` - Exclude files
- `[context-name]` - Define named contexts for different views
- Supports `*` and `**` wildcards, patterns relative to git root

**Contexts:** Use `-x context-name` to apply different file filtering rules. Contexts are independent - they don't inherit patterns from the default section. Useful for documentation-only reviews (`docs-only`), code-only analysis (`code-only`), or security audits.

**Default Directory Behaviour:** When you have a `.blobify` file in your current directory, you can run `bfy` without specifying a directory argument - it will automatically use the current directory. This makes it easy to set up project-specific configurations and run blobify with just `bfy --clip` or `bfy -x context-name`.

## Efficient Usage

The file index and line numbers significantly improve AI response quality and accuracy, but they also increase token usage. For large projects approaching input limits, you can create contexts to reduce tokens:

**For projects with many small files** - Exclude the index first:

```
[compact]
@no-index
# Include all files but remove index to save tokens
```

**For projects with fewer large files** - Exclude line numbers first:

```
[compact]
@no-line-numbers
# Keep file index but remove line numbers to save tokens
```

**For maximum compression** - Exclude both:

```
[minimal]
@no-index
@no-line-numbers
# Minimal tokens for general analysis only
```

Use with: `bfy -x compact --clip` or `bfy -x minimal --clip`

---

## Development & Maintenance

### For Contributors

#### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/AlexanderParker/blobify.git
cd blobify

# Install development dependencies
pip install -e ".[dev,scrubbing]"

# Install pre-commit hooks
pre-commit install
```

#### Available Development Tasks

Use `invoke` for development tasks:

```bash
# Run tests
invoke test

# Run tests with coverage
invoke coverage

# Format code (black + isort)
invoke format

# Run linting checks
invoke lint

# Clean build artifacts
invoke clean

# Run all checks (format + lint + test)
invoke all-checks

# List all available tasks
invoke --list
```

#### Running Tests

```bash
# Basic test run
invoke test

# Verbose test output
invoke test-verbose

# With coverage report
invoke coverage

# Direct test runner (alternative)
python test_runner.py
```

#### Code Quality

The project uses:

- **black** for code formatting
- **isort** for import sorting
- **flake8** for linting
- **pre-commit** for automated checks

Pre-commit hooks run automatically on every commit and will:

- Format your code with black
- Check for common issues with flake8
- Run the test suite
- Clean up whitespace and line endings

You can run these manually with `invoke format` and `invoke lint`.

#### Project Structure

```
blobify/
├── blobify/                # Main package
│   ├── __init__.py
│   ├── main.py            # CLI entry point
│   ├── config.py          # .blobify configuration handling
│   ├── console.py         # Console output utilities
│   ├── content_processor.py  # File content processing
│   ├── file_scanner.py    # File discovery and filtering
│   ├── git_utils.py       # Git repository utilities
│   └── output_formatter.py   # Output generation
├── tests/                 # Test suite
│   ├── test_*.py         # Individual test modules
│   └── conftest.py       # Test configuration
├── tasks.py              # Development task definitions (invoke)
├── test_runner.py        # Test runner with xunit support
├── pyproject.toml        # Project configuration
├── .pre-commit-config.yaml   # Pre-commit hook configuration
└── .github/workflows/    # GitHub Actions CI/CD
```

### For Maintainers

#### Updating Dependencies

```bash
# Update pre-commit hook versions
pre-commit autoupdate

# Update Python dependencies
pip install --upgrade pip
pip install -e ".[dev,scrubbing]" --upgrade

# Check for outdated packages
pip list --outdated
```

#### Version Alignment

Keep these aligned across all configuration files:

- **pyproject.toml** `[project.optional-dependencies.dev]`
- **.pre-commit-config.yaml** `rev:` values
- **.github/workflows/test.yml** tool versions
- **tasks.py** tool commands

Current versions in use:

- pre-commit-hooks: `v4.5.0`
- black: `25.1.0`
- flake8: `7.0.0`
- Python: `3.10+`

#### Release Process

1. **Update version** in `pyproject.toml` and `blobify/__init__.py`
2. **Run full test suite**: `invoke coverage`
3. **Update CHANGELOG** (if maintained)
4. **Tag release**: `git tag v1.x.x`
5. **Push**: `git push origin main --tags`

#### CI/CD Pipeline

GitHub Actions automatically:

- Runs tests on Python 3.10, 3.11, 3.12
- Generates test reports with xunit format
- Publishes test results
- Handles optional dependencies gracefully

Check `.github/workflows/test.yml` for full pipeline configuration.

#### Common Maintenance Tasks

```bash
# Check code coverage
invoke coverage

# Update pre-commit hooks to latest versions
pre-commit autoupdate

# Run pre-commit on all files
pre-commit run --all-files

# Clean up development artifacts
invoke clean

# Check for security issues (if using additional tools)
# pip install safety bandit
# safety check
# bandit -r blobify/
```

#### Testing Strategy

The test suite provides high coverage with minimal test cases:

- **Unit tests** for each module in `tests/`
- **Integration tests** via `test_main.py`
- **Mock external dependencies** (git, file system, scrubadub)
- **Cross-platform testing** in CI
- **Coverage reporting** via GitHub Actions

Tests are designed to be fast, reliable, and comprehensive without being brittle.

## License

[MIT License](LICENSE) - see the project repository for details.
