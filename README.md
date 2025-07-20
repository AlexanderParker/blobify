# Blobify

A Python utility that packages your entire codebase into a single text file for AI consumption. Feed your project to Claude, ChatGPT, or other AI assistants for code analysis, debugging, refactoring, documentation, or feature development.

## Why Use Blobify?

**Primary use case:** Get AI help with your entire codebase by sharing a single comprehensive file, e.g.

```bash
# Package entire codebase for AI analysis and copy to clipboard
blobify . --clip

# Or pipe to clipboard manually (may have Unicode issues on Windows)
blobify . | clip

# Then paste the contents into Claude/ChatGPT with prompts like:
# "Review this code and suggest improvements"
# "Add oauth user authentication to this app"
# "Find potential security issues in this codebase"
```

**What it does:**

- Scans your project directory recursively
- Combines all text files into one structured document
- Respects `.gitignore` patterns automatically
- Scrubs sensitive data (emails, API keys, etc.) by default
- Includes line numbers for precise AI feedback
- Allows custom file filtering with `.blobify` configuration
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

**Blobify file Pattern syntax:**

- `+pattern` - Include files matching pattern with `+` (overrides gitignore and default exclusions)
- `-pattern` - Exclude files matching pattern with `-`
- Use `*` for wildcards, `**` for recursive directories
- Patterns are relative to git root, so assumes you are operating in a git repo directory structure.
- Patterns are parsed sequentially

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

## License

MIT License - see the project repository for details.
