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
blobify . --clip
```

Then paste into AI with prompts like "Review this code and suggest improvements" or "Add oauth authentication to this app".

**Key features:** Respects `.gitignore`, optional sensitive data scrubbing, includes line numbers, supports custom filtering via `.blobify` configuration, cross-platform clipboard support. Automatically excludes common build/cache directories (`.git`, `node_modules`, `__pycache__`, etc.) and binary files.

**⚠️ Security Notice:** If using scrubbing, always review output before sharing externally as scrubbing may miss sensitive data.

## Command Line Options

```
blobify <directory> [output] [options]
```

- `directory` - Directory to scan (required)
- `output` - Output file path (optional, defaults to stdout)
- `-x, --context <n>` - Use specific context from .blobify file
- `--clip` - Copy to clipboard (Windows/macOS/Linux support)
- `--noclean` - Disable sensitive data scrubbing
- `--no-line-numbers` - Disable line numbers in output
- `--no-index` - Disable file index section
- `--debug` - Show detailed processing information

## Examples

Output to stdout:

```bash
blobify .
```

Copy to clipboard:

```bash
blobify . --clip
```

Save to file:

```bash
blobify /path/to/project output.txt
```

Use context (if configured in .blobify):

```bash
blobify . -x docs-only --clip
```

## .blobify Configuration

The `.blobify` file lets you customize which files are included and set default command-line options. Blobify applies filters in this order: default exclusions → gitignore → .blobify excludes → .blobify includes. This means you can override gitignore rules when needed.

Create a `.blobify` file in your git root:

```
# Default switches (applied automatically)
@debug
@clip

# Include files that would normally be excluded
+.pre-commit-config.yaml
+.github/**

# Exclude additional files
-*.log
-temp/**

[docs-only]
# Context for documentation review
# Use with -x docs-only or --context=docs-only
-**
+*.md
+docs/**
```

**Syntax:**

- `@switch` - Set default command-line option (`@debug`, `@clip`, `@noclean`, `@no-line-numbers`, `@no-index`)
- `+pattern` - Include files (overrides gitignore/default exclusions)
- `-pattern` - Exclude files
- `[context-name]` - Define named contexts for different views
- Supports `*` and `**` wildcards, patterns relative to git root

**Contexts:** Use `-x context-name` to apply different file filtering rules. Useful for documentation-only reviews (`docs-only`), code-only analysis (`code-only`), or security audits.

## License

MIT License - see the project repository for details.
