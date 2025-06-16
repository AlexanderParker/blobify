# Blobify

A cross-platform Python utility for recursively scanning directories and creating comprehensive text file indexes with content extraction.

## Features

- Recursively scans directories for text files
- Creates an indexed listing of all discovered text files
- Extracts and includes full file contents
- Captures file metadata (creation time, modification time, access time, size)
- Cross-platform compatible
- Supports output to file or stdout
- Handles UTF-8 encoded files
- Smart text file detection using MIME types and content analysis

## Requirements

- Python 3.6 or higher

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
python blobify.py /path/to/directory -o output.txt
```

### Command-line Arguments

```
blobify.py [-h] [--output OUTPUT] directory
```

- `directory`: The directory to scan (required)
- `--output`, `-o`: Output file path (optional, defaults to stdout)
- `-h`, `--help`: Show help message

## Output Format

The output is structured in two main sections:

### 1. Index Section
```
INDEX OF TEXT FILES
================================================================================
file1.txt
path/to/file2.txt
another/path/file3.txt
```

### 2. Content Section
```
================================================================================
File: file1.txt
Metadata:
  Size: 1234 bytes
  Created: 2024-01-31T12:34:56
  Modified: 2024-01-31T12:34:56
  Accessed: 2024-01-31T12:34:56

Contents:
[file contents here]
```

## Error Handling

- Unreadable files are noted in the output with an error message
- Binary files are automatically excluded
- Permission errors are handled gracefully
- Invalid paths trigger appropriate error messages

## Examples

1. Scan current directory and view results:
   ```bash
   python blobify.py .
   ```

2. Scan Documents folder and save to text file:
   ```bash
   python blobify.py ~/Documents -o document_index.txt
   ```

3. Scan a project directory:
   ```bash
   python blobify.py /path/to/project -o project_files.txt
   ```

## Limitations

- Only handles text files (binary files are excluded)
- Large directories with many text files may require significant memory
- File timestamps may vary in precision across different operating systems

## Contributing

Feel free to open issues or submit pull requests for:
- Bug fixes
- Feature enhancements
- Documentation improvements
- Performance optimizations

## License

This project is open source and available under the MIT License.