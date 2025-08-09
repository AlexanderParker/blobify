<div align="center">
  <h1>
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/AlexanderParker/blobify/main/misc/blobify-light.svg">
      <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/AlexanderParker/blobify/main/misc/blobify-dark.svg">
      <img alt="Blobify" src="https://raw.githubusercontent.com/AlexanderParker/blobify/main/misc/blobify-dark.svg" width="48" height="48" style="vertical-align: middle; margin-right: 12px;">
    </picture>
    Blobify
  </h1>
  <p><em>Package your entire codebase into a single text file for AI consumption</em></p>
</div>

[![PyPI version](https://img.shields.io/pypi/v/blobify)](https://pypi.org/project/blobify/)
[![Python version](https://img.shields.io/pypi/pyversions/blobify)](https://pypi.org/project/blobify/)
[![License](https://img.shields.io/pypi/l/blobify)](https://github.com/AlexanderParker/blobify/blob/main/LICENSE)
[![Tests](https://img.shields.io/github/actions/workflow/status/AlexanderParker/blobify/test.yml?branch=main&label=tests)](https://github.com/AlexanderParker/blobify/actions)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Feed your project to Claude, ChatGPT, or other AI assistants for code analysis, debugging, refactoring, documentation, or feature development.

## Quick Start

Install:

```bash
pip install blobify
```

Basic usage:

```bash
# Package current directory to clipboard
bfy . --copy-to-clipboard=true

# Or run without directory if .blobify exists
bfy --copy-to-clipboard=true

```

## Command Line Options

```
bfy [directory] [options]
```

- `directory` - Directory to scan (optional, defaults to current directory if .blobify file exists)
- `--output-filename <file>` - Output file path (optional, defaults to stdout)
- `-x,` `--context [name]` - Use specific context from .blobify file, or list available contexts if no name provided
- `-f,` `--filter <"name","regex","filepattern">` - Content filter: extract only lines matching regex pattern, optionally restricted to files matching filepattern (can be used multiple times)
- `--debug`=`true|false` - Enable debug output for gitignore and .blobify processing (default: false)
- `--enable-scrubbing`=`true|false` - Enable scrubadub processing of sensitive data (default: true)
- `--output-line-numbers`=`true|false` - Include line numbers in file content output (default: true)
- `--output-index`=`true|false` - Include file index section at start of output (default: true)
- `--output-content`=`true|false` - Include file contents in output (default: true)
- `--output-metadata`=`true|false` - Include file metadata (size, timestamps, status) in output (default: true)
- `--show-excluded`=`true|false` - Show excluded files in file contents section (default: true)
- `--copy-to-clipboard`=`true|false` - Copy output to clipboard (default: false)
- `--suppress-timestamps`=`true|false` - Suppress timestamps in output for reproducible builds (default: false)
- `--list-patterns`=`none|ignored|contexts` - List patterns and exit: 'ignored' shows built-in patterns, 'contexts' shows available contexts (default: none)

**Key features:** Respects `.gitignore`, automatic sensitive data scrubbing, includes line numbers, supports custom filtering via `.blobify` configuration, content filters for extracting specific patterns with file targeting, context listing for easy discovery, cross-platform clipboard support, **context inheritance** for reusable configurations.

**Important Notice:** The scrubbing feature is not guaranteed to work; it may not detect some sensitive data. Consider it a best-effort helper only. Always review output before sharing.

## Content Filters

You can add multiple filters to extract specific patterns from files.

The filter syntax is: `"name","regex","filepattern"` where:

- `name` - Filter identifier (for display)
- `regex` - Regular expression to match content lines
- `filepattern` - **Optional** file glob pattern (defaults to `*` for all files if omitted)

If you provide only two values like `"name","regex"`, the filter applies to all matched files. Single values like `"regex"` use the regex as both name and pattern.

### Basic Filters

```bash
# Function and class definitions
bfy . --filter '"signatures","^(def|class)\s+"' --copy-to-clipboard=true

# Multiple filters (OR logic)
bfy . --filter '"funcs","^def"' --filter '"imports","^import"' --copy-to-clipboard=true
```

### File-Targeted Filters

Target specific file types with the file pattern syntax:

```bash
# Python functions only
bfy . --filter '"py-functions","^def","*.py"' --copy-to-clipboard=true

# Backend API analysis: routes from Python + SQL from migrations
bfy . --filter '"api-routes","@app\.","*.py"' --filter '"queries","^(SELECT|INSERT)","*.sql"' --copy-to-clipboard=true

```

## .blobify Configuration

Create a `.blobify` file in your project directory for custom configurations. When a `.blobify` file exists in your current directory, you can run `bfy` without specifying a directory argument.

**VS Code Extension:** For `.blobify` file syntax highlighting and validation, install the [Blobify Format extension](https://marketplace.visualstudio.com/items?itemName=ShentonConsulting.blobify-format) from the VS Code Marketplace.

### Basic Configuration

- `@option=value` - Set default configuration option (`@debug=true`, `@copy-to-clipboard=true`, `@output-content=false`, etc.)
- `@filter="name","regex","filepattern"` - Set default content filter with CSV format for file targeting
- `+pattern` - Include files (overrides gitignore)
- `-pattern` - Exclude files
- `[context-name]` - Define named contexts
- `[context-name:parent]` - Define context with single inheritance
- `[context-name:parent1,parent2]` - Define context with multiple inheritance
- `## instruction` - Add LLM/AI analysis instructions (appears in output header)
- Supports `*` and `**` wildcards

```
# Default configuration options
@copy-to-clipboard=true
@show-excluded=false
@suppress-timestamps=true

# Content filters with file targeting (CSV format)
@filter="signatures","^(def|class)\s+","*.py"
@filter="imports","^(import|from)","*.py"
@filter="routes","@app\.(get|post)","app.py"

# Include/exclude patterns
+.github/**
+.pre-commit-config.yaml
-*.log
-temp/**

[docs-only]
# Documentation review context
## Review this documentation for clarity and completeness
## Check for broken links and outdated information
-**
+*.md
+docs/**

[security-review]
## This codebase represents a web application built with Flask
## Focus on security vulnerabilities including SQL injection and XSS
## Pay special attention to authentication and authorization mechanisms
+*.py
+templates/*.html

[todos]
# Find all TODOs and FIXMEs
@filter="todos","(TODO|FIXME|XXX)"
@show-excluded=false
+**
```

LLM instructions (lines starting with `##`) appear in the output header as:

```
# Instructions for AI/LLM analysis:
# * Review this documentation for clarity and completeness
# * Check for broken links and outdated information
```

### Context Inheritance

- Use `[context:parent]` for single inheritance
- Use `[context:parent1,parent2]` for multiple inheritance
- Contexts can only inherit from contexts defined earlier in the file
- Child contexts inherit all patterns and options from parents, then add their own
- Cannot redefine the `default` context - it's automatically created
- Inheritance order is preserved: parent1 → parent2 → child
- LLM instructions are also inherited from parent contexts

```
# Base configuration
@copy-to-clipboard=true
@debug=true
# Match nothing by default
-**

[backend:default]
# Inherits @copy-to-clipboard=true, @debug=true, +*.py, -*.pyc from default
## Analyze backend code for performance and security issues
+*.sql
+migrations/**
@filter="functions","^def","*.py"
@filter="models","^class.*Model","models/*.py"

[frontend:default]
# Also inherits from default
## Focus on component structure and state management
+*.js
+*.vue
+*.css
@filter="components","^(function|const)\s+[A-Z]","*.jsx"

[full:backend,frontend]
# Multiple inheritance - combines backend + frontend
## Perform comprehensive full-stack analysis
+*.md
+docs/**
@show-excluded=false
```

---

## Development

### Setup

1 - Clone and enter directory:

```bash
git clone https://github.com/AlexanderParker/blobify.git
cd blobify
```

2 - Create and activate virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows
```

3 - Install with dev dependencies:

```bash
pip install -e ".[dev]"
pre-commit install
```

### Run Tests

```bash
invoke test        # Run tests
invoke coverage    # Run with coverage
invoke format      # Format code
invoke lint        # Check code quality
invoke all         # Check everything
```

### For Maintainers

**Publishing to PyPI:**

This package is published to PyPI as `blobify`. Releases are managed using invoke tasks:

```bash
# On branch main - after any release-related PRs are merged in.

# Bump version (choose one):
invoke bump-patch     # 1.0.0 → 1.0.1
invoke bump-minor     # 1.0.0 → 1.1.0
invoke bump-major     # 1.0.0 → 2.0.0
# or set specific version:
invoke set-version 1.2.3

# Ensure all tests pass:
invoke all

# Clean any previous build artifacts:
invoke clean-dist

# Build the package:
invoke build

# Test upload to TestPyPI first (recommended):
invoke publish-test

# Upload to production PyPI (requires appropriate credentials):
invoke publish

# Finally tag the build with the new version number and push the tag to the remote:
invoke tag-release
```

**TestPyPI Testing:**

```bash
# Install from TestPyPI to verify the package:
invoke test-install
```

## License

[MIT License](https://github.com/AlexanderParker/blobify/blob/main/LICENSE) - see the project repository for details.
