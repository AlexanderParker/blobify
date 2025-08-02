"""Configuration handling for .blobify files."""

import argparse
from pathlib import Path
from typing import List, Optional, Tuple

from .console import print_debug, print_error, print_warning


def read_blobify_config(git_root: Path, context: Optional[str] = None, debug: bool = False) -> Tuple[List[str], List[str], List[str]]:
    """
    Read .blobify configuration file from git root.
    Returns tuple of (include_patterns, exclude_patterns, default_switches).
    If context is provided, uses patterns from that context section instead of defaults.
    """
    blobify_file = git_root / ".blobify"
    include_patterns = []
    exclude_patterns = []
    default_switches = []

    if not blobify_file.exists():
        if debug:
            print_debug("No .blobify file found")
        return include_patterns, exclude_patterns, default_switches

    try:
        with open(blobify_file, "r", encoding="utf-8", errors="ignore") as f:
            current_context = None  # None means default context
            target_context = context  # Context we're looking for
            in_target_section = target_context is None  # Start in target if no context specified

            for line_num, line in enumerate(f, 1):
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith("#"):
                    continue

                # Check for context headers [context-name]
                if line.startswith("[") and line.endswith("]"):
                    current_context = line[1:-1]
                    in_target_section = target_context == current_context
                    if debug:
                        if in_target_section:
                            print_debug(f".blobify line {line_num}: Entering context '{current_context}'")
                        else:
                            print_debug(f".blobify line {line_num}: Skipping context '{current_context}'")
                    continue

                # Only process lines if we're in the target context section
                if not in_target_section:
                    continue

                if line.startswith("@"):
                    # Default switch pattern - can be boolean or key=value
                    switch_line = line[1:].strip()
                    if switch_line:
                        default_switches.append(switch_line)
                        context_info = f" (context: {current_context})" if current_context else " (default)"
                        if debug:
                            print_debug(f".blobify line {line_num}: Default switch '{switch_line}'{context_info}")
                elif line.startswith("+"):
                    # Include pattern
                    pattern = line[1:].strip()
                    if pattern:
                        include_patterns.append(pattern)
                        context_info = f" (context: {current_context})" if current_context else " (default)"
                        if debug:
                            print_debug(f".blobify line {line_num}: Include pattern '{pattern}'{context_info}")
                elif line.startswith("-"):
                    # Exclude pattern
                    pattern = line[1:].strip()
                    if pattern:
                        exclude_patterns.append(pattern)
                        context_info = f" (context: {current_context})" if current_context else " (default)"
                        if debug:
                            print_debug(f".blobify line {line_num}: Exclude pattern '{pattern}'{context_info}")
                else:
                    if debug:
                        print_debug(f".blobify line {line_num}: Ignoring invalid pattern '{line}' (must start with +, -, or @)")

        context_info = f" for context '{context}'" if context else " (default context)"
        if debug:
            print_debug(
                f"Loaded .blobify config{context_info}: {len(include_patterns)} include patterns, "
                f"{len(exclude_patterns)} exclude patterns, {len(default_switches)} default switches"
            )

    except OSError as e:
        if debug:
            print_error(f"Error reading .blobify file: {e}")

    return include_patterns, exclude_patterns, default_switches


def apply_default_switches(args: argparse.Namespace, default_switches: List[str], debug: bool = False) -> argparse.Namespace:
    """
    Apply default switches from .blobify file to command line arguments.
    Command line arguments take precedence over defaults.
    """
    if not default_switches:
        return args

    # Convert args to dict for easier manipulation
    args_dict = vars(args)

    for switch_line in default_switches:
        if debug:
            print_debug(f"Processing default switch: '{switch_line}'")

        # Check if this is a key=value switch or boolean switch
        if "=" in switch_line:
            # Handle key=value switches like "output=filename.txt"
            key, value = switch_line.split("=", 1)
            key = key.strip()
            value = value.strip()

            if key == "output":
                if not args_dict.get("output"):  # Only apply if not set via command line
                    args_dict["output"] = value
                    if debug:
                        print_debug(f"Applied default: --output={value}")
            else:
                if debug:
                    print_warning(f"Unknown key=value switch ignored: '{key}={value}'")
        else:
            # Handle boolean switches
            switch = switch_line.strip()

            if switch == "debug":
                if not args_dict.get("debug", False):
                    args_dict["debug"] = True
                    if debug:
                        print_debug("Applied default: --debug")
            elif switch == "noclean":
                if not args_dict.get("noclean", False):
                    args_dict["noclean"] = True
                    if debug:
                        print_debug("Applied default: --noclean")
            elif switch == "no-line-numbers":
                if not args_dict.get("no_line_numbers", False):
                    args_dict["no_line_numbers"] = True
                    if debug:
                        print_debug("Applied default: --no-line-numbers")
            elif switch == "no-index":
                if not args_dict.get("no_index", False):
                    args_dict["no_index"] = True
                    if debug:
                        print_debug("Applied default: --no-index")
            elif switch == "no-content":
                if not args_dict.get("no_content", False):
                    args_dict["no_content"] = True
                    if debug:
                        print_debug("Applied default: --no-content")
            elif switch == "no-metadata":
                if not args_dict.get("no_metadata", False):
                    args_dict["no_metadata"] = True
                    if debug:
                        print_debug("Applied default: --no-metadata")
            elif switch == "clip":
                if not args_dict.get("clip", False):
                    args_dict["clip"] = True
                    if debug:
                        print_debug("Applied default: --clip")
            else:
                # Handle switches with dashes converted to underscores
                switch_variants = [switch, switch.replace("-", "_"), switch.replace("_", "-")]

                applied = False
                for variant in switch_variants:
                    if variant in args_dict and not args_dict.get(variant, False):
                        args_dict[variant] = True
                        applied = True
                        if debug:
                            print_debug(f"Applied default: --{variant}")
                        break

                if not applied and debug:
                    print_warning(f"Unknown default switch ignored: '{switch}'")

    # Convert back to namespace
    return argparse.Namespace(**args_dict)
