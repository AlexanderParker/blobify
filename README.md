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

**⚠️ Important Notice:** The optional scrubbing feature is not guaranteed to work; it may not detect some sensitive data, it may find false positives. Consider it to be a best-effort helper feature only. Scrubbing, if installed, can be disabled with --noclean. You can opt not to install it upfront if you do not use the [scrubbing] option when installing. *This project makes no claims or guarantees of data security - you should always review the output of any tool to check for and clean up sensitive data before you use such data anywhere.*

## Command Line Options

```
bfy [directory] [options]
```

- `directory` - Directory to scan (optional, defaults to current directory if .blobify file exists)
- `-o,`, `--output <file>` - Output file path (optional, defaults to stdout)
- `-x,`, `--context <name>` - Use specific context from .blobify file
- `-d,`, `--debug` - Enable debug output for gitignore and .blobify processing
- `-n,`, `--noclean` - Disable scrubadub processing of sensitive data
- `-l,`, `--no-line-numbers` - Disable line numbers in file content output
- `-i,`, `--no-index` - Disable file index section at start of output
- `-c,`, `--clip` - Copy output to clipboard

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

**For minimum blobify output size** - Exclude both:

```
[minimal]
@no-index
@no-line-numbers
# Minimal tokens for general analysis only
```

You could add these example contexts to .blobify and use with: `bfy -x compact --clip` or `bfy -x minimal --clip`

---

## Development

### Setup

1. Clone the repository
    ```bash
    git clone https://github.com/AlexanderParker/blobify.git
    ```
    Enter the project folder:
    ```bash
    cd blobify
    ```
2. Create a virtual environment:

    ```bash
    python -m venv venv
    ```

2. Activate the virtual environment

    Linux, MacOS:

    ```bash
    source venv/bin/activate
    ```

    Windows:

    ```
    venv\Scripts\activate
    ```

4. Install with dev & scrubbing dependencies:

    ```bash
    pip install -e ".[dev,scrubbing]"
    ```

5. Install pre-commit hooks:
    ```bash
    pre-commit install
    ```

### Run Tests

* Run tests

    With normal CLI output:
    ```bash
    invoke test
    ```

    Redirect to clipboard (test on windows only at this stage)

    ```bash
    invoke test-to-clip
    ```
* Run with coverage

    ```bash
    invoke coverage
    ```
* Format code

    ```bash
    invoke format
    ```
* Check code quality

    ```bash
    invoke lint
    ```

## License

[MIT License](LICENSE) - see the project repository for details.
