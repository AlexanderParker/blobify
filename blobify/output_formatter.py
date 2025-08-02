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
) -> str:
    """Generate the file header with metadata and configuration info."""
    blobify_include_patterns, blobify_exclude_patterns, default_switches = blobify_patterns_info

    git_info = f"\n# Git repository: {git_root}" if git_root else "\n# Not in a git repository"

    blobify_info = ""
    if git_root and (blobify_include_patterns or blobify_exclude_patterns):
        context_info = f" (context: {context})" if context else ""
        blobify_info = f"\n# .blobify configuration{context_info}: {len(blobify_include_patterns)} include patterns, {len(blobify_exclude_patterns)} exclude patterns"
    if git_root and default_switches:
        blobify_info += f", {len(default_switches)} default switches"

    scrubbing_info = ""
    if scrub_data and SCRUBADUB_AVAILABLE:
        scrubbing_info = "\n# Content processed with scrubadub for sensitive data detection"
        scrubbing_info += "\n# WARNING: Review output carefully - scrubadub may miss sensitive data"
    elif not scrub_data:
        scrubbing_info = "\n# Sensitive data scrubbing DISABLED (--noclean flag used)"
    else:
        scrubbing_info = "\n# Sensitive data scrubbing UNAVAILABLE (scrubadub not installed)"

    # Adjust format description based on whether index is included
    if include_index:
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


def generate_index(all_files: List[Dict], gitignored_directories: List[Path]) -> str:
    """Generate the file index section."""
    index = []

    # Add gitignored directories to the index
    for dir_path in sorted(gitignored_directories, key=lambda x: str(x).lower()):
        index.append(f"{dir_path} [IGNORED BY GITIGNORE]")

    # Build index for files
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

    # Build index section
    index_section = "# FILE INDEX\n" + "#" * 80 + "\n"
    index_section += "\n".join(index)
    index_section += "\n\n# FILE CONTENTS\n" + "#" * 80 + "\n"

    return index_section


def generate_content(all_files: List[Dict], scrub_data: bool, include_line_numbers: bool, debug: bool) -> tuple:
    """
    Generate the file content section.
    Returns tuple of (content_string, total_substitutions).
    """
    content = []
    total_substitutions = 0

    for file_info in all_files:
        file_path = file_info["path"]
        relative_path = file_info["relative_path"]
        is_git_ignored = file_info["is_git_ignored"]
        is_blobify_excluded = file_info["is_blobify_excluded"]
        is_blobify_included = file_info.get("is_blobify_included", False)

        metadata = get_file_metadata(file_path)

        content.append(f"\nSTART_FILE: {relative_path}")
        content.append("FILE_METADATA:")
        content.append(f"  Path: {relative_path}")
        content.append(f"  Size: {metadata['size']} bytes")
        content.append(f"  Created: {metadata['created']}")
        content.append(f"  Modified: {metadata['modified']}")
        content.append(f"  Accessed: {metadata['accessed']}")

        if is_blobify_included:
            content.append("  Status: INCLUDED BY .blobify")
        elif is_git_ignored:
            content.append("  Status: IGNORED BY GITIGNORE")
        elif is_blobify_excluded:
            content.append("  Status: EXCLUDED BY .blobify")
        elif scrub_data and SCRUBADUB_AVAILABLE:
            content.append("  Status: PROCESSED WITH SCRUBADUB")

        content.append("\nFILE_CONTENT:")

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

        content.append("\nEND_FILE: {}\n".format(relative_path))

    return "".join(content), total_substitutions


def format_output(
    discovery_context: Dict,
    directory: Path,
    context: str,
    scrub_data: bool,
    include_line_numbers: bool,
    include_index: bool,
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
    header = generate_header(directory, git_root, context, scrub_data, blobify_patterns_info, include_index)

    # Generate index section (if enabled)
    if include_index:
        index_section = generate_index(all_files, gitignored_directories)
    else:
        # No index, just file contents header
        index_section = "\n# FILE CONTENTS\n" + "#" * 80 + "\n"

    # Generate content section
    content_section, total_substitutions = generate_content(all_files, scrub_data, include_line_numbers, debug)

    # Combine all sections
    result = header + index_section + content_section

    return result, total_substitutions, len(included_files)
