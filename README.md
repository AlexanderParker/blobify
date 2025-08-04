<div align="center">
  <h1>
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="misc/blobify-light.svg">
      <source media="(prefers-color-scheme: light)" srcset="misc/blobify-dark.svg">
      <img alt="Blobify" src="misc/blobify-dark.svg" width="48" height="48" style="vertical-align: middle; margin-right: 12px;">
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
pip install git+https://github.com/AlexanderParker/blobify.git
```

Basic usage:

```bash
# Package current directory to clipboard
bfy . --copy-to-clipboard=true

# Or run without directory if .blobify exists
bfy --copy-to-clipboard=true

# List available contexts from .blobify file
bfy -x

# Extract only function signatures
bfy . --filter '"signatures","^(def|class)\s+"' --copy-to-clipboard=true

# Extract functions from Python files only
bfy . --filter '"py-functions","^def","*.py"' --copy-to-clipboard=true

# Use specific context
bfy -x docs-only --copy-to-clipboard=true
```

**Key features:** Respects `.gitignore`, automatic sensitive data scrubbing, includes line numbers, supports custom filtering via `.blobify` configuration, content filters for extracting specific patterns with file targeting, context listing for easy discovery, cross-platform clipboard support, **context inheritance** for reusable configurations.

**ΓÜá∩╕Å Important Notice:** The scrubbing feature is not guaranteed to work; it may not detect some sensitive data. Consider it a best-effort helper only. Always review output before sharing.

## Command Line Options

```
bfy [directory] [options]
```

- `directory` - Directory to scan (optional, defaults to current directory if .blobify file exists)
- `--output-filename <file>` - Output file path (optional, defaults to stdout)
- `-x,` `--context [name]` - Use specific context from .blobify file, or list available contexts if no name provided
- `-f,` `--filter <"name","regex","filepattern">` - Content filter: extract only lines matching regex pattern, optionally restricted to files matching filepattern (can be used multiple times)
- `--debug=true|false` - Enable debug output for gitignore and .blobify processing (default: false)
- `--enable-scrubbing=true|false` - Enable scrubadub processing of sensitive data (default: true)
- `--output-line-numbers=true|false` - Include line numbers in file content output (default: true)
- `--output-index=true|false` - Include file index section at start of output (default: true)
- `--output-content=true|false` - Include file contents in output (default: true)
- `--output-metadata=true|false` - Include file metadata (size, timestamps, status) in output (default: true)
- `--show-excluded=true|false` - Show excluded files in file contents section (default: true)
- `--copy-to-clipboard=true|false` - Copy output to clipboard (default: false)
- `--list-patterns=none|ignored|contexts` - List patterns and exit: 'ignored' shows built-in patterns, 'contexts' shows available contexts (default: none)

## Content Filters

Extract specific patterns from your files for focused AI analysis:

### Basic Filters

```bash
# Function and class definitions
bfy . --filter '"signatures","^(def|class)\s+"' --copy-to-clipboard=true

# Import statements
bfy . --filter '"imports","^(import|from)"' --copy-to-clipboard=true

# Multiple filters (OR logic)
bfy . --filter '"funcs","^def"' --filter '"imports","^import"' --copy-to-clipboard=true
```

### File-Targeted Filters

Target specific file types with the new file pattern syntax:

```bash
# Python functions only
bfy . --filter '"py-functions","^def","*.py"' --copy-to-clipboard=true

# JavaScript functions only
bfy . --filter '"js-functions","^function","*.js"' --copy-to-clipboard=true

# CSS selectors from stylesheets
bfy . --filter '"css-selectors","^[.#][a-zA-Z]","*.css"' --copy-to-clipboard=true

# API routes from specific backend files
bfy . --filter '"routes","@app\.(get|post|put|delete)","app.py"' --copy-to-clipboard=true

# SQL queries from migration files
bfy . --filter '"sql","^(SELECT|INSERT|UPDATE|DELETE)","migrations/*.sql"' --copy-to-clipboard=true

# Configuration keys from specific config files
bfy . --filter '"config-keys","^[A-Z_]+\s*=","config/*.py"' --copy-to-clipboard=true

# Test functions from test files only
bfy . --filter '"tests","^def test_","test_*.py"' --copy-to-clipboard=true

# React components from JSX files
bfy . --filter '"components","^(function|const)\s+[A-Z]","*.jsx"' --copy-to-clipboard=true
```

### Complex Combinations

```bash
# Backend API analysis: routes from Python + SQL from migrations
bfy . --filter '"api-routes","@app\.","*.py"' --filter '"queries","^(SELECT|INSERT)","*.sql"' --copy-to-clipboard=true

# Frontend component analysis: React + CSS
bfy . --filter '"components","^(function|const)\s+[A-Z]","*.jsx"' --filter '"styles","^\.[a-z]","*.css"' --copy-to-clipboard=true

