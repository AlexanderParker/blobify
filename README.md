# Blobify

A Python utility that packages your entire codebase into a single text file for AI consumption. Feed your project to Claude, ChatGPT, or other AI assistants for code analysis, debugging, refactoring, documentation, or feature development.

## Why Use Blobify?

**Primary use case:** Get AI help with your entire codebase by sharing a single comprehensive file, e.g.

Package entire codebase and copy to clipboard:

```bash
blobify . --clip
```

Or pipe to clipboard manually (may have Unicode issues on Windows)
```bash
blobify . | clip
```

Then paste the contents into Claude/ChatGPT (assuming large enough context window) with prompts like:

- "Review this code and suggest improvements"
- "Add oauth user authentication to this app"
- "Find potential security issues in this codebase"

This is an alternative to agentic coding, and places the entire codebase in the context window.

**What it does:**

- Scans your project directory recursively
- Combines all text files into one structured document
- Respects `.gitignore` patterns automatically
- Scrubs sensitive data (emails, API keys, etc.) by default
- Includes line numbers for precise AI feedback
- Allows custom file filtering with `.blobify` configuration
- Supports contexts for different views of your codebase
- Supports default command-line switches via `.blobify` file
- Built-in clipboard support with proper Unicode handling

## Installation

```bash
# Basic installation
pip install git+https://github.com/AlexanderParker/blobify.git

# With data scrubbing support
pip install "blobify[scrubbing] @ git+https://github.com/AlexanderParker/blobify.git"
```

## Basic Usage

```bash
# Scan current directory
blobify .

# Copy to clipboard (recommended - handles Unicode properly)
blobify . --clip

# Save to file
blobify /path/to/project output.txt

# Use specific context from .blobify file
blobify . --context=docs-only

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
- `-x`, `--context` - Use specific context from .blobify file
- `--clip` - Copy output to clipboard with proper Unicode support
- `--noclean` - Disable sensitive data scrubbing
- `--no-line-numbers` - Disable line numbers in output
- `--debug` - Show detailed processing information

**Default exclusions:** `.git`, `.svn`, `node_modules`, `venv`, `env`, `__pycache__`, `dist`, `build`, `target`, `.idea`, `.vscode`, and other common build/cache directories.

The tool processes files in this order: default exclusions → gitignore → .blobify excludes → .blobify includes

## Clipboard Support

The `--clip` option provides cross-platform clipboard support with proper Unicode handling:

- **Windows**: Uses temp file approach to preserve Unicode characters
- **macOS**: Uses `pbcopy`
- **Linux**: Uses `xclip` (install with `sudo apt install xclip`)

This is much more reliable than piping to `clip` on Windows, which often corrupts Unicode characters like emoji.

## Git Integration

- Automatically detects git repositories
- Respects all `.gitignore` files and patterns
- Shows ignored files in index but excludes content

## File Type Detection

- Attempts to identify text files using extensions, MIME types, and content analysis
- Automatically excludes binary files and security files (certificates, keys, etc.)
- Skips large directories like `node_modules`, `venv`, `__pycache__` for performance
- Specific files and directories can be included / excluded with a .blobify file

## .blobify Configuration

Blobify automatically excludes common directories like `node_modules`, `venv`, `__pycache__`, `.git`, build folders, and files starting with `.` for performance and relevance.

If you find the default exclusions don't go far enough, or exclude files you'd like to include, you may create a `.blobify` file in your git root to customise which files are included:

```
# Default command-line switches (always applied unless overridden)
@debug
@clip

# Include configuration files that might be gitignored
+.pre-commit-config.yaml
+.editorconfig
+.github/**

# Exclude additional files
-*.log
-temp/**

[docs-only]
# Documentation-only context
-**
+*.md
+docs/**
```

### Context System

Contexts allow you to define different "views" of your codebase within a single `.blobify` file. Each context can have its own patterns and default switches.

### Using Contexts

```bash
# Default context (patterns outside any [context] section)
blobify .

# Use documentation-only context
blobify . --context=docs-only

# Use code-only context for development analysis
blobify . -x code-only --clip

# Minimal context for quick AI reviews
blobify . -x minimal
```

### Context Benefits

- **Documentation Reviews**: Use `docs-only` context to focus on README files, documentation, and guides
- **Code Analysis**: Use `code-only` context to exclude tests and configuration for pure code review
- **Security Audits**: Create a `security` context that includes config files and excludes test data
- **Team Onboarding**: Create a `minimal` context showing just the essential files new developers need

### Blobify File Pattern Syntax

- `[context-name]` - Define a new context section (use snake-case or kebab-case names)
- `@switch` - Set default command-line switch (e.g., `@debug`, `@clip`, `@noclean`, `@no-line-numbers`)
- `+pattern` - Include files matching pattern with `+` (overrides gitignore and default exclusions)
- `-pattern` - Exclude files matching pattern with `-`
- Use `*` for wildcards, `**` for recursive directories
- Patterns are relative to git root, so assumes you are operating in a git repo directory structure
- Patterns and switches are parsed sequentially within each context

### Default Switches

The `@` prefix allows you to set default command-line options that will be applied automatically whenever blobify runs from that repository. This is particularly useful for consistent behaviour across team members or CI/CD pipelines.

**Available default switches:**

- `@debug` - Enable debug output
- `@noclean` - Disable sensitive data scrubbing
- `@no-line-numbers` - Disable line numbers in output
- `@clip` - Copy output to clipboard

**Priority:** Command-line arguments override default switches from `.blobify`. This means you can always override project defaults when needed.

## Line Numbers

Line numbers are included by default to make it easier to reference specific code:

- **With AI tools**: "Check line 42 in config.py"
- **Code reviews**: Easy line-by-line discussions
- **Debugging**: Quickly locate issues

Disable with `--no-line-numbers` if you prefer cleaner output.

## Data Scrubbing

Blobify uses the `scrubadub` library to automatically detect and replace sensitive data like emails, names, phone numbers, and API keys with placeholder text (e.g., `{{EMAIL_ADDRESS}}`).

**⚠️ Important Security Notice:**
This is a best-effort attempt at data scrubbing. scrubadub may miss sensitive data or incorrectly identify non-sensitive data. **Always review output before sharing externally.**

To disable scrubbing and preserve original content, use the `--noclean` flag.

## Common Use Cases

### AI Code Review

```bash
# Default: comprehensive analysis with gitignore respected
blobify . --clip
# Paste into AI: "Review this codebase for potential improvements"

# Alternative: code-only view without tests/config
blobify . -x code-only --clip
```

### Documentation Analysis

```bash
# Default: all files including docs
blobify . --clip
# Paste into AI: "Improve the documentation structure and clarity"

# Alternative: focus only on documentation
blobify . -x docs-only --clip
```

### Security Audit

```bash
# Include config files but scrub sensitive data (default behaviour)
blobify . --clip
# Paste into AI: "Identify potential security vulnerabilities"
```

### Quick Project Overview

```bash
# Standard overview respecting gitignore
blobify . --clip
# Paste into AI: "Explain what this project does and how it's structured"
```

## License

MIT License - see the project repository for details.
