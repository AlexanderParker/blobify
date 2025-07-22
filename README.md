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

**Key features:** Respects `.gitignore`, optional sensitive data scrubbing (see important notice below), includes line numbers, supports custom filtering via `.blobify` configuration, cross-platform clipboard support. Automatically excludes common build/cache directories (`.git`, `node_modules`, `__pycache__`, etc.) and binary files.

**⚠️ Important Notice:** The scrubbing feature is not guaranteed to work at all, it may not detect some sensitive data and it may find false positives; it is a best-effort helper feature only. It can be disabled with --noclean or not installed at all if you do not use the [scrubbing] option when installing. You should review the output of this utility to check for and clean up sensitive data before you use it anywhere.

## Command Line Options

```
blobify <directory> [options]
```

- `directory` - Directory to scan (required)
- `-o, --output <file>` - Output file path (optional, defaults to stdout)
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
blobify /path/to/project -o output.txt
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

Use with: `blobify . -x compact --clip` or `blobify . -x minimal --clip`

## License

[MIT License](LICENSE) - see the project repository for details.
