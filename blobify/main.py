#!/usr/bin/env python3

import argparse
import io
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from .config import apply_default_switches, list_available_contexts, read_blobify_config
from .console import print_debug, print_error, print_phase, print_status, print_success
from .content_processor import SCRUBADUB_AVAILABLE, parse_named_filters
from .file_scanner import get_built_in_ignored_patterns, scan_files
from .git_utils import is_git_repository
from .output_formatter import format_output


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
            "Supports .blobify configuration files for pattern-based overrides and default command-line switches. "
            "Attempts to detect and replace sensitive data using scrubadub by default."
        )
        parser.add_argument(
            "directory",
            nargs="?",  # Make directory optional
            default=None,
            help="Directory to scan (defaults to current directory if .blobify file exists)",
        )
        parser.add_argument("-o", "--output", help="Output file (optional, defaults to stdout)")
        parser.add_argument(
            "-x",
            "--context",
            nargs="?",  # Make the value optional
            const="__list__",  # Default value when flag is provided without argument
            help="Use specific context from .blobify file, or list available contexts if no name provided",
        )
        parser.add_argument(
            "-d",
            "--debug",
            action="store_true",
            help="Enable debug output for gitignore and .blobify processing",
        )
        parser.add_argument(
            "-n",
            "--noclean",
            action="store_true",
            help="Disable scrubadub processing of sensitive data (emails, names, etc.)",
        )
        parser.add_argument(
            "-l",
            "--no-line-numbers",
            action="store_true",
            help="Disable line numbers in file content output",
        )
        parser.add_argument(
            "-i",
            "--no-index",
            action="store_true",
            help="Disable file index section at start of output",
        )
        parser.add_argument(
            "-k",
            "--no-content",
            action="store_true",
            help="Exclude file contents but include metadata (size, timestamps, status)",
        )
        parser.add_argument(
            "-m",
            "--no-metadata",
            action="store_true",
            help="Exclude file metadata (size, timestamps, status) from output",
        )
        parser.add_argument(
            "-c",
            "--clip",
            action="store_true",
            help="Copy output to clipboard",
        )
        parser.add_argument(
            "-s",
            "--suppress-excluded",
            action="store_true",
            help="Suppress excluded files from file contents section (keep them in index only)",
        )
        parser.add_argument(
            "-f",
            "--filter",
            action="append",
            help="Content filter: name:regex pattern (can be used multiple times)",
        )
        parser.add_argument(
            "-g",
            "--list-ignored",
            action="store_true",
            help="List built-in ignored patterns and exit",
        )
        args = parser.parse_args()

        # Handle --list-ignored option
        if args.list_ignored:
            list_ignored_patterns()
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
                print_phase("Default Switch Application")
            _, _, default_switches = read_blobify_config(git_root, args.context, args.debug)
            if default_switches:
                if args.debug:
                    context_info = f" for context '{args.context}'" if args.context else " (default context)"
                    print_debug(f"Found {len(default_switches)} default switches in .blobify{context_info}")
                args = apply_default_switches(args, default_switches, args.debug)

        # Parse named filters
        filters = {}
        filter_names = []
        if args.filter:
            filters, filter_names = parse_named_filters(args.filter)
            if args.debug:
                print_debug(f"Parsed {len(filters)} content filters: {', '.join(filter_names)}")

        # Check scrubadub availability
        scrub_data = not args.noclean
        if scrub_data and not SCRUBADUB_AVAILABLE:
            if args.debug:
                print_debug("scrubadub not installed - sensitive data will NOT be processed")
            scrub_data = False

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
            include_line_numbers=not args.no_line_numbers,
            include_index=not args.no_index,
            include_content=not args.no_content,
            include_metadata=not args.no_metadata,
            suppress_excluded=args.suppress_excluded,
            debug=args.debug,
            blobify_patterns_info=blobify_patterns_info,
            filters=filters,
        )

        # Show final summary
        context_info = f" (context: {args.context})" if args.context else ""
        summary_parts = [f"Processed {file_count} files{context_info}"]

        if filters:
            summary_parts.append(f"with {len(filters)} content filters")

        if args.no_content and args.no_index and args.no_metadata:
            summary_parts.append("(no useful output - index, content, and metadata all disabled)")
            # Show helpful hint in CLI when there's essentially no output
            print_status(
                "Note: All output options are disabled (--no-index --no-content --no-metadata). Use --help to see output options.",
                style="yellow",
            )
        elif args.no_content and args.no_index:
            summary_parts.append("(metadata only)")
        elif args.no_content and args.no_metadata:
            summary_parts.append("(index only)")
        elif args.no_content:
            summary_parts.append("(index and metadata only)")
        elif args.no_metadata and args.no_index:
            summary_parts.append("(content only, no metadata)")
        elif args.no_metadata:
            summary_parts.append("(index and content, no metadata)")
        elif scrub_data and SCRUBADUB_AVAILABLE and total_substitutions > 0:
            if args.debug:
                summary_parts.append(f"scrubadub made {total_substitutions} substitutions")
            else:
                summary_parts.append(f"scrubadub made {total_substitutions} substitutions - use --debug for details")

        summary_message = ", ".join(summary_parts)
        print_status(summary_message, style="bold blue")

        # Remove BOM if present
        if result.startswith("\ufeff"):
            result = result[1:]

        # Handle output
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(result)
        elif args.clip:
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
                print_error(f"Clipboard failed: {e}. Use: blobify . --noclean > file.txt")
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