# Error handling across different file types
bfy . --filter '"py-errors","(except|raise)","*.py"' --filter '"js-errors","(catch|throw)","*.js"' --copy-to-clipboard=true
```

Filter syntax: `"name","regex","filepattern"` where:

- `name` - Filter identifier (for display)
- `regex` - Regular expression to match content lines
- `filepattern` - Optional file glob pattern (defaults to `*` for all files if omitted)

If you provide only two values like `"name","regex"`, the filter applies to all files. Single values like `"regex"` use the regex as both name and pattern.

## .blobify Configuration

Create a `.blobify` file in your project directory for custom configurations. When a `.blobify` file exists in your current directory, you can run `bfy` without specifying a directory argument.

### Basic Configuration

```
# Default configuration options
@copy-to-clipboard=true
@show-excluded=false

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
-**
+*.md
+docs/**

[python-analysis]
# Python-specific code analysis
@filter="functions","^def","*.py"
@filter="classes","^class","*.py"
@filter="imports","^(import|from)","*.py"
@output-line-numbers=false
@show-excluded=false
+*.py

[frontend-components]
# Frontend component analysis
@filter="react","^(function|const)\s+[A-Z]","*.jsx"
@filter="styles","^\.[a-z-]+","*.css"
@filter="types","^(interface|type)","*.ts"
+src/**/*.jsx
+src/**/*.css
+src/**/*.ts

[api-analysis]
# Backend API analysis
@filter="routes","@app\.(get|post|put|delete)","*.py"
@filter="models","^class.*Model","models/*.py"
@filter="schemas","^class.*Schema","schemas/*.py"
+*.py
+migrations/*.sql

[todos]
# Find all TODOs and FIXMEs
@filter="todos","(TODO|FIXME|XXX)"
@show-excluded=false
+**
```

### Context Inheritance

**NEW:** Contexts can now inherit from other contexts, allowing for powerful reusable configurations:

```
# Base configuration
@copy-to-clipboard=true
@debug=true
+*.py
-*.pyc

[backend:default]
# Inherits @copy-to-clipboard=true, @debug=true, +*.py, -*.pyc from default
+*.sql
+migrations/**
@filter="functions","^def","*.py"
@filter="models","^class.*Model","models/*.py"

[frontend:default]
# Also inherits from default
+*.js
+*.vue
+*.css
@filter="components","^(function|const)\s+[A-Z]","*.jsx"

[full:backend,frontend]
# Multiple inheritance - combines backend + frontend
+*.md
+docs/**
@show-excluded=false
```

**Inheritance Rules:**

- Use `[context:parent]` for single inheritance
- Use `[context:parent1,parent2]` for multiple inheritance
- Contexts can only inherit from contexts defined earlier in the file
- Child contexts inherit all patterns and options from parents, then add their own
- Cannot redefine the `default` context - it's automatically created
- Inheritance order is preserved: parent1 ΓåÆ parent2 ΓåÆ child

### Context Discovery

List available contexts before using them:

```bash
# List contexts
bfy -x
bfy --context

# Example output:
# Available contexts:
# ====================
#   docs-only: Documentation review context
#   python-analysis (inherits from default): Python code analysis
#   api-analysis (inherits from backend): Server-side API analysis
#   full (inherits from backend,frontend): Complete codebase
#
# Use with: bfy -x <context-name>
```

### Configuration Syntax

- `@option=value` - Set default configuration option (`@debug=true`, `@copy-to-clipboard=true`, `@output-content=false`, etc.)
- `@filter="name","regex","filepattern"` - Set default content filter with CSV format for file targeting
- `+pattern` - Include files (overrides gitignore)
- `-pattern` - Exclude files
- `[context-name]` - Define named contexts
- `[context-name:parent]` - Define context with single inheritance
- `[context-name:parent1,parent2]` - Define context with multiple inheritance
- Supports `*` and `**` wildcards

## Common Use Cases

```bash
# Basic usage
bfy . --copy-to-clipboard=true                              # Copy project to clipboard
bfy -x                                                      # List available contexts
bfy -x docs-only --copy-to-clipboard=true                   # Use docs context

# Context inheritance
bfy -x backend --copy-to-clipboard=true                     # Use backend context (inherits from default)
bfy -x full --copy-to-clipboard=true                        # Use full context (inherits from multiple parents)

# File-targeted filtering
bfy . --filter '"py-funcs","^def","*.py"' --copy-to-clipboard=true         # Python functions only
bfy . --filter '"api-routes","@app\.","*.py"' --copy-to-clipboard=true     # API routes from Python files
bfy . --filter '"components","^function","*.jsx"' --copy-to-clipboard=true # React components from JSX files

# Cross-language analysis
bfy . --filter '"backend-funcs","^def","*.py"' --filter '"frontend-funcs","^function","*.js"' --copy-to-clipboard=true

# Clean output
bfy . --show-excluded=false --output-metadata=false --copy-to-clipboard=true  # Only included files
bfy . --output-content=false --copy-to-clipboard=true       # Index only

# Save to file
bfy . --output-filename=project-summary.txt                 # Save to file
bfy . --filter '"sigs","^def","*.py"' --output-filename=overview.txt   # Filtered overview
```

## Efficient Token Usage

For large projects, use contexts and targeted filters to reduce AI token consumption:

```bash
# Project overview (minimal tokens)
bfy -x python-analysis --copy-to-clipboard=true

# API-specific analysis
bfy -x api-analysis --copy-to-clipboard=true

# Find specific patterns in specific files
bfy . --filter '"errors","(except|Error)","*.py"' --show-excluded=false --copy-to-clipboard=true

# Frontend-only analysis
bfy . --filter '"components","^(function|const)","*.jsx"' --filter '"styles","^\.","*.css"' --copy-to-clipboard=true

# Documentation only
bfy -x docs-only --copy-to-clipboard=true

# Clean summary with file targeting
bfy . --filter '"sigs","^(def|class)","*.py"' --output-line-numbers=false --show-excluded=false --copy-to-clipboard=true
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

## License

[MIT License](LICENSE) - see the project repository for details.
