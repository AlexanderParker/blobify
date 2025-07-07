# Blobify

A Python utility that packages your entire codebase into a single text file for AI consumption. Feed your project to Claude, ChatGPT, or other AI assistants for code analysis, debugging, refactoring, documentation, or feature development.

## Why Use Blobify?

**Primary use case:** Get AI help with your entire codebase by sharing a single comprehensive file.

**What it does:**
- Scans your project directory recursively
- Combines all text files into one structured document
- Respects `.gitignore` patterns automatically
- Scrubs sensitive data (emails, API keys, etc.) by default
- Includes line numbers for precise AI feedback
- Allows custom file filtering with `.blobify` configuration

**Perfect for:**
- "Help me refactor this entire Flask app"
- "Review my project structure and suggest improvements"
- "Find bugs across my codebase"
- "Generate documentation for this project"
- "Help me add a new feature that touches multiple files"

## Installation

### Install directly from GitHub

```bash
# Basic installation
pip install git+https://github.com/AlexanderParker/blobify.git

# With data scrubbing support
pip install "git+https://github.com/AlexanderParker/blobify.git[scrubbing]"
```

### Install from Source

```bash
# Clone the repository
git clone https://github.com/AlexanderParker/blobify.git
cd blobify

# Install in development mode
pip install -e .

# Or install with scrubbing support
pip install -e .[scrubbing]
```

**Note:** The `scrubbing` extra installs `scrubadub` for automatic sensitive data detection and replacement.

## Basic Usage

```bash
# Scan current directory
blobify .

# Save to file
blobify /path/to/project output.txt

# Disable data scrubbing (keep original content)
blobify . --noclean

# Disable line numbers
blobify . --no-line-numbers

# Debug mode (see processing details)
blobify . --debug
```

### Command Line Arguments

- `directory` - Directory to scan (required)
- `output` - Output file path (optional, defaults to stdout)
- `--noclean` - Disable sensitive data scrubbing
- `--no-line-numbers` - Disable line numbers in output
- `--debug` - Show detailed processing information

## .blobify Configuration

Blobify automatically excludes common directories like `node_modules`, `venv`, `__pycache__`, `.git`, build folders, and files starting with `.` for performance and relevance.

If you find the default exclusions don't go far enough, or exclude files you'd like to include, you may create a `.blobify` file in your git root to customize which files are included:

```
# Include configuration files that might be gitignored
+.pre-commit-config.yaml
+.editorconfig
+.github/**

# Include local development files
+local.settings.json
+.env.local

# Exclude additional files
-*.log
-temp/**
-backup/
```

**Pattern syntax:**
- `+pattern` - Include files matching pattern (overrides gitignore and default exclusions)
- `-pattern` - Exclude files matching pattern
- Use `*` for wildcards, `**` for recursive directories
- Patterns are relative to git root

**Default exclusions:** `.git`, `.svn`, `node_modules`, `venv`, `env`, `__pycache__`, `dist`, `build`, `target`, `.idea`, `.vscode`, and other common build/cache directories.

The tool processes files in this order: default exclusions → gitignore → .blobify excludes → .blobify includes

## Data Scrubbing

Blobify uses the `scrubadub` library to automatically detect and replace sensitive data like emails, names, phone numbers, and API keys with placeholder text (e.g., `{{EMAIL_ADDRESS}}`).

**⚠️ Important Security Notice:**
This is a best-effort attempt at data scrubbing. scrubadub may miss sensitive data or incorrectly identify non-sensitive data. **Always review output before sharing externally.**

To disable scrubbing and preserve original content, use the `--noclean` flag.

## Output Format

The tool generates a structured text file with two sections:

### File Index
```
# FILE INDEX
################################################################################
.pre-commit-config.yaml
src/main.py
config/settings.json [IGNORED BY GITIGNORE]
debug.log [EXCLUDED BY .blobify]
```

### File Contents
```
START_FILE: src/main.py

FILE_METADATA:
  Path: src/main.py
  Size: 1234 bytes
  Created: 2025-01-15T10:30:45.123456
  Modified: 2025-01-15T10:30:45.123456
  Status: PROCESSED WITH SCRUBADUB

FILE_CONTENT:
  1: #!/usr/bin/env python3
  2: import os
  3: 
  4: API_KEY = "{{API_KEY}}"  # Scrubbed sensitive data
  5: 
  6: def main():
  7:     print("Hello World")

END_FILE: src/main.py
```

## Advanced Features

### Git Integration
- Automatically detects git repositories
- Respects all `.gitignore` files and patterns
- Supports global gitignore configuration
- Shows ignored files in index but excludes content

### File Type Detection
- Intelligently identifies text files using extensions, MIME types, and content analysis
- Automatically excludes binary files and security files (certificates, keys, etc.)
- Skips large directories like `node_modules`, `venv`, `__pycache__` for performance

### Line Numbers
Line numbers are included by default to make it easier to reference specific code:
- **With AI tools**: "Check line 42 in config.py"
- **Code reviews**: Easy line-by-line discussions
- **Debugging**: Quickly locate issues

Disable with `--no-line-numbers` if you prefer cleaner output.

## Use Cases

### Getting AI Help with Your Project
```bash
# Package entire codebase for AI analysis
blobify . my-project.txt

# Then paste the contents into Claude/ChatGPT with prompts like:
# "Review this code and suggest improvements"
# "Help me add user authentication to this app"
# "Find potential security issues in this codebase"
```

## License

MIT License - see the project repository for details.