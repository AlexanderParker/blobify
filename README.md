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

Install (basic):

```bash
pip install git+https://github.com/AlexanderParker/blobify.git
```

Install (with sensitive data scrubbing):

```bash
pip install "blobify[scrubbing] @ git+https://github.com/AlexanderParker/blobify.git"
```

Basic usage:

```bash
# Package current directory to clipboard
bfy . --clip

# Or run without directory if .blobify exists
bfy --clip

# List available contexts from .blobify file
bfy -x

# Extract only function signatures
bfy . --filter "signatures:^(def|class)\s+" --clip

# Use specific context
bfy -x docs-only --clip
```

**Key features:** Respects `.gitignore`, optional sensitive data scrubbing, includes line numbers, supports custom filtering via `.blobify` configuration, content filters for extracting specific patterns, context listing for easy discovery, cross-platform clipboard support.

**⚠️ Important Notice:** The optional scrubbing feature is not guaranteed to work; it may not detect some sensitive data. Consider it a best-effort helper only. Always review output before sharing.

## Command Line Options

```
bfy [directory] [options]
```

- `directory` - Directory to scan (optional, defaults to current directory if .blobify file exists)
- `-o,` `--output <file>` - Output file path (optional, defaults to stdout)
- `-x,` `--context [name]` - Use specific context from .blobify file, or list available contexts if no name provided
- `-f,` `--filter <name:regex>` - Content filter: extract only lines matching regex pattern (can be used multiple times)
- `-d,` `--debug` - Enable debug output for gitignore and .blobify processing
- `-n,` `--noclean` - Disable scrubadub processing of sensitive data
- `-l,` `--no-line-numbers` - Disable line numbers in file content output
- `-i,` `--no-index` - Disable file index section at start of output
- `-k,` `--no-content` - Exclude file contents but include metadata (size, timestamps, status)
- `-m,` `--no-metadata` - Exclude file metadata (size, timestamps, status) from output
- `-s,` `--suppress-excluded` - Suppress excluded files from file contents section (keep them in index only)
- `-c,` `--clip` - Copy output to clipboard
- `-g,` `--list-ignored` - List built-in ignored patterns and exit

## Content Filters

Extract specific patterns from your files for focused AI analysis:

```bash
# Function and class definitions
bfy . --filter "signatures:^(def|class)\s+" --clip

# Import statements
bfy . --filter "imports:^(import|from)" --clip

# Multiple filters (OR logic)
bfy . --filter "funcs:^def" --filter "imports:^import" --clip

# API endpoints
bfy . --filter "routes:@app\.(get|post|put|delete)" --clip

# Error handling
bfy . --filter "errors:(except|raise|Error)" --clip
```

Filters use `name:regex` format. If you omit the name, the regex becomes the name.

## .blobify Configuration

Create a `.blobify` file in your project directory for custom configurations. When a `.blobify` file exists in your current directory, you can run `bfy` without specifying a directory argument.

```
# Default switches
@clip
@suppress-excluded

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
@no-line-numbers
@suppress-excluded
+*.py
+*.js

[todos]
# Find all TODOs and FIXMEs
@filter=todos:(TODO|FIXME|XXX)
@suppress-excluded
+**
```

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
#   signatures: Code structure analysis
#   todos: Find all TODOs and FIXMEs
#
# Use with: bfy -x <context-name>
```

### Configuration Syntax

- `@switch` - Set default boolean option (`@debug`, `@clip`, `@no-content`, etc.)
- `@key=value` - Set default option with value (`@output=file.txt`)
- `@filter=name:regex` - Set default content filter
- `+pattern` - Include files (overrides gitignore)
- `-pattern` - Exclude files
- `[context-name]` - Define named contexts
- Supports `*` and `**` wildcards

## Common Use Cases

```bash
# Basic usage
bfy . --clip                              # Copy project to clipboard
bfy -x                                    # List available contexts
bfy -x docs-only --clip                   # Use docs context

# Content filtering
bfy . --filter "sigs:^def" --clip         # Extract function definitions
bfy . --filter "todos:TODO" --clip        # Find all TODOs

# Clean output
bfy . --suppress-excluded --no-metadata --clip  # Only included files
bfy . --no-content --clip                 # Index only

# Save to file
bfy . -o project-summary.txt              # Save to file
bfy . --filter "sigs:^def" -o overview.txt # Filtered overview
```

## Efficient Token Usage

For large projects, use contexts and filters to reduce AI token consumption:

```bash
# Project overview (minimal tokens)
bfy -x signatures --clip

# Find specific patterns
bfy . --filter "errors:(except|Error)" --suppress-excluded --clip

# Documentation only
bfy -x docs-only --clip

# Clean summary
bfy . --filter "sigs:^(def|class)" --no-line-numbers --suppress-excluded --clip
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
   pip install -e ".[dev,scrubbing]"
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
