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

### Windows Installation (Recommended Method)

1. **Download the script** to a tools directory (e.g., `C:\tools\blobify\blobify.py`)

2. **Create a batch wrapper** for easy command-line access:
   - Create a file named `blobify.bat` in `C:\tools\` (or another directory in your PATH)
   - Add this content:
     ```batch
     @echo off
     python "%~dp0blobify\blobify.py" %*
     ```

3. **Add to your PATH** (if `C:\tools` isn't already there):
   - Open System Properties → Advanced → Environment Variables
   - Edit your `PATH` variable and add `C:\tools`
   - Or use PowerShell as Administrator:
     ```powershell
     $env:PATH += ";C:\tools"
     [Environment]::SetEnvironmentVariable("PATH", $env:PATH, "Machine")
     ```

4. **Test the installation**:
   ```cmd
   blobify --help
   ```

### Alternative Windows Methods

**Method 1: Direct Python execution**
```cmd
python C:\tools\blobify\blobify.py [directory] [output]
```

**Method 2: Create standalone executable** (requires pyinstaller):
```cmd
pip install pyinstaller
pyinstaller --onefile blobify.py
```

### Linux/Unix Installation

1. **Download the script** to a local directory:
   ```bash
   mkdir -p ~/bin
   wget -O ~/bin/blobify https://raw.githubusercontent.com/yourusername/blobify/main/blobify.py
   # or download manually to ~/bin/blobify
   ```

2. **Make it executable**:
   ```bash
   chmod +x ~/bin/blobify
   ```

3. **Add to your PATH** (if `~/bin` isn't already there):
   ```bash
   # For bash/zsh - add to ~/.bashrc or ~/.zshrc
   echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
   source ~/.bashrc
   
   # For fish shell - add to ~/.config/fish/config.fish
   echo 'set -gx PATH $HOME/bin $PATH' >> ~/.config/fish/config.fish
   ```

4. **Test the installation**:
   ```bash
   blobify --help
   ```

### macOS Installation

**Method 1: Using Homebrew** (if you have a Homebrew formula):
```bash
brew install blobify
```

**Method 2: Manual installation** (same as Linux):
```bash
# Download to local bin directory
mkdir -p ~/bin
curl -o ~/bin/blobify https://raw.githubusercontent.com/yourusername/blobify/main/blobify.py

# Make executable and add shebang
chmod +x ~/bin/blobify

# Add to PATH (if needed)
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

**Method 3: Using /usr/local/bin** (system-wide):
```bash
# Requires sudo for system-wide installation
sudo curl -o /usr/local/bin/blobify https://raw.githubusercontent.com/yourusername/blobify/main/blobify.py
sudo chmod +x /usr/local/bin/blobify
```

## Usage

### Windows Command Examples

```cmd
# Scan current directory
blobify .

# Scan a project directory
blobify C:\MyProject

# Save output to file
blobify C:\MyProject project_files.txt

# Debug mode to see gitignore processing
blobify C:\MyProject --debug

# Scan and copy to clipboard
blobify . | clip
```

### Linux/Unix/macOS Examples

```bash
# Scan current directory
blobify .

# Scan project directory with output file
blobify /path/to/project project_index.txt

# Debug mode to see gitignore processing
blobify /path/to/project --debug

# Scan and copy to clipboard (Linux with xclip)
blobify . | xclip -selection clipboard

# Scan and copy to clipboard (macOS)
blobify . | pbcopy

# Scan with sudo for restricted directories
sudo blobify /var/log system_logs.txt

# Process output with other tools
blobify . | grep -E "START_FILE.*\.py" | wc -l  # Count Python files
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

## Troubleshooting

### Windows-Specific Issues

**"'blobify' is not recognised as an internal or external command"**
- Ensure `C:\tools` (or your chosen directory) is in your PATH
- Restart your command prompt after adding to PATH
- Check that `blobify.bat` exists in the PATH directory

**"Python not found"**
- Ensure Python is installed and in your PATH
- Try using `py` instead of `python` in the batch file:
  ```batch
  @echo off
  py "%~dp0blobify\blobify.py" %*
  ```

**Unicode/encoding issues**
- The script automatically handles UTF-8 encoding on Windows
- If you see strange characters, ensure your terminal supports UTF-8

### Linux/Unix/macOS Issues

**"blobify: command not found"**
- Ensure the script is executable: `chmod +x ~/bin/blobify`
- Check that `~/bin` is in your PATH: `echo $PATH`
- Restart your terminal after modifying PATH

**"Permission denied"**
- Make sure the script has execute permissions: `ls -la ~/bin/blobify`
- For system directories, you may need `sudo`

**"Python not found" or shebang issues**
- Ensure Python 3 is installed: `python3 --version`
- Check the shebang line points to correct Python: `which python3`
- Alternative shebang options:
  ```python
  #!/usr/bin/python3
  #!/usr/local/bin/python3
  ```

**Git integration not working**
- Ensure Git is installed and in PATH: `git --version`
- Check Git repository status: `git status`

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