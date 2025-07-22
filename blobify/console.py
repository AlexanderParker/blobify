"""Console output and styling utilities."""

import sys
from typing import Optional

try:
    from rich.console import Console
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# Initialize console for rich output
if RICH_AVAILABLE and sys.stderr.isatty():
    console = Console(stderr=True, force_terminal=True)
else:
    console = None


def print_status(message: str, style: Optional[str] = None):
    """Print status message with optional rich styling, fallback to plain print."""
    if console:
        console.print(message, style=style)
    else:
        print(message, file=sys.stderr)


def print_debug(message: str):
    """Print debug message with debug styling."""
    if console:
        console.print(message, style="dim cyan")
    else:
        print(message, file=sys.stderr)


def print_phase(phase_name: str):
    """Print phase header with distinct styling."""
    if console:
        console.print(f"\n[bold magenta]──── {phase_name.upper()} ────[/bold magenta]")
    else:
        print(f"\n=== {phase_name.upper()} ===", file=sys.stderr)


def print_warning(message: str):
    """Print warning message with warning styling."""
    if console:
        console.print(message, style="yellow")
    else:
        print(message, file=sys.stderr)


def print_error(message: str):
    """Print error message with error styling."""
    if console:
        console.print(message, style="bold red")
    else:
        print(message, file=sys.stderr)


def print_success(message: str):
    """Print success message with success styling."""
    if console:
        console.print(message, style="green")
    else:
        print(message, file=sys.stderr)


def print_file_processing(message: str):
    """Print file processing message with distinct styling."""
    if console:
        console.print(message, style="bold yellow")
    else:
        print(message, file=sys.stderr)