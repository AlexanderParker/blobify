"""Configuration handling for .blobify files."""

import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .console import print_debug, print_error, print_warning


def validate_boolean_value(value: str) -> bool:
    """Validate and convert boolean string values."""
    if value.lower() in ["true", "1", "yes", "on"]:
        return True
    elif value.lower() in ["false", "0", "no", "off"]:
        return False
    else:
        raise ValueError(f"Invalid boolean value: '{value}'. Use 'true' or 'false'.")


def validate_list_patterns_value(value: str) -> str:
    """Validate list-patterns option values."""
    allowed_values = ["none", "ignored", "contexts"]
    if value not in allowed_values:
        raise ValueError(f"Invalid list-patterns value: '{value}'. Use one of: {', '.join(allowed_values)}")
    return value


def read_blobify_config(git_root: Path, context: Optional[str] = None, debug: bool = False) -> Tuple[List[str], List[str], List[str]]:
    """
    Read .blobify configuration file from git root with context inheritance support.
    Returns tuple of (include_patterns, exclude_patterns, default_switches).
    If context is provided, uses patterns from that context section with inheritance.

    Context inheritance syntax: [context-name:parent-context]
    """
    blobify_file = git_root / ".blobify"

    if not blobify_file.exists():
        if debug:
            print_debug("No .blobify file found")
        return [], [], []

    try:
        contexts = _parse_contexts_with_inheritance(blobify_file, debug)

        # Get the target context (default to "default")
        target_context = context if context is not None else "default"

        if target_context in contexts:
            config = contexts[target_context]
            return config["include_patterns"], config["exclude_patterns"], config["default_switches"]
        else:
            if debug and context is not None:
                print_warning(f"Context '{context}' not found")
            return [], [], []

    except OSError as e:
        if debug:
            print_error(f"Error reading .blobify file: {e}")
        return [], [], []


def _parse_contexts_with_inheritance(blobify_file: Path, debug: bool = False) -> Dict[str, Dict]:
    """
    Parse .blobify file and build contexts with inheritance.
    Processes file sequentially, building inherited contexts as we go.
    """
    # Initialize with empty default context
    contexts = {"default": {"include_patterns": [], "exclude_patterns": [], "default_switches": []}}

    current_context = "default"

    with open(blobify_file, "r", encoding="utf-8", errors="ignore") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue

            # Check for context headers [context-name] or [context-name:parent] or [context-name:parent1,parent2]
            if line.startswith("[") and line.endswith("]"):
                context_header = line[1:-1]  # Remove brackets

                if ":" in context_header:
                    context_name, parents_str = context_header.split(":", 1)
                    context_name = context_name.strip()
                    parent_contexts = [p.strip() for p in parents_str.split(",") if p.strip()]
                else:
                    context_name = context_header.strip()
                    parent_contexts = []

                # Error if trying to redefine default context
                if context_name == "default":
                    if debug:
                        print_error(f".blobify line {line_num}: Cannot redefine 'default' context")
                    raise ValueError(f"Line {line_num}: Cannot redefine 'default' context")

                # Error if context already exists
                if context_name in contexts:
                    if debug:
                        print_error(f".blobify line {line_num}: Context '{context_name}' already defined")
                    raise ValueError(f"Line {line_num}: Context '{context_name}' already defined")

                # Create new context
                if parent_contexts:
                    # Check all parents exist
                    missing_parents = [p for p in parent_contexts if p not in contexts]
                    if missing_parents:
                        missing_str = ", ".join(missing_parents)
                        if debug:
                            print_error(f".blobify line {line_num}: Parent context(s) not found: {missing_str}")
                        raise ValueError(f"Line {line_num}: Parent context(s) not found: {missing_str}")

                    # Merge all parent contexts
                    merged_config = {"include_patterns": [], "exclude_patterns": [], "default_switches": []}

                    for parent_context in parent_contexts:
                        parent_config = contexts[parent_context]
                        merged_config["include_patterns"].extend(parent_config["include_patterns"])
                        merged_config["exclude_patterns"].extend(parent_config["exclude_patterns"])
                        merged_config["default_switches"].extend(parent_config["default_switches"])

                    contexts[context_name] = merged_config

                    if debug:
                        parents_str = ", ".join(parent_contexts)
                        print_debug(f".blobify line {line_num}: Created context '{context_name}' inheriting from {parents_str}")
                else:
                    # No parent specified, create empty context
                    contexts[context_name] = {"include_patterns": [], "exclude_patterns": [], "default_switches": []}
                    if debug:
                        print_debug(f".blobify line {line_num}: Created context '{context_name}' with no inheritance")

                current_context = context_name
                continue

            # Process patterns and switches for current context
            current_config = contexts[current_context]

            if line.startswith("@"):
                # Configuration option pattern
                switch_line = line[1:].strip()
                if switch_line:
                    # Check if this is a key=value option or legacy boolean switch
                    if "=" in switch_line:
                        key, value = switch_line.split("=", 1)
                        key = key.strip()
                        value = value.strip()
                        switch_entry = f"{key}={value}"
                    else:
                        # Legacy boolean switch format - treat as key=true
                        key = switch_line
                        switch_entry = f"{key}=true"

                    # Implement "last value wins" - remove any previous entries for this key
                    current_config["default_switches"] = [s for s in current_config["default_switches"] if not s.startswith(f"{key}=")]

                    # Add the new entry
                    current_config["default_switches"].append(switch_entry)

                    if debug:
                        context_info = f" (context: {current_context})"
                        print_debug(f".blobify line {line_num}: Configuration option '{switch_entry}'{context_info}")

            elif line.startswith("+"):
                # Include pattern
                pattern = line[1:].strip()
                if pattern:
                    current_config["include_patterns"].append(pattern)
                    if debug:
                        context_info = f" (context: {current_context})"
                        print_debug(f".blobify line {line_num}: Include pattern '{pattern}'{context_info}")

            elif line.startswith("-"):
                # Exclude pattern
                pattern = line[1:].strip()
                if pattern:
                    current_config["exclude_patterns"].append(pattern)
                    if debug:
                        context_info = f" (context: {current_context})"
                        print_debug(f".blobify line {line_num}: Exclude pattern '{pattern}'{context_info}")
            else:
                if debug:
                    print_debug(f".blobify line {line_num}: Ignoring invalid pattern '{line}' (must start with +, -, or @)")

    if debug:
        for ctx_name, config in contexts.items():
            print_debug(
                f"Final context '{ctx_name}': "
                f"{len(config['include_patterns'])} include, "
                f"{len(config['exclude_patterns'])} exclude, "
                f"{len(config['default_switches'])} options"
            )

    return contexts


