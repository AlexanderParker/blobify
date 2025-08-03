#!/usr/bin/env python3

import argparse
import io
import os
import subprocess
import sys
import tempfile
from pathlib import Path

__version__ = "1.0.0"
__author__ = "Alexander Parker"
__email__ = "pypi@parker.im"

from .config import apply_default_switches, list_available_contexts, read_blobify_config
from .console import print_debug, print_error, print_phase, print_status, print_success
from .content_processor import parse_named_filters
from .file_scanner import get_built_in_ignored_patterns, scan_files
from .git_utils import is_git_repository
from .output_formatter import format_output


def validate_boolean(value):
    """Validate and convert boolean string values."""
    if isinstance(value, bool):
        return value
    if value.lower() in ["true", "1", "yes", "on"]:
        return True
    elif value.lower() in ["false", "0", "no", "off"]:
        return False
    else:
        raise argparse.ArgumentTypeError(f"Invalid boolean value: '{value}'. Use 'true' or 'false'.")


def validate_list_patterns(value):
    """Validate list-patterns option values."""
    allowed_values = ["none", "ignored", "contexts"]
    if value not in allowed_values:
        raise argparse.ArgumentTypeError(f"Invalid list-patterns value: '{value}'. Use one of: {', '.join(allowed_values)}")
    return value


def _should_modify_stdout():
    """
    Determine if we should modify sys.stdout for Windows Unicode support.

    Returns False if:
    - Not on Windows
    - Running under pytest
    - stdout is not a terminal (redirected to file/pipe)
    - stdout doesn't have a buffer attribute (already wrapped or captured)
    """
    if sys.platform != "win32":
        return False

    # Check if running under pytest
    if "pytest" in sys.modules or "PYTEST_CURRENT_TEST" in os.environ:
        return False

    # Check if stdout is a real terminal
    if not sys.stdout.isatty():
        return False

    # Check if stdout has a buffer attribute (real file-like object)
    if not hasattr(sys.stdout, "buffer"):
        return False

    return True


def list_ignored_patterns():
    """List the built-in ignored patterns to stdout."""
    patterns = get_built_in_ignored_patterns()

    print("Built-in ignored patterns:")
    print("=" * 30)

    # Group patterns by type for better readability
    dot_folders = [p for p in patterns if p.startswith(".")]
    package_dirs = [p for p in patterns if p in ["node_modules", "bower_components", "vendor", "packages"]]
    python_dirs = [p for p in patterns if p in ["venv", "env", ".env", ".venv", "__pycache__", ".pytest_cache", ".mypy_cache"]]
    build_dirs = [p for p in patterns if p in ["dist", "build", "target", "out", "obj", "Debug"]]
    security_dirs = [p for p in patterns if p in ["certs", "certificates", "keys", "private", "ssl", ".ssh", "tls", ".gpg", ".keyring", ".gnupg"]]
    other_patterns = [p for p in patterns if p not in dot_folders + package_dirs + python_dirs + build_dirs + security_dirs]

    categories = [
        ("Dot folders:", dot_folders),
        ("Package manager directories:", package_dirs),
        ("Python environments & cache:", python_dirs),
        ("Build directories:", build_dirs),
        ("Security & certificate directories:", security_dirs),
        ("Other patterns:", other_patterns),
    ]

    for category_name, category_patterns in categories:
        if category_patterns:
            print(f"\n{category_name}")
            for pattern in sorted(category_patterns):
                print(f"  {pattern}")


def show_version():
    """Print version information and exit."""
    print(f"blobify {__version__}")


