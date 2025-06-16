# Blobify

A cross-platform Python utility for recursively scanning directories and creating comprehensive text file indexes with content extraction. Features intelligent Git integration that respects `.gitignore` patterns whilst maintaining visibility of ignored files.

## Features

- **Comprehensive Directory Scanning**: Recursively scans directories for text files
- **Git Integration**: Automatically detects Git repositories and respects `.gitignore` patterns
- **Smart File Detection**: Uses MIME types, file extensions, and content analysis to identify text files
- **Complete File Index**: Creates indexed listing of all discovered text files
- **Content Extraction**: Includes full file contents for non-ignored files
- **Metadata Capture**: Records file size, creation time, modification time, and access time
- **Security-Aware**: Automatically excludes security-sensitive files (certificates, keys, etc.)
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Flexible Output**: Supports output to file or stdout
- **UTF-8 Support**: Handles UTF-8 encoded files with proper encoding detection

## Requirements

- Python 3.6 or higher
- Git (optional, for `.gitignore` functionality)

## Installation

1. Clone or download the script
2. Ensure it's executable (Unix-like systems):
   ```bash
   chmod +x blobify.py
   ```

## Usage

### Basic Usage

To scan a directory and output to stdout:
```bash
python blobify.py /path/to/directory
```

To scan a directory and save to a file:
```bash
python blobify.py /path/to/directory output.txt
```

### Command-line Arguments

```
blobify.py [-h] [--debug] directory [output]
```

- `directory`: The directory to scan (required)
- `output`: Output file path (optional, defaults to stdout)
- `--debug`: Enable debug output for Git ignore processing
- `-h`, `--help`: Show help message

### Git Integration

When scanning within a Git repository, Blobify automatically:

- **Detects Git repositories** by searching for `.git` directories
- **Loads gitignore patterns** from:
  - Global gitignore file (`git config core.excludesfile`)
  - Repository-level `.gitignore`
  - Directory-specific `.gitignore` files
- **Respects all gitignore syntax**:
  - Wildcards (`*`, `**`, `?`)
  - Negation patterns (`!pattern`)
  - Directory-only patterns (`pattern/`)
  - Root-relative patterns (`/pattern`)

## Output Format

The output is structured in two main sections:

### 1. File Index
Lists all discovered files with clear marking of ignored files:
```
# FILE INDEX
################################################################################
globalUsings.cs
host.json
local.settings.json [IGNORED BY GITIGNORE]
Program.cs
project.lock.json [IGNORED BY GITIGNORE]
```

### 2. File Contents
Detailed sections for each file with metadata and content:

#### Regular Files
```
START_FILE: Program.cs

FILE_METADATA:
  Path: Program.cs
  Size: 1234 bytes
  Created: 2025-06-16T12:34:56.123456
  Modified: 2025-06-16T12:34:56.123456
  Accessed: 2025-06-16T14:22:10.654321

FILE_CONTENT:
[actual file contents here]

END_FILE: Program.cs
```

#### Ignored Files
```
START_FILE: local.settings.json

FILE_METADATA:
  Path: local.settings.json
  Size: 156 bytes
  Created: 2025-06-16T10:30:45.123456
  Modified: 2025-06-16T10:30:45.123456
  Accessed: 2025-06-16T14:22:10.654321
  Status: IGNORED BY GITIGNORE

FILE_CONTENT:
[Content excluded - file ignored by .gitignore]

END_FILE: local.settings.json
```

## File Type Detection

Blobify intelligently identifies text files using multiple methods:

### Supported Text File Extensions
- Source code: `.py`, `.js`, `.ts`, `.java`, `.c`, `.cpp`, `.cs`, `.rb`, `.php`, `.go`, etc.
- Web files: `.html`, `.css`, `.xml`, `.json`, `.yaml`
- Documentation: `.md`, `.txt`, `.rst`, `.tex`
- Configuration: `.ini`, `.cfg`, `.conf`, `.env`, `.properties`
- Data files: `.csv`, `.log`, `.sql`

### Automatically Excluded Files
- **Binary files**: Detected by content analysis and file signatures
- **Security files**: Certificates (`.crt`, `.pem`), keys (`.key`, `.ppk`), keystores (`.jks`, `.p12`)
- **System directories**: `.git`, `.svn`, `node_modules`, `__pycache__`, etc.

## Error Handling

- **Permission errors**: Handled gracefully with informative messages
- **Unreadable files**: Noted in output with error descriptions
- **Git unavailable**: Operates normally without Git integration
- **Invalid paths**: Clear error messages with exit codes
- **Encoding issues**: Automatic fallback handling for file encoding

## Examples

### Basic Scanning
```bash
# Scan current directory
python blobify.py .

# Scan project directory with output file
python blobify.py /path/to/project project_index.txt
```

### Git-Aware Scanning
```bash
# Scan Git repository (respects .gitignore)
python blobify.py /path/to/git/repo

# Debug mode to see gitignore processing
python blobify.py /path/to/git/repo --debug
```

### Practical Use Cases
```bash
# Copy project structure to clipboard (Windows)
python blobify.py . | clip

# Create documentation of codebase
python blobify.py ./src codebase_documentation.txt

# Analyse project with sensitive files excluded
python blobify.py . --debug > analysis.txt 2> debug.log
```

## Debug Mode

Use `--debug` flag to see detailed information about:
- Git repository detection
- Gitignore pattern loading and conversion
- File processing decisions
- Pattern matching details

Example debug output:
```
# Git repository detected at: C:\Dev\Code\MyProject
# Loaded 147 gitignore patterns
# Sample patterns:
#   'local.settings.json' -> '^(local\.settings\.json|.*/local\.settings\.json)$'
#   '*.suo' -> '^([^/]*\.suo|.*/[^/]*\.suo)$'
# Ignored 5 files due to gitignore patterns
```

## Performance Considerations

- **Memory usage**: Proportional to total text content size
- **Large repositories**: Git ignore patterns provide significant performance benefits by excluding build artifacts
- **Network drives**: May be slower due to file system latency
- **File system permissions**: Inaccessible files are skipped gracefully

## Contributing

Feel free to open issues or submit pull requests for:
- Bug fixes and performance improvements
- Additional file type support
- Enhanced Git integration features
- Documentation improvements
- Cross-platform compatibility enhancements

## License

This project is open source and available under the MIT License.

## Version History

- **v2.0**: Added Git integration with `.gitignore` support
- **v1.0**: Initial release with basic directory scanning and text file detection