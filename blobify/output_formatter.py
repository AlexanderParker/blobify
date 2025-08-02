"""Output formatting and generation utilities."""

import datetime
from pathlib import Path
from typing import Dict, List

from .console import print_debug, print_file_processing
from .content_processor import SCRUBADUB_AVAILABLE, get_file_metadata, scrub_content


def generate_header(
    directory: Path,
    git_root: Path,
    context: str,
    scrub_data: bool,
    blobify_patterns_info: tuple,
    include_index: bool = True,
    include_content: bool = True,
    include_metadata: bool = True,
) -> str:
    """Generate the file header with metadata and configuration info."""
    blobify_include_patterns, blobify_exclude_patterns, default_switches = blobify_patterns_info

    # Keep headers minimal - no verbose metadata
    git_info = ""
    blobify_info = ""
    scrubbing_info = ""

    # Adjust format description based on options
    if not include_content and not include_index and not include_metadata:
        format_description = """# This file contains no useful output - index, content, and metadata have all been disabled."""
    elif not include_content and not include_index:
        format_description = """# This file contains metadata of all text files found in the specified directory.
# Format:
# 1. Metadata sections for each file (size, timestamps)
# 2. Each file section is marked with START_FILE and END_FILE delimiters"""
    elif not include_content and not include_metadata:
        format_description = """# This file contains an index of all text files found in the specified directory."""
    elif not include_content:
        format_description = """# This file contains an index and metadata of all text files found in the specified directory.
# Format:
# 1. File listing with relative paths
# 2. Metadata sections for each file (size, timestamps)
# 3. Each file section is marked with START_FILE and END_FILE delimiters"""
    elif not include_metadata and include_index:
        format_description = """# This file contains an index and contents of all text files found in the specified directory.
# Format:
# 1. File listing with relative paths
# 2. Content sections for each file
# 3. Each file section is marked with START_FILE and END_FILE delimiters
#
# Files ignored by .gitignore are listed in the index but marked as [IGNORED BY GITIGNORE]
# Files excluded by .blobify are listed in the index but marked as [EXCLUDED BY .blobify]
# and their content is excluded with a placeholder message."""
    elif not include_metadata:
        format_description = """# This file contains contents of all text files found in the specified directory.
# Format:
# 1. Content sections for each file
# 2. Each file section is marked with START_FILE and END_FILE delimiters
#
# Files ignored by .gitignore or excluded by .blobify have their content excluded
# with a placeholder message."""
    elif include_index:
        format_description = """# This file contains an index and contents of all text files found in the specified directory.
# Format:
# 1. File listing with relative paths
# 2. Content sections for each file, including metadata and full content
# 3. Each file section is marked with START_FILE and END_FILE delimiters
#
# Files ignored by .gitignore are listed in the index but marked as [IGNORED BY GITIGNORE]
# Files excluded by .blobify are listed in the index but marked as [EXCLUDED BY .blobify]
# and their content is excluded with a placeholder message."""
    else:
        format_description = """# This file contains the contents of all text files found in the specified directory.
# Format:
# 1. Content sections for each file, including metadata and full content
# 2. Each file section is marked with START_FILE and END_FILE delimiters
#
# Files ignored by .gitignore or excluded by .blobify have their content excluded
# with a placeholder message."""

    header = """# Blobify Text File Index
# Generated: {datetime}
# Source Directory: {directory}{git_info}{blobify_info}{scrubbing_info}
#
{format_description}
#
# This format is designed to be both human-readable and machine-parseable.
# Files are ordered alphabetically by relative path.
#
""".format(
        datetime=datetime.datetime.now().isoformat(),
        directory=str(directory.absolute()),
        git_info=git_info,
        blobify_info=blobify_info,
        scrubbing_info=scrubbing_info,
        format_description=format_description,
    )

    return header


def generate_index(all_files: List[Dict], gitignored_directories: List[Path], include_content: bool = True) -> str:
    """Generate the file index section."""
    index = []

    # When content is disabled, don't show status labels since they refer to content inclusion
    if include_content:
        # Add gitignored directories to the index with status labels
        for dir_path in sorted(gitignored_directories, key=lambda x: str(x).lower()):
            index.append(f"{dir_path} [IGNORED BY GITIGNORE]")

        # Build index for files with status labels
        for file_info in all_files:
            relative_path = file_info["relative_path"]
            if file_info.get("is_blobify_included", False):
                index.append(f"{relative_path} [INCLUDED BY .blobify]")
            elif file_info["is_git_ignored"]:
                index.append(f"{relative_path} [IGNORED BY GITIGNORE]")
            elif file_info["is_blobify_excluded"]:
                index.append(f"{relative_path} [EXCLUDED BY .blobify]")
            else:
                index.append(str(relative_path))
    else:
        # When content is disabled, just show clean file listings without status labels
        # Include all discovered files regardless of git/blobify status
        all_paths = []

        # Add directories (without status labels)
        for dir_path in sorted(gitignored_directories, key=lambda x: str(x).lower()):
            all_paths.append(str(dir_path))

        # Add files (without status labels)
        for file_info in all_files:
            all_paths.append(str(file_info["relative_path"]))

        # Sort all paths together for a clean listing
        index = sorted(set(all_paths), key=str.lower)

    # Build index section
    index_section = "# FILE INDEX\n" + "#" * 80 + "\n"
    index_section += "\n".join(index)

    # Only add FILE CONTENTS header if content will be included
    if include_content:
        index_section += "\n\n# FILE CONTENTS\n" + "#" * 80 + "\n"
    else:
        index_section += "\n"

    return index_section