def main():
    # Fix Windows Unicode output by replacing stdout with UTF-8 wrapper
    # Only do this when running in a real terminal, not under pytest or when redirected
    original_stdout = None
    if _should_modify_stdout():
        original_stdout = sys.stdout
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="surrogateescape", newline="\n")

    try:
        parser = argparse.ArgumentParser(
            description="Recursively scan directory for text files and create index. Respects .gitignore when in a git repository. "
            "Supports .blobify configuration files for pattern-based overrides and default command-line options. "
            "Attempts to detect and replace sensitive data using scrubadub by default."
        )
        parser.add_argument(
            "directory",
            nargs="?",  # Make directory optional
            default=None,
            help="Directory to scan (defaults to current directory if .blobify file exists)",
        )
        parser.add_argument("--output-filename", help="Output file (optional, defaults to stdout)")
        parser.add_argument(
            "-x",
            "--context",
            nargs="?",  # Make the value optional
            const="__list__",  # Default value when flag is provided without argument
            help="Use specific context from .blobify file, or list available contexts if no name provided",
        )
        parser.add_argument(
            "-v",
            "--version",
            action="store_true",
            help="Show version information and exit",
        )
        parser.add_argument(
            "--debug",
            type=validate_boolean,
            default=False,
            help="Enable debug output for gitignore and .blobify processing (default: false)",
        )
        parser.add_argument(
            "--enable-scrubbing",
            type=validate_boolean,
            default=True,
            help="Enable scrubadub processing of sensitive data (default: true)",
        )
        parser.add_argument(
            "--output-line-numbers",
            type=validate_boolean,
            default=True,
            help="Include line numbers in file content output (default: true)",
        )
        parser.add_argument(
            "--output-index",
            type=validate_boolean,
            default=True,
            help="Include file index section at start of output (default: true)",
        )
        parser.add_argument(
            "--output-content",
            type=validate_boolean,
            default=True,
            help="Include file contents in output (default: true)",
        )
        parser.add_argument(
            "--output-metadata",
            type=validate_boolean,
            default=True,
            help="Include file metadata (size, timestamps, status) in output (default: true)",
        )
        parser.add_argument(
            "--copy-to-clipboard",
            type=validate_boolean,
            default=False,
            help="Copy output to clipboard (default: false)",
        )
        parser.add_argument(
            "--show-excluded",
            type=validate_boolean,
            default=True,
            help="Show excluded files in file contents section (default: true)",
        )
        parser.add_argument(
            "-f",
            "--filter",
            action="append",
            help='Content filter: "name","regex","filepattern" or "name","regex" (can be used multiple times)',
        )
        parser.add_argument(
            "--list-patterns",
            type=validate_list_patterns,
            default="none",
            help="List patterns and exit: 'ignored' shows built-in patterns, 'contexts' shows available contexts (default: none)",
        )
        args = parser.parse_args()

        # Handle version flag first
        if args.version:
            show_version()
            return

        # Handle --list-patterns option
        if args.list_patterns == "ignored":
            list_ignored_patterns()
            return
        elif args.list_patterns == "contexts":
            # Handle case where --list-patterns=contexts was provided
            if args.directory is None:
                # Try to use current directory if .blobify exists
                current_dir = Path.cwd()
                blobify_file = current_dir / ".blobify"
                if blobify_file.exists():
                    list_available_contexts(current_dir)
                else:
                    print("No .blobify file found in current directory.")
                    print("Please specify a directory or run from a directory with a .blobify file.")
            else:
                directory = Path(args.directory)
                if not directory.exists():
                    print_error(f"Directory does not exist: {directory}")
                    sys.exit(1)
                list_available_contexts(directory)
            return

        # Handle --context without value (list contexts)
        if args.context == "__list__":
            # Handle case where --context was provided without a value
            if args.directory is None:
                # Try to use current directory if .blobify exists
                current_dir = Path.cwd()
                blobify_file = current_dir / ".blobify"
                if blobify_file.exists():
                    list_available_contexts(current_dir)
                else:
                    print("No .blobify file found in current directory.")
                    print("Please specify a directory or run from a directory with a .blobify file.")
            else:
                directory = Path(args.directory)
                if not directory.exists():
                    print_error(f"Directory does not exist: {directory}")
                    sys.exit(1)
                list_available_contexts(directory)
            return

        # Handle default directory logic
        if args.directory is None:
            current_dir = Path.cwd()
            blobify_file = current_dir / ".blobify"

            if blobify_file.exists():
                args.directory = "."
                if args.debug:
                    print_debug("No directory specified, but .blobify file found - using current directory")
            else:
                parser.error("directory argument is required when no .blobify file exists in current directory")

        # Check if we're in a git repository and apply default switches from .blobify
        directory = Path(args.directory)
        if not directory.exists():
            print_error(f"Directory does not exist: {directory}")
            sys.exit(1)

        if not directory.is_dir():
            print_error(f"Path is not a directory: {directory}")
            sys.exit(1)
        git_root = is_git_repository(directory)
        if git_root:
            if args.debug:
                print_phase("Default Option Application")
            _, _, default_switches = read_blobify_config(git_root, args.context, args.debug)
            if default_switches:
                if args.debug:
                    context_info = f" for context '{args.context}'" if args.context else " (default context)"
                    print_debug(f"Found {len(default_switches)} default options in .blobify{context_info}")
                args = apply_default_switches(args, default_switches, args.debug)

        # Parse named filters
        filters = {}
        filter_names = []
        if args.filter:
            filters, filter_names = parse_named_filters(args.filter)
            if args.debug:
                print_debug(f"Parsed {len(filters)} content filters: {', '.join(filter_names)}")

        # Check scrubbing configuration
        scrub_data = args.enable_scrubbing
        if args.debug:
            if scrub_data:
                print_debug("scrubadub processing is enabled")
            else:
                print_debug("scrubadub processing is disabled")

        # Scan files
        discovery_context = scan_files(directory, context=args.context, debug=args.debug)

        # Get blobify pattern info for header generation
        blobify_patterns_info = ([], [], [])
        if git_root:
            blobify_patterns_info = read_blobify_config(git_root, args.context, False)

        # Format output
        result, total_substitutions, file_count = format_output(
            discovery_context,
            directory,
            args.context,
            scrub_data,
            include_line_numbers=args.output_line_numbers,
            include_index=args.output_index,
            include_content=args.output_content,
            include_metadata=args.output_metadata,
            suppress_excluded=not args.show_excluded,
            debug=args.debug,
            blobify_patterns_info=blobify_patterns_info,
            filters=filters,
        )

        # Show final summary
        context_info = f" (context: {args.context})" if args.context else ""
        summary_parts = [f"Processed {file_count} files{context_info}"]

        if filters:
            summary_parts.append(f"with {len(filters)} content filters")

        if not args.output_content and not args.output_index and not args.output_metadata:
            summary_parts.append("(no useful output - index, content, and metadata all disabled)")
            # Show helpful hint in CLI when there's essentially no output
            print_status(
                "Note: All output options are disabled (--output-content=false --output-index=false --output-metadata=false). Use --help to see output options.",
                style="yellow",
            )
        elif not args.output_content and not args.output_index:
            summary_parts.append("(metadata only)")
        elif not args.output_content and not args.output_metadata:
            summary_parts.append("(index only)")
        elif not args.output_content:
            summary_parts.append("(index and metadata only)")
        elif not args.output_metadata and not args.output_index:
            summary_parts.append("(content only, no metadata)")
        elif not args.output_metadata:
            summary_parts.append("(index and content, no metadata)")
        elif scrub_data and total_substitutions > 0:
            if args.debug:
                summary_parts.append(f"scrubadub made {total_substitutions} substitutions")
            else:
                summary_parts.append(f"scrubadub made {total_substitutions} substitutions - use --debug=true for details")

        summary_message = ", ".join(summary_parts)
        print_status(summary_message, style="bold blue")

        # Remove BOM if present
        if result.startswith("\ufeff"):
            result = result[1:]

        # Handle output
        if args.output_filename:
            with open(args.output_filename, "w", encoding="utf-8") as f:
                f.write(result)
        elif args.copy_to_clipboard:
            try:
                if sys.platform == "win32":
                    # Simple file-based approach that preserves UTF-8
                    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False, suffix=".txt") as f:
                        f.write(result)
                        temp_file = f.name

                    # Use type command to read file and pipe to clip
                    subprocess.run(f'type "{temp_file}" | clip', shell=True, check=True)

                    # Clean up
                    os.unlink(temp_file)

                elif sys.platform == "darwin":  # macOS
                    proc = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE, text=True, encoding="utf-8")
                    proc.communicate(result)
                else:  # Linux
                    proc = subprocess.Popen(["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE, text=True, encoding="utf-8")
                    proc.communicate(result)

                print_success("Output copied to clipboard")

            except Exception as e:
                print_error(f"Clipboard failed: {e}. Use: blobify . --enable-scrubbing=false --output-filename=file.txt")
                return  # Don't output to stdout if clipboard was requested
        else:
            sys.stdout.write(result)
            sys.stdout.flush()

    except Exception as e:
        print_error(f"Error: {str(e)}")
        sys.exit(1)

    finally:
        # Restore original stdout if we modified it
        if original_stdout is not None:
            sys.stdout = original_stdout


if __name__ == "__main__":
    main()
