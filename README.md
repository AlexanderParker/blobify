Blobify

A cross-platform Python utility for recursively scanning directories and creating comprehensive text file indexes with content extraction. Features intelligent Git integration that respects .gitignore patterns whilst maintaining visibility of ignored files, and best-effort sensitive data detection using scrubadub for safer sharing.
Features

    Comprehensive Directory Scanning: Recursively scans directories for text files
    Git Integration: Automatically detects Git repositories and respects .gitignore patterns
    Smart File Detection: Uses MIME types, file extensions, and content analysis to identify text files
    Complete File Index: Creates indexed listing of all discovered text files
    Content Extraction: Includes full file contents for non-ignored files
    🆕 Sensitive Data Detection: Uses Microsoft's scrubadub library to attempt detection and replacement of passwords, emails, credit cards, names, and other PII
    Metadata Capture: Records file size, creation time, modification time, and access time
    Security-Aware: Automatically excludes security-sensitive files (certificates, keys, etc.)
    Cross-Platform: Works on Windows, macOS, and Linux
    Flexible Output: Supports output to file or stdout
    UTF-8 Support: Handles UTF-8 encoded files with proper encoding detection

⚠️ Important Security Notice

Blobify uses the scrubadub library to attempt detection and replacement of sensitive data. This is a best-effort process and may not catch all sensitive information. Users must manually review all output before sharing to ensure no sensitive data remains.

    scrubadub may miss some sensitive data
    scrubadub may incorrectly flag non-sensitive data
    Always review output before sharing externally
    Use at your own risk - no guarantees of complete data scrubbing

Requirements

    Python 3.6 or higher
    Git (optional, for .gitignore functionality)
    scrubadub (optional but recommended, for sensitive data detection and replacement)

Installation
Step 1: Install Python Dependencies

Install scrubadub for sensitive data detection:

bash

pip install scrubadub