def get_available_contexts(git_root: Path, debug: bool = False) -> List[str]:
    """
    Get list of available contexts from .blobify file.
    Returns list of context names found in the file (excluding default).
    """
    blobify_file = git_root / ".blobify"
    contexts = []

    if not blobify_file.exists():
        return contexts

    try:
        with open(blobify_file, "r", encoding="utf-8", errors="ignore") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith("#"):
                    continue

                # Check for context headers [context-name] or [context-name:parent] or [context-name:parent1,parent2]
                if line.startswith("[") and line.endswith("]"):
                    context_header = line[1:-1]  # Remove brackets
                    if ":" in context_header:
                        context_name = context_header.split(":", 1)[0].strip()
                    else:
                        context_name = context_header.strip()

                    if context_name and context_name not in contexts:
                        contexts.append(context_name)
                        if debug:
                            print_debug(f".blobify line {line_num}: Found context '{context_name}'")

    except OSError as e:
        if debug:
            print_error(f"Error reading .blobify file: {e}")

    return contexts


def get_context_descriptions(git_root: Path) -> Dict[str, str]:
    """
    Extract context descriptions from comments in .blobify file.
    Returns dict mapping context names to their descriptions.
    """
    blobify_file = git_root / ".blobify"
    descriptions = {}

    if not blobify_file.exists():
        return descriptions

    try:
        with open(blobify_file, "r", encoding="utf-8", errors="ignore") as f:
            current_context = None
            pending_comments = []

            for line in f:
                line = line.strip()

                if not line:
                    pending_comments.clear()
                    continue

                # Collect comments that might describe the next context
                if line.startswith("#"):
                    comment_text = line[1:].strip()
                    if comment_text:  # Skip empty comments
                        pending_comments.append(comment_text)
                    continue

                # Check for context headers [context-name] or [context-name:parent] or [context-name:parent1,parent2]
                if line.startswith("[") and line.endswith("]"):
                    context_header = line[1:-1]  # Remove brackets
                    if ":" in context_header:
                        current_context = context_header.split(":", 1)[0].strip()
                    else:
                        current_context = context_header.strip()

                    if current_context and pending_comments:
                        # Use the last meaningful comment as description
                        descriptions[current_context] = pending_comments[-1]
                    pending_comments.clear()
                    continue

                # Clear pending comments when we hit patterns/switches
                if line.startswith(("+", "-", "@")):
                    pending_comments.clear()

    except OSError:
        pass

    return descriptions