def generate_content(
    all_files: List[Dict],
    scrub_data: bool,
    include_line_numbers: bool,
    include_content: bool,
    include_metadata: bool,
    debug: bool,
) -> tuple:
    """
    Generate the file content section.
    Returns tuple of (content_string, total_substitutions).
    """
    # If both content and metadata are disabled, return empty string immediately
    if not include_content and not include_metadata:
        return "", 0

    content = []
    total_substitutions = 0

    for file_info in all_files:
        file_path = file_info["path"]
        relative_path = file_info["relative_path"]
        is_git_ignored = file_info["is_git_ignored"]
        is_blobify_excluded = file_info["is_blobify_excluded"]
        is_blobify_included = file_info.get("is_blobify_included", False)

        # Always include the START_FILE marker when metadata or content is enabled
        content.append(f"\nSTART_FILE: {relative_path}")

        # Include metadata section if enabled
        if include_metadata:
            metadata = get_file_metadata(file_path)
            content.append("FILE_METADATA:")
            content.append(f"  Path: {relative_path}")
            content.append(f"  Size: {metadata['size']} bytes")
            content.append(f"  Created: {metadata['created']}")
            content.append(f"  Modified: {metadata['modified']}")
            content.append(f"  Accessed: {metadata['accessed']}")

            # Only include status when content is also being included
            if include_content:
                if is_blobify_included:
                    content.append("  Status: INCLUDED BY .blobify")
                elif is_git_ignored:
                    content.append("  Status: IGNORED BY GITIGNORE")
                elif is_blobify_excluded:
                    content.append("  Status: EXCLUDED BY .blobify")
                elif scrub_data and SCRUBADUB_AVAILABLE:
                    content.append("  Status: PROCESSED WITH SCRUBADUB")

        # Include content section if enabled
        if include_content:
            content.append("FILE_CONTENT:")
            if is_git_ignored:
                content.append("[Content excluded - file ignored by .gitignore]")
            elif is_blobify_excluded:
                content.append("[Content excluded - file excluded by .blobify]")
            else:
                try:
                    if debug:
                        print_file_processing(f"Processing file: {relative_path}")

                    with open(file_path, "r", encoding="utf-8", errors="strict") as f:
                        file_content = f.read()

                    # Attempt to scrub content if enabled
                    processed_content, substitutions = scrub_content(file_content, scrub_data, debug)
                    total_substitutions += substitutions

                    if debug and substitutions > 0:
                        print_debug(f"File had {substitutions} substitutions, total now: {total_substitutions}")

                    # Add line numbers if enabled
                    if include_line_numbers:
                        lines = processed_content.split("\n")
                        numbered_lines = []
                        line_number_width = len(str(len(lines)))

                        for i, line in enumerate(lines, 1):
                            line_number = str(i).rjust(line_number_width)
                            numbered_lines.append(f"{line_number}: {line}")

                        processed_content = "\n".join(numbered_lines)

                    content.append(processed_content)

                except Exception as e:
                    content.append(f"[Error reading file: {str(e)}]")

        content.append(f"END_FILE: {relative_path}\n")

    return "\n".join(content), total_substitutions


def format_output(
    discovery_context: Dict,
    directory: Path,
    context: str,
    scrub_data: bool,
    include_line_numbers: bool,
    include_index: bool,
    include_content: bool,
    include_metadata: bool,
    debug: bool,
    blobify_patterns_info: tuple,
) -> tuple:
    """
    Format the complete output string.
    Returns tuple of (output_string, total_substitutions, file_count).
    """
    all_files = discovery_context["all_files"]
    gitignored_directories = discovery_context["gitignored_directories"]
    git_root = discovery_context["git_root"]
    included_files = discovery_context["included_files"]

    # Sort all files for consistent output
    all_files.sort(key=lambda x: str(x["relative_path"]).lower())

    # Generate header
    header = generate_header(
        directory,
        git_root,
        context,
        scrub_data,
        blobify_patterns_info,
        include_index,
        include_content,
        include_metadata,
    )

    # Generate index section (if enabled)
    if include_index:
        index_section = generate_index(all_files, gitignored_directories, include_content)
    else:
        # No index, just file contents header (unless no content either)
        if include_content or include_metadata:
            index_section = "\n# FILE CONTENTS\n" + "#" * 80 + "\n"
        else:
            index_section = ""

    # Generate content section (only if content or metadata is enabled)
    if include_content or include_metadata:
        content_section, total_substitutions = generate_content(all_files, scrub_data, include_line_numbers, include_content, include_metadata, debug)
    else:
        content_section = ""
        total_substitutions = 0
        # Add debug output to see if this branch is being taken
        if debug:
            from .console import print_debug

            print_debug("Skipping content generation due to --no-content and --no-metadata flags")

    # Combine all sections
    result = header + index_section + content_section

    return result, total_substitutions, len(included_files)
