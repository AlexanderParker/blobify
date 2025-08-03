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
bfy . --filter "signatures:^(def|class)\s+" --copy-to-clipboard=true

# Use specific context
bfy -x docs-only --copy-to-clipboard=true
```

**Key features:** Respects `.gitignore`, automatic sensitive data scrubbing, includes line numbers, supports custom filtering via `.blobify` configuration, content filters for extracting specific patterns, context listing for easy discovery, cross-platform clipboard support, **context inheritance** for reusable configurations.

**⚠️ Important Notice:** The scrubbing feature is not guaranteed to work; it may not detect some sensitive data. Consider it a best-effort helper only. Always review output before sharing.

## Command Line Options

```
bfy [directory] [options]
```

- `directory` - Directory to scan (optional, defaults to current directory if .blobify file exists)
- `--output-filename <file>` - Output file path (optional, defaults to stdout)
- `-x,` `--context [name]` - Use specific context from .blobify file, or list available contexts if no name provided
- `-f,` `--filter <name:regex>` - Content filter: extract only lines matching regex pattern (can be used multiple times)
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

```bash
# Function and class definitions
bfy . --filter "signatures:^(def|class)\s+" --copy-to-clipboard=true

# Import statements
bfy . --filter "imports:^(import|from)" --copy-to-clipboard=true

# Multiple filters (OR logic)
bfy . --filter "funcs:^def" --filter "imports:^import" --copy-to-clipboard=true

# API endpoints
bfy . --filter "routes:@app\.(get|post|put|delete)" --copy-to-clipboard=true

# Error handling
bfy . --filter "errors:(except|raise|Error)" --copy-to-clipboard=true
```

Filters use `name:regex` format. If you omit the name, the regex becomes the name.

## .blobify Configuration

Create a `.blobify` file in your project directory for custom configurations. When a `.blobify` file exists in your current directory, you can run `bfy` without specifying a directory argument.

### Basic Configuration

```
# Default configuration options
@copy-to-clipboard=true
@show-excluded=false

# Content filters
@filter=signatures:^(def|class)\s+
@filter=imports:^(import|from)

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

[signatures]
# Code structure analysis
@filter=signatures:^(def|class)\s+
@output-line-numbers=false
@show-excluded=false
+*.py
+*.js

[todos]
# Find all TODOs and FIXMEs
@filter=todos:(TODO|FIXME|XXX)
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
@filter=functions:^def

[frontend:default]
# Also inherits from default
+*.js
+*.vue
+*.css

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
- Inheritance order is preserved: parent1 → parent2 → child

**Multiple Inheritance Example:**

```
[nothing]
# Example context that returns nothing - overrides default greedy behavior
@show-excluded=false
-**
@output-index=false

[license]
+LICENSE

[readme]
+README.md

[both:nothing,license,readme]
# Will only include LICENSE and README.md

```

The `complete` context gets:

- **Includes**: `*.py`, `*.md`, `docs/**`, `test_*.py`, `tests/**`, `**`
- **Excludes**: `__pycache__/**`
- **Options**: `copy-to-clipboard=true`, `debug=true`, `output-metadata=false`, `show-excluded=false`

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
#   backend (inherits from default): Server-side code context
#   full (inherits from backend,frontend): Complete codebase
#
# Use with: bfy -x <context-name>
```

### Configuration Syntax

- `@option=value` - Set default configuration option (`@debug=true`, `@copy-to-clipboard=true`, `@output-content=false`, etc.)
- `@filter=name:regex` - Set default content filter
- `+pattern` - Include files (overrides gitignore)
- `-pattern` - Exclude files
- `[context-name]` - Define named contexts
- `[context-name:parent]` - Define context with single inheritance
- `[context-name:parent1,parent2]` - Define context with multiple inheritance
- Supports `*` and `**` wildcards

**Configuration Option Values:**

- Boolean options: `true`, `false`
- Enum options: specific allowed values (e.g., `list-patterns=ignored`)
- Last value wins: if the same option appears multiple times in a context, the final value is used

## Common Use Cases

```bash
# Basic usage
bfy . --copy-to-clipboard=true                              # Copy project to clipboard
bfy -x                                                      # List available contexts
bfy -x docs-only --copy-to-clipboard=true                   # Use docs context

# Context inheritance
bfy -x backend --copy-to-clipboard=true                     # Use backend context (inherits from default)
bfy -x full --copy-to-clipboard=true                        # Use full context (inherits from multiple parents)

# Content filtering
bfy . --filter "sigs:^def" --copy-to-clipboard=true         # Extract function definitions
bfy . --filter "todos:TODO" --copy-to-clipboard=true        # Find all TODOs

# Clean output
bfy . --show-excluded=false --output-metadata=false --copy-to-clipboard=true  # Only included files
bfy . --output-content=false --copy-to-clipboard=true       # Index only

# Save to file
bfy . --output-filename=project-summary.txt                 # Save to file
bfy . --filter "sigs:^def" --output-filename=overview.txt   # Filtered overview
```

## Efficient Token Usage

For large projects, use contexts and filters to reduce AI token consumption:

```bash
# Project overview (minimal tokens)
bfy -x signatures --copy-to-clipboard=true

# Find specific patterns
bfy . --filter "errors:(except|Error)" --show-excluded=false --copy-to-clipboard=true

# Documentation only
bfy -x docs-only --copy-to-clipboard=true

# Backend code only (with inheritance)
bfy -x backend --copy-to-clipboard=true

# Clean summary
bfy . --filter "sigs:^(def|class)" --output-line-numbers=false --show-excluded=false --copy-to-clipboard=true
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