def list_available_contexts(directory: Path):
    """List available contexts from .blobify file and exit."""
    from .git_utils import is_git_repository

    git_root = is_git_repository(directory)
    if not git_root:
        print("No git repository found - contexts require a .blobify file in a git repository.")
        return

    contexts = get_available_contexts(git_root)

    if not contexts:
        print("No contexts found in .blobify file.")
        print("\nTo create contexts, add sections like this to your .blobify file:")
        print("")
        print("[docs-only]")
        print("# Context for documentation files only")
        print("-**")
        print("+*.md")
        print("+docs/**")
        print("")
        print("[signatures]")
        print("# Context for extracting function signatures")
        print("@filter=signatures:^(def|class)\\s+")
        print("@output-line-numbers=false")
        print("+*.py")
        print("")
        print("Context inheritance:")
        print("[base]")
        print("@copy-to-clipboard=true")
        print("+*.py")
        print("")
        print("[extended:base]")
        print("# Inherits @copy-to-clipboard=true and +*.py from base")
        print("+*.md")
        print("")
        print("Multiple inheritance:")
        print("[combined:base,docs]")
        print("# Inherits from both base and docs contexts")
        print("+*.txt")
        return

    print("Available contexts:")
    print("=" * 20)

    # Try to read context descriptions and inheritance info
    context_descriptions = get_context_descriptions(git_root)
    context_inheritance = _get_context_inheritance_info(git_root)

    for context in sorted(contexts):
        description = context_descriptions.get(context, "")
        inheritance = context_inheritance.get(context, "")

        output_parts = [f"  {context}"]
        if inheritance:
            output_parts.append(f" (inherits from {inheritance})")
        if description:
            output_parts.append(f": {description}")

        print("".join(output_parts))

    print("\nUse with: bfy -x <context-name> or bfy --context=<context-name>")


def _get_context_inheritance_info(git_root: Path) -> Dict[str, str]:
    """Get inheritance information for contexts for display purposes."""
    blobify_file = git_root / ".blobify"
    inheritance_info = {}

    if not blobify_file.exists():
        return inheritance_info

    try:
        with open(blobify_file, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if line.startswith("[") and line.endswith("]"):
                    context_header = line[1:-1]
                    if ":" in context_header:
                        context_name, parents_str = context_header.split(":", 1)
                        inheritance_info[context_name.strip()] = parents_str.strip()
    except OSError:
        pass

    return inheritance_info


def apply_default_switches(args: argparse.Namespace, default_switches: List[str], debug: bool = False) -> argparse.Namespace:
    """
    Apply default configuration options from .blobify file to command line arguments.
    Command line arguments take precedence over defaults.
    """
    if not default_switches:
        return args

    # Convert args to dict for easier manipulation
    args_dict = vars(args)

    for switch_line in default_switches:
        if debug:
            print_debug(f"Processing default option: '{switch_line}'")

        # Parse the option
        if "=" in switch_line:
            key, value = switch_line.split("=", 1)
            key = key.strip()
            value = value.strip()
        else:
            # Legacy format support - treat as boolean=true
            key = switch_line.strip()
            value = "true"

        # Convert key to argument name (handle dashes/underscores)
        arg_name = key.replace("-", "_")

        # Only apply if not already set by command line (check for default values)
        if arg_name in args_dict:
            current_value = args_dict[arg_name]

            # Determine if this is the default value based on the argument type
            is_default_value = False
            if isinstance(current_value, bool):
                # For boolean options, check against expected defaults
                expected_defaults = {
                    "debug": False,
                    "enable_scrubbing": True,
                    "output_line_numbers": True,
                    "output_index": True,
                    "output_content": True,
                    "output_metadata": True,
                    "copy_to_clipboard": False,
                    "show_excluded": True,
                }
                is_default_value = current_value == expected_defaults.get(arg_name, current_value)
            elif current_value == "none":  # list_patterns default
                is_default_value = True
            elif current_value is None:  # output_filename, filter, context defaults
                is_default_value = True
            elif isinstance(current_value, list) and not current_value:  # empty filter list
                is_default_value = True

            if is_default_value:
                try:
                    if key == "filter":
                        # Handle filter options - can have multiple filters
                        if not args_dict.get("filter"):
                            args_dict["filter"] = []
                        args_dict["filter"].append(value)
                        if debug:
                            print_debug(f"Applied default: --{key}={value}")
                    elif key in ["output-filename", "output_filename"]:
                        # Handle output filename
                        args_dict["output_filename"] = value
                        if debug:
                            print_debug(f"Applied default: --output-filename={value}")
                    elif key == "list-patterns" or key == "list_patterns":
                        # Handle list-patterns option
                        validated_value = validate_list_patterns_value(value)
                        args_dict["list_patterns"] = validated_value
                        if debug:
                            print_debug(f"Applied default: --list-patterns={validated_value}")
                    else:
                        # Handle boolean options
                        validated_value = validate_boolean_value(value)
                        args_dict[arg_name] = validated_value
                        if debug:
                            print_debug(f"Applied default: --{key}={validated_value}")
                except ValueError as e:
                    if debug:
                        print_warning(f"Invalid default option value ignored: '{key}={value}' - {e}")
            else:
                if debug:
                    print_debug(f"Skipping default option '{key}={value}' - command line value takes precedence")
        else:
            if debug:
                print_warning(f"Unknown default option ignored: '{key}={value}'")

    # Convert back to namespace
    return argparse.Namespace(**args_dict)
