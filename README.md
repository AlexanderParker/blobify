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

Extract only function signatures and return statements:

```bash
bfy . --filter "signatures:^(def|class)\s+" --filter "returns:return" --clip
```

Then paste into AI with prompts like "Review this code and suggest improvements" or "Add oauth authentication to this app".

**Key features:** Respects `.gitignore`, optional sensitive data scrubbing (see important notice below), includes line numbers, supports custom filtering via `.blobify` configuration, **content filters for extracting specific patterns**, cross-platform clipboard support. Automatically excludes common build/cache directories (`.git`, `node_modules`, `__pycache__`, etc.) and binary files. Only includes text files automatically detected by file extension and content analysis.

**⚠️ Important Notice:** The optional scrubbing feature is not guaranteed to work; it may not detect some sensitive data, it may find false positives. Consider it to be a best-effort helper feature only. Scrubbing, if installed, can be disabled with --noclean. You can opt not to install it upfront if you do not use the [scrubbing] option when installing. _This project makes no claims or guarantees of data security - you should always review the output of any tool to check for and clean up sensitive data before you use such data anywhere._

## Command Line Options

```
bfy [directory] [options]
```

- `directory` - Directory to scan (optional, defaults to current directory if .blobify file exists)
- `-o,` `--output <file>` - Output file path (optional, defaults to stdout)
- `-x,` `--context <name>` - Use specific context from .blobify file
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

Content filters allow you to extract only specific patterns from your files, perfect for generating focused summaries for AI analysis.

### Basic Filter Usage

```bash
# Extract function and class definitions
bfy . --filter "signatures:^(def|class)\s+" --clip

# Extract import statements
bfy . --filter "imports:^(import|from)" --clip

# Extract TODO comments
bfy . --filter "todos:(TODO|FIXME|XXX)" --clip

# Multiple filters (OR logic - line included if ANY filter matches)
bfy . --filter "funcs:^def" --filter "classes:^class" --filter "imports:^import" --clip
```

### Filter Format

Filters use the format `name:regex` where:

- `name` - Descriptive name for the filter (shown in output header)
- `regex` - Python regex pattern to match lines

If you omit the name (just provide the regex), the pattern itself becomes the name.

### Advanced Filter Examples

```bash
# Extract API endpoints and routes
bfy . --filter "routes:@app\.(get|post|put|delete)" --filter "endpoints:/api/" --clip

# Extract type annotations and return types
bfy . --filter "types::\s*\w+.*->" --filter "returns:return\s+" --clip

# Extract configuration and constants
bfy . --filter "config:^[A-Z_]+ = " --filter "env:os\.environ" --clip

# Extract error handling
bfy . --filter "errors:(except|raise|Error)" --filter "logging:(log\.|logger)" --clip
```

### Filter Integration with Other Options

```bash
# Clean output with only filtered content
bfy . --filter "sigs:^(def|class)" --suppress-excluded --no-metadata --clip

# Filter with specific context
bfy . --context docs-only --filter "headers:^#+\s" --clip

# Save filtered overview for AI analysis
bfy . --filter "funcs:^def" --filter "imports:^import" --output ai-overview.txt
```

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

Extract only Python signatures and save for AI review:

```bash
bfy . --filter "signatures:^(def|class)\s+" --filter "imports:^(import|from)" -o code-summary.txt
```

Use context (if configured in .blobify):

```bash
bfy . -x docs-only --clip
```

Use context with .blobify defaults:

```bash
bfy -x docs-only --clip
```

Index only (no file contents):

```bash
bfy . --no-content --clip
```

Metadata only (file info with content but no sizes/timestamps):

```bash
bfy . --no-metadata --clip
```

Index only (no metadata or content):

```bash
bfy . --no-content --no-metadata --clip
```

Suppress excluded files from content section:

```bash
bfy . --suppress-excluded --clip
```

Clean output with only included files in content:

```bash
bfy . --suppress-excluded --no-metadata --clip
```

List built-in ignored patterns:

```bash
bfy -g
```

## .blobify Configuration

The `.blobify` file lets you customise which files are included, set default command-line options, and configure content filters. Blobify applies filters in this order: default exclusions → gitignore → .blobify excludes → .blobify includes → content filters. This means you can override gitignore rules when needed.

Create a `.blobify` file in your project directory (git repository or otherwise):

```
# Default switches (applied automatically)
@debug
@clip
@suppress-excluded
@output=blob.txt

# Content filters for extracting specific patterns
@filter=signatures:^(def|class)\s+
@filter=imports:^(import|from)

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

[code-signatures]
# Context for extracting code structure without implementation details
@filter=signatures:^(def|class|function)\s+
@filter=imports:^(import|from|#include)
@filter=exports:^(export|module\.exports)
@suppress-excluded
@no-metadata
+*.py
+*.js
+*.ts
+*.java
+*.cpp
+*.h

[overview]
# Context for project overview with key components
@filter=classes:^(class|interface)\s+
@filter=functions:^(def|function|public|private)\s+
@filter=imports:^(import|from|#include)
@no-line-numbers
+*.py
+*.js
+*.ts
+*.md

[todos]
# Context for finding all TODOs and FIXMEs
@filter=todos:(TODO|FIXME|XXX|HACK|NOTE)
@suppress-excluded
+**

[errors]
# Context for error handling analysis
@filter=errors:(except|catch|throw|raise|Error|Exception)
@filter=logging:(log\.|logger|console\.)
+*.py
+*.js
+*.ts
+*.java
```