Note: Blobify will work without scrubadub, but will not attempt to detect or replace sensitive data. A warning will be displayed if scrubadub is not available.
Step 2: Install Blobify
Windows Installation (Recommended Method)

    Download the script to a tools directory (e.g., C:\tools\blobify\blobify.py)
    Create a batch wrapper for easy command-line access:
        Create a file named blobify.bat in C:\tools\ (or another directory in your PATH)
        Add this content:

        batch

        @echo off
        python "%~dp0blobify\blobify.py" %*

    Add to your PATH (if C:\tools isn't already there):
        Open System Properties → Advanced → Environment Variables
        Edit your PATH variable and add C:\tools
        Or use PowerShell as Administrator:

        powershell

        $env:PATH += ";C:\tools"
        [Environment]::SetEnvironmentVariable("PATH", $env:PATH, "Machine")

    Test the installation:

    cmd

    blobify --help

Alternative Windows Methods

Method 1: Direct Python execution

cmd

python C:\tools\blobify\blobify.py [directory] [output]

Method 2: Create standalone executable (requires pyinstaller):

cmd

pip install pyinstaller
pyinstaller --onefile blobify.py

Linux/Unix Installation

    Download the script to a local directory:

    bash

    mkdir -p ~/bin
    wget -O ~/bin/blobify https://raw.githubusercontent.com/yourusername/blobify/main/blobify.py
    # or download manually to ~/bin/blobify

    Make it executable:

    bash

    chmod +x ~/bin/blobify

    Add to your PATH (if ~/bin isn't already there):

    bash

    # For bash/zsh - add to ~/.bashrc or ~/.zshrc
    echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
    source ~/.bashrc

    # For fish shell - add to ~/.config/fish/config.fish
    echo 'set -gx PATH $HOME/bin $PATH' >> ~/.config/fish/config.fish

    Test the installation:

    bash

    blobify --help

macOS Installation

Method 1: Using Homebrew (if you have a Homebrew formula):

bash

brew install blobify

Method 2: Manual installation (same as Linux):

bash

# Download to local bin directory

mkdir -p ~/bin
curl -o ~/bin/blobify https://raw.githubusercontent.com/yourusername/blobify/main/blobify.py

# Make executable and add shebang

chmod +x ~/bin/blobify

# Add to PATH (if needed)

echo 'export PATH="$HOME/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

Method 3: Using /usr/local/bin (system-wide):

bash

# Requires sudo for system-wide installation

sudo curl -o /usr/local/bin/blobify https://raw.githubusercontent.com/yourusername/blobify/main/blobify.py
sudo chmod +x /usr/local/bin/blobify

Usage
Basic Usage

bash

# Scan current directory with scrubadub processing (default)

blobify .

# Scan project directory without scrubadub processing

blobify /path/to/project --noclean

# Save output to file

blobify /path/to/project project_files.txt

# Debug mode to see gitignore processing

blobify /path/to/project --debug

Windows Command Examples

cmd

# Scan current directory (scrubadub processing by default)

blobify .

# Scan a project directory without scrubadub processing

blobify C:\MyProject --noclean

# Save output to file with scrubadub processing

blobify C:\MyProject project_files.txt

# Debug mode to see gitignore processing

blobify C:\MyProject --debug

# Scan and copy to clipboard (with scrubadub processing)

blobify . | clip

Linux/Unix/macOS Examples

bash

# Scan current directory (scrubadub processing by default)

blobify .

# Scan project directory with output file, no scrubadub processing

blobify /path/to/project --noclean project_index.txt

# Debug mode to see gitignore processing

blobify /path/to/project --debug

# Scan and copy to clipboard (Linux with xclip)

blobify . | xclip -selection clipboard

# Scan and copy to clipboard (macOS)

blobify . | pbcopy

# Scan with sudo for restricted directories

sudo blobify /var/log system_logs.txt

# Process output with other tools

blobify . | grep -E "START_FILE.\*\.py" | wc -l # Count Python files

Command-line Arguments

blobify.py [-h] [--debug] [--noclean] directory [output]

    directory: The directory to scan (required)
    output: Output file path (optional, defaults to stdout)
    --debug: Enable debug output for Git ignore processing
    --noclean: Disable sensitive data anonymisation (anonymisation is enabled by default)
    -h, --help: Show help message

🆕 Data Anonymisation

Blobify anonymises sensitive data by default to make file dumps safe for sharing, analysis, or debugging.
What Gets Anonymised

    Email addresses: john.doe@company.com → {{EMAIL_ADDRESS}}
    Phone numbers: +1-555-123-4567 → {{PHONE_NUMBER}}
    Names: John Smith → {{PERSON}}
    Credit card numbers: 4111 1111 1111 1111 → {{CREDIT_CARD}}
    URLs with credentials: https://user:pass@api.com → https://{{USERNAME}}:{{PASSWORD}}@api.com
    Social security numbers and other government IDs

Anonymisation Control

bash

# Anonymise sensitive data (default behaviour)

blobify /path/to/project

# Disable anonymisation (preserve original content)

blobify /path/to/project --noclean

# Check if anonymisation is working

blobify /path/to/project | head -20 # Look for anonymisation note in header

Anonymous Output Indicators

The output header will indicate anonymisation status:

# Sensitive data anonymised using scrubadub # ← Anonymisation enabled

# Sensitive data anonymisation DISABLED # ← --noclean used

# Sensitive data anonymisation UNAVAILABLE # ← scrubadub not installed

Individual files will also show status in metadata:

FILE_METADATA:
Path: config.py
Size: 1234 bytes
Created: 2025-06-16T12:34:56.123456
Modified: 2025-06-16T12:34:56.123456
Accessed: 2025-06-16T14:22:10.654321
Status: PROCESSED WITH SCRUBADUB # ← Content processed by scrubadub

Git Integration

When scanning within a Git repository, Blobify automatically:

    Detects Git repositories by searching for .git directories
    Loads gitignore patterns from:
        Global gitignore file (git config core.excludesfile)
        Repository-level .gitignore
        Directory-specific .gitignore files
    Respects all gitignore syntax:
        Wildcards (*, **, ?)
        Negation patterns (!pattern)
        Directory-only patterns (pattern/)
        Root-relative patterns (/pattern)

Output Format

The output is structured in two main sections:

1. File Index

Lists all discovered files with clear marking of ignored files:

# FILE INDEX

################################################################################
globalUsings.cs
host.json
local.settings.json [IGNORED BY GITIGNORE]
Program.cs
project.lock.json [IGNORED BY GITIGNORE]

2. File Contents

Detailed sections for each file with metadata and content:
Regular Files (Processed with scrubadub)

START_FILE: Program.cs

FILE_METADATA:
Path: Program.cs
Size: 1234 bytes
Created: 2025-06-16T12:34:56.123456
Modified: 2025-06-16T12:34:56.123456
Accessed: 2025-06-16T14:22:10.654321
Status: PROCESSED WITH SCRUBADUB

FILE_CONTENT:
using System;

class Program
{
static void Main()
{
var email = "{{EMAIL_ADDRESS}}";
var apiKey = "{{API_KEY}}";
Console.WriteLine($"Contact: {email}");
}
}

END_FILE: Program.cs

Regular Files (Not Processed, --noclean used)

START_FILE: Program.cs

FILE_METADATA:
Path: Program.cs
Size: 1234 bytes
Created: 2025-06-16T12:34:56.123456
Modified: 2025-06-16T12:34:56.123456
Accessed: 2025-06-16T14:22:10.654321

FILE_CONTENT:
[actual file contents here - no scrubbing attempted]

END_FILE: Program.cs

Ignored Files

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

File Type Detection

Blobify intelligently identifies text files using multiple methods:
Supported Text File Extensions

    Source code: .py, .js, .ts, .java, .c, .cpp, .cs, .rb, .php, .go, etc.
    Web files: .html, .css, .xml, .json, .yaml
    Documentation: .md, .txt, .rst, .tex
    Configuration: .ini, .cfg, .conf, .env, .properties
    Data files: .csv, .log, .sql

Automatically Excluded Files

    Binary files: Detected by content analysis and file signatures
    Security files: Certificates (.crt, .pem), keys (.key, .ppk), keystores (.jks, .p12)
    System directories: .git, .svn, node_modules, __pycache__, etc.

Error Handling

    Permission errors: Handled gracefully with informative messages
    Unreadable files: Noted in output with error descriptions
    Git unavailable: Operates normally without Git integration
    scrubadub unavailable: Operates with warning, no anonymisation
    Anonymisation failures: Falls back to original content with warning
    Invalid paths: Clear error messages with exit codes
    Encoding issues: Automatic fallback handling for file encoding

Debug Mode

Use --debug flag to see detailed information about:

    Git repository detection
    Gitignore pattern loading and conversion
    File processing decisions
    Pattern matching details
    Anonymisation status

Example debug output:

# Git repository detected at: C:\Dev\Code\MyProject

# Loaded 147 gitignore patterns

# Sample patterns:

# 'local.settings.json' -> '^(local\.settings\.json|.\*/local\.settings\.json)

# '_.suo' -> '^([^/]_\.suo|._/[^/]_\.suo)

# Ignored 5 files due to gitignore patterns

Security and Privacy Considerations
Data Anonymisation Benefits

    Safe sharing: Anonymised outputs can be shared without exposing sensitive data
    Debugging assistance: Send anonymised code dumps to support teams
    Documentation: Create sanitised examples for documentation
    Code analysis: Use with AI tools without privacy concerns

What Is NOT Anonymised

    File names and paths: Directory structure remains intact
    Code structure: Function names, class names, and logic flow preserved
    Comments: Most code comments remain (unless they contain detected PII)
    Gitignored files: These are excluded entirely, not anonymised

Recommendations

    Review output: Always review anonymised output before sharing externally
    Use --noclean judiciously: Only disable anonymisation when you're certain no sensitive data is present
    Test anonymisation: Run on sample data to understand what gets anonymised
    Combine with gitignore: Ensure sensitive config files are gitignored

Performance Considerations

    Memory usage: Proportional to total text content size
    Anonymisation overhead: Adds ~10-20% processing time for text content
    Large repositories: Git ignore patterns provide significant performance benefits by excluding build artifacts
    Network drives: May be slower due to file system latency
    File system permissions: Inaccessible files are skipped gracefully

Troubleshooting
Anonymisation Issues

"scrubadub not installed" warning

bash

pip install scrubadub

Anonymisation not working as expected

    Check the output header for anonymisation status
    Use --debug to see processing details
    Test with known sensitive data to verify detection

False positives in anonymisation

    scrubadub may over-anonymise some content
    Use --noclean if you need exact original content
    Consider this when sharing anonymised output

Windows-Specific Issues

"'blobify' is not recognised as an internal or external command"

    Ensure C:\tools (or your chosen directory) is in your PATH
    Restart your command prompt after adding to PATH
    Check that blobify.bat exists in the PATH directory

"Python not found"

    Ensure Python is installed and in your PATH
    Try using py instead of python in the batch file:

    batch

    @echo off
    py "%~dp0blobify\blobify.py" %*

Unicode/encoding issues

    The script automatically handles UTF-8 encoding on Windows
    If you see strange characters, ensure your terminal supports UTF-8

Linux/Unix/macOS Issues

"blobify: command not found"

    Ensure the script is executable: chmod +x ~/bin/blobify
    Check that ~/bin is in your PATH: echo $PATH
    Restart your terminal after modifying PATH

"Permission denied"

    Make sure the script has execute permissions: ls -la ~/bin/blobify
    For system directories, you may need sudo

"Python not found" or shebang issues

    Ensure Python 3 is installed: python3 --version
    Check the shebang line points to correct Python: which python3
    Alternative shebang options:

    python

    #!/usr/bin/python3
    #!/usr/local/bin/python3

Git integration not working

    Ensure Git is installed and in PATH: git --version
    Check Git repository status: git status

scrubadub installation issues

    Some systems may need additional dependencies:

    bash

    # On Ubuntu/Debian
    sudo apt-get install python3-dev

    # On CentOS/RHEL
    sudo yum install python3-devel

    # Then install scrubadub
    pip3 install scrubadub

Use Cases
Development and Debugging

bash

# Create anonymised dump for bug reports

blobify /path/to/buggy-project bug-report.txt

# Share code structure without sensitive data

blobify . | mail -s "Code review" teammate@company.com

Documentation and Training

bash

# Create sanitised examples for documentation

blobify /path/to/example-project --noclean examples.txt

# Generate training materials

blobify /learning/projects training-code-dump.txt

Code Analysis and AI Assistance

bash

# Safe input for AI code analysis tools

blobify . | your-ai-analysis-tool

# Create datasets for code analysis (anonymised)

blobify /opensource/projects dataset.txt

Security Auditing

bash

# Audit what would be exposed (with anonymisation)

blobify /production/code security-review.txt

# Check what sensitive data exists (disable anonymisation)

blobify /production/code --noclean internal-audit.txt

Contributing

Feel free to open issues or submit pull requests for:

    Bug fixes and performance improvements
    Additional file type support
    Enhanced Git integration features
    Improved anonymisation patterns
    Documentation improvements
    Cross-platform compatibility enhancements

License

This project is open source and available under the MIT License.
Version History

    v3.0: Added automatic sensitive data anonymisation with scrubadub integration
    v2.0: Added Git integration with .gitignore support
    v1.0: Initial release with basic directory scanning and text file detection

Dependencies

    Python 3.6+: Core requirement
    scrubadub (optional): Sensitive data anonymisation

    bash

    pip install scrubadub

    Git (optional): For .gitignore integration
