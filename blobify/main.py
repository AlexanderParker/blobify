#!/usr/bin/env python3

import argparse
import io
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from .config import apply_default_switches, read_blobify_config
from .console import print_debug, print_error, print_phase, print_status, print_success
from .content_processor import SCRUBADUB_AVAILABLE
from .file_scanner import scan_files
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


def main():
    # Fix Windows Unicode output by replacing stdout with UTF-8 wrapper
    # Only do this when running in a real terminal, not under pytest or when redirected
    original_stdout = None
    if _should_modify_stdout():
        original_stdout = sys.stdout
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="surrogateescape", newline="\n")

    try:
        parser = argparse.ArgumentParser(
            description="Recursively scan directory for text files and create index. Respects .gitignore when in a git repository. Supports .blobify configuration files for pattern-based overrides and default command-line switches. Attempts to detect and replace sensitive data using scrubadub by default."
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
            help="Use specific context from .blobify file (default uses patterns outside any context section)",
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
            "-c",
            "--clip",
            action="store_true",
            help="Copy output to clipboard",
        )
        args = parser.parse_args()

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
            debug=args.debug,
            blobify_patterns_info=blobify_patterns_info,
        )

        # Show final summary
        context_info = f" (context: {args.context})" if args.context else ""
        summary_parts = [f"Processed {file_count} files{context_info}"]

        if scrub_data and SCRUBADUB_AVAILABLE and total_substitutions > 0:
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