**Syntax:**

- `@switch` - Set default boolean option (`@debug`, `@clip`, `@noclean`, `@no-line-numbers`, `@no-index`, `@no-content`, `@no-metadata`, `@suppress-excluded`)
- `@key=value` - Set default option with value (`@output=filename.txt`)
- `@filter=name:regex` - Set default content filter pattern
- `+pattern` - Include files (overrides gitignore/default exclusions)
- `-pattern` - Exclude files
- `[context-name]` - Define named contexts for different views
- Supports `*` and `**` wildcards, patterns relative to project root

**Content Filters in .blobify:**

- Multiple `@filter=` lines add multiple filters (OR logic)
- Filters are applied after file inclusion/exclusion rules
- Files with no matching lines are marked as `[FILE CONTENTS EXCLUDED BY FILTERS]`
- Use `@suppress-excluded` to hide filter-excluded files from content sections

**Contexts:** Use `-x context-name` to apply different file filtering rules and content filters. Contexts are independent - they don't inherit patterns from the default section. Command line arguments take precedence over .blobify default switches. Perfect for different analysis needs:

- `code-signatures` - Extract function/class signatures without implementation
- `overview` - High-level project structure for AI understanding
- `todos` - Find all TODO items across the codebase
- `errors` - Focus on error handling patterns
- `docs-only` - Documentation files only

**Default Directory Behaviour:** When you have a `.blobify` file in your current directory, you can run `bfy` without specifying a directory argument - it will automatically use the current directory. This makes it easy to set up project-specific configurations and run blobify with just `bfy --clip` or `bfy -x context-name`.

**Suppressing Excluded Files:** By default, excluded files (those ignored by .gitignore, excluded by .blobify patterns, or with no filter matches) appear in the file contents section with placeholder messages like "[Content excluded - file ignored by .gitignore]". Use `--suppress-excluded` to remove these files from the contents section entirely while keeping them listed in the index. This creates cleaner output when you only want to see the actual content of included files.

## Efficient Usage

The file index and line numbers significantly improve AI response quality and accuracy, but they also increase token usage. For large projects approaching input limits, you can use filters and contexts to reduce tokens:

**For getting project overview** - Use signatures and imports:

```
[overview]
@filter=signatures:^(def|class|function)\s+
@filter=imports:^(import|from|#include)
@no-line-numbers
@suppress-excluded
```

**For finding specific patterns** - Use targeted filters:

```
[api-analysis]
@filter=routes:@app\.(get|post|put|delete)
@filter=endpoints:/api/
@filter=auth:(login|authenticate|authorize)
@suppress-excluded
```

**For code structure analysis** - Extract definitions only:

```
[structure]
@filter=definitions:^(def|class|function|interface|type)\s+
@filter=exports:^(export|module\.exports)
@no-metadata
@suppress-excluded
```

**For error analysis** - Focus on error handling:

```
[errors]
@filter=errors:(except|catch|throw|raise|Error)
@filter=logging:(log\.|logger|console\.)
@filter=validation:(validate|check|verify)
@suppress-excluded
```

**For minimum token usage** - Exclude index and line numbers:

```
[minimal]
@filter=key-functions:^(def main|function main|public static)
@no-index
@no-line-numbers
@no-metadata
@suppress-excluded
```

**For AI-optimized summaries** - Perfect for pre-commit hooks:

```bash
# Generate AI-friendly project summary
bfy . --filter "sigs:^(def|class)" --filter "imports:^import" --suppress-excluded --output .ai-summary.txt
```

You can add these example contexts to .blobify and use with: `bfy -x overview --clip`, `bfy -x structure --clip`, `bfy -x errors --clip`, or `bfy -x minimal --clip`

## Pre-commit Integration

Perfect for automatically generating AI-readable summaries:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: blobify-summary
        name: Generate AI project summary
        entry: bfy
        language: system
        args: ["-x", "overview", "--output", ".ai-summary.txt"]
        files: "\.(py|js|ts|md)$"
        pass_filenames: false
        always_run: true
```

This automatically updates `.ai-summary.txt` with filtered project content whenever you commit, perfect for feeding to AI assistants.

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

3. Activate the virtual environment

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

- Run tests

  With normal CLI output:

  ```bash
  invoke test
  ```

  Redirect to clipboard (test on windows only at this stage)

  ```bash
  invoke test-to-clip
  ```

  Or:

  ```bash
  invoke test | clip
  ```

- Run with coverage

  ```bash
  invoke coverage
  ```

- Format code

  ```bash
  invoke format
  ```

- Check code quality

  ```bash
  invoke lint
  ```

- Check all

  ```bash
  invoke all
  ```

## License

[MIT License](LICENSE) - see the project repository for details.
