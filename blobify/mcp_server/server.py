"""
MCP server implementation for blobify.

This module implements the core MCP server functionality for blobify,
providing tools, resources, and prompts that allow AI agents to interact
with blobify's codebase aggregation capabilities.
"""

import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

from mcp.server.fastmcp import Context, FastMCP
from mcp.server.session import ServerSession

# Import blobify components
from ..config import get_available_contexts, get_context_descriptions
from ..file_scanner import get_built_in_ignored_patterns, scan_files
from ..git_utils import is_git_repository
from ..main import main as blobify_main


# Separate implementation functions for testing
async def _analyse_filesystem_impl(directory: str, ctx: Optional[Context] = None) -> Dict[str, Any]:
    """
    Implementation of filesystem analysis for blobify configuration.

    This function scans the directory structure, respects .gitignore patterns, applies built-in
    exclusions, and returns detailed information about discovered files and directories
    to help with .blobify configuration generation.

    Args:
        directory: Path to the project directory to analyze
        ctx: Optional context for progress reporting

    Returns:
        Dictionary containing filesystem analysis with file lists, statistics, and metadata
    """
    if ctx:
        await ctx.info(f"Analyzing filesystem structure: {directory}")

    try:
        dir_path = Path(directory)
        if not dir_path.exists():
            raise ValueError(f"Directory does not exist: {directory}")
        if not dir_path.is_dir():
            raise ValueError(f"Path is not a directory: {directory}")

        if ctx:
            await ctx.report_progress(0.2, message="Scanning files...")

        # Use blobify's built-in file scanner
        discovery_context = scan_files(dir_path, debug=False)

        if ctx:
            await ctx.report_progress(0.8, message="Processing results...")

        # Extract information from discovery context
        all_files = discovery_context["all_files"]
        included_files = discovery_context["included_files"]
        git_ignored_files = discovery_context["git_ignored_files"]
        blobify_excluded_files = discovery_context["blobify_excluded_files"]
        gitignored_directories = discovery_context["gitignored_directories"]
        git_root = discovery_context["git_root"]

        # Organize files by type/extension
        file_types = {}
        for file_info in all_files:
            path = file_info["relative_path"]
            ext = path.suffix.lower() if path.suffix else "(no extension)"
            if ext not in file_types:
                file_types[ext] = []
            file_types[ext].append(str(path))

        # Build directory structure
        directories = set()
        for file_info in all_files:
            path = file_info["relative_path"]
            for parent in path.parents:
                if parent != Path("."):
                    directories.add(str(parent))

        result = {
            "directory": str(dir_path.absolute()),
            "is_git_repository": git_root is not None,
            "git_root": str(git_root) if git_root else None,
            "statistics": {
                "total_files": len(all_files),
                "included_files": len(included_files),
                "git_ignored_files": len(git_ignored_files),
                "blobify_excluded_files": len(blobify_excluded_files),
                "directories": len(directories),
                "gitignored_directories": len(gitignored_directories),
            },
            "file_types": {k: len(v) for k, v in file_types.items()},
            "sample_files_by_type": {k: v[:5] for k, v in file_types.items()},  # First 5 of each type
            "directories": sorted(directories),
            "gitignored_directories": [str(d) for d in gitignored_directories],
            "included_files": [str(f["relative_path"]) for f in included_files[:20]],  # First 20
            "git_ignored_files": [str(f["relative_path"]) for f in git_ignored_files[:10]],  # First 10
            "blobify_excluded_files": [str(f["relative_path"]) for f in blobify_excluded_files[:10]],  # First 10
        }

        if ctx:
            await ctx.report_progress(1.0, message="Analysis complete")
            await ctx.info(f"Analysis complete: {result['statistics']['total_files']} files analyzed")

        return result

    except Exception as e:
        error_msg = f"Error analyzing filesystem: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        raise ValueError(error_msg)


async def _update_blobify_file_impl(directory: str, content: str, ctx: Optional[Context] = None) -> str:
    """
    Implementation of .blobify file creation/update.

    Args:
        directory: Path to the directory where .blobify file should be created/updated
        content: Complete content for the .blobify file
        ctx: Optional context for logging

    Returns:
        Confirmation message about the file operation
    """
    if ctx:
        await ctx.info(f"Updating .blobify file in directory: {directory}")

    try:
        dir_path = Path(directory)
        if not dir_path.exists():
            raise ValueError(f"Directory does not exist: {directory}")
        if not dir_path.is_dir():
            raise ValueError(f"Path is not a directory: {directory}")

        blobify_file = dir_path / ".blobify"
        action = "Updated" if blobify_file.exists() else "Created"

        # Write the content to .blobify file
        blobify_file.write_text(content, encoding="utf-8")

        if ctx:
            await ctx.info(f"{action} .blobify file with {len(content)} characters")

        return f"{action} .blobify file at {blobify_file}"

    except Exception as e:
        error_msg = f"Error updating .blobify file: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        raise ValueError(error_msg)


async def _run_blobify_impl(
    directory: str,
    context: Optional[str] = None,
    enable_scrubbing: bool = True,
    output_line_numbers: bool = True,
    show_excluded: bool = True,
    ctx: Optional[Context] = None,
) -> str:
    """
    Implementation of blobify execution.

    Args:
        directory: Path to the directory to process
        context: Optional .blobify context to use
        enable_scrubbing: Whether to enable sensitive data scrubbing
        output_line_numbers: Whether to include line numbers in output
        show_excluded: Whether to show excluded files in output
        ctx: Optional context for logging

    Returns:
        String containing the complete blobify output with packaged codebase content
    """
    if ctx:
        await ctx.info(f"Running blobify on directory: {directory}")
        if context:
            await ctx.info(f"Using context: {context}")

    try:
        # Validate directory exists
        dir_path = Path(directory)
        if not dir_path.exists():
            raise ValueError(f"Directory does not exist: {directory}")
        if not dir_path.is_dir():
            raise ValueError(f"Path is not a directory: {directory}")

        # Build command line arguments
        args = ["bfy", str(dir_path)]

        if context:
            args.extend(["-x", context])

        args.extend(
            [
                f"--enable-scrubbing={str(enable_scrubbing).lower()}",
                f"--output-line-numbers={str(output_line_numbers).lower()}",
                f"--show-excluded={str(show_excluded).lower()}",
            ]
        )

        if ctx:
            await ctx.debug(f"Running blobify with args: {args}")

        # Capture output by temporarily redirecting stdout
        original_stdout = sys.stdout
        original_argv = sys.argv
        temp_file_path = None

        try:
            # Create temporary file for output
            with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as temp_file:
                temp_file_path = temp_file.name

            # Run blobify with output file
            sys.argv = args + ["--output-filename", temp_file_path]
            blobify_main()

            # Read the output - ensure file exists and has content
            if os.path.exists(temp_file_path):
                with open(temp_file_path, "r", encoding="utf-8") as f:
                    result = f.read()
            else:
                # If file doesn't exist, blobify may have failed silently
                result = ""

            if ctx:
                await ctx.info(f"Successfully generated blobify output ({len(result)} characters)")

            return result

        finally:
            sys.stdout = original_stdout
            sys.argv = original_argv
            # Clean up temp file
            if temp_file_path:
                os.unlink(temp_file_path)

    except Exception as e:
        error_msg = f"Error running blobify: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        raise ValueError(error_msg)


def _get_blobify_file_impl(directory_path: str) -> str:
    """
    Implementation of .blobify file reading.

    Returns the complete .blobify file content if it exists, or an error message
    if the file is not found.
    """
    try:
        dir_path = Path(directory_path)
        blobify_file = dir_path / ".blobify"

        if not blobify_file.exists():
            return f"No .blobify file exists in {directory_path}"

        content = blobify_file.read_text(encoding="utf-8")
        return f".blobify configuration for {directory_path}:\n\n{content}"

    except Exception as e:
        return f"Error reading .blobify file: {str(e)}"


def _get_default_excludes_impl() -> str:
    """
    Implementation of default excludes listing.

    Returns a formatted list of all directories and files that blobify excludes
    automatically.
    """
    try:
        patterns = get_built_in_ignored_patterns()

        # Categorize patterns for better readability
        categories = {
            "Version Control": [".git", ".svn", ".hg"],
            "IDEs": [".idea", ".vscode", ".vs"],
            "Package Managers": ["node_modules", "bower_components", "vendor", "packages"],
            "Python": ["__pycache__", ".pytest_cache", ".mypy_cache", "venv", ".venv", "env", ".env"],
            "Build/Output": ["dist", "build", "target", "out", "obj", "Debug", "release", "Release"],
            "Security": [
                "certs",
                "certificates",
                "keys",
                "private",
                "ssl",
                ".ssh",
                "tls",
                ".gpg",
                ".keyring",
                ".gnupg",
            ],
            "Other": [],
        }

        # Categorize patterns
        categorized = {cat: [] for cat in categories}
        for pattern in patterns:
            placed = False
            for category, cat_patterns in categories.items():
                if pattern in cat_patterns:
                    categorized[category].append(pattern)
                    placed = True
                    break
            if not placed:
                categorized["Other"].append(pattern)

        # Format output
        result = "Built-in exclusion patterns that blobify applies automatically:\n\n"
        for category, cat_patterns in categorized.items():
            if cat_patterns:
                result += f"{category}:\n"
                for pattern in sorted(cat_patterns):
                    result += f"  - {pattern}\n"
                result += "\n"

        result += f"Total patterns: {len(patterns)}\n\n"
        result += "These patterns are applied before any .blobify configuration rules."

        return result

    except Exception as e:
        return f"Error getting default excludes: {str(e)}"


def _get_contexts_impl(directory_path: str) -> str:
    """
    Implementation of contexts listing.

    Returns information about all defined contexts in the .blobify file.
    """
    try:
        dir_path = Path(directory_path)

        # Check if it's a git repository (required for .blobify)
        git_root = is_git_repository(dir_path)
        if not git_root:
            return f"No git repository found in {directory_path}. Contexts require a .blobify file in a git repository."

        # Get available contexts
        contexts = get_available_contexts(git_root)
        if not contexts:
            return f"No contexts found in .blobify file at {git_root}"

        # Get context descriptions and inheritance info
        descriptions = get_context_descriptions(git_root)

        result = f"Available contexts in {directory_path}:\n\n"

        for context in sorted(contexts):
            result += f"• {context}"

            # Add description if available
            if context in descriptions:
                result += f": {descriptions[context]}"

            result += "\n"

        result += f"\nTotal contexts: {len(contexts)}\n"
        result += "\nUse these context names with the run_blobify tool's 'context' parameter."

        return result

    except Exception as e:
        return f"Error getting contexts: {str(e)}"


def _generate_blobify_file_prompt_impl(filesystem_analysis: str, instructions: str = "") -> str:
    """
    Implementation of .blobify file generation prompt.
    """
    base_prompt = """Based on the filesystem analysis provided, generate a comprehensive .blobify configuration file.

The .blobify file uses this syntax:
- `+pattern` to include files/directories
- `-pattern` to exclude files/directories
- `@option=value` for configuration options
- `[context-name]` to define contexts
- `[child:parent]` for context inheritance
- `## comment` for AI/LLM instructions

Common patterns:
- `+*.py` - include Python files
- `+src/**` - include everything in src directory
- `-tests/**` - exclude test directories
- `-*.log` - exclude log files
- `@copy-to-clipboard=true` - enable clipboard output
- `@filter="functions","^def"` - content filtering

"""

    if instructions:
        base_prompt += f"\nSpecific instructions: {instructions}\n"

    base_prompt += f"\nFilesystem analysis:\n{filesystem_analysis}\n\n"
    base_prompt += """Generate a .blobify configuration that:
1. Creates useful contexts for different use cases (e.g., docs-only, backend, frontend, tests)
2. Properly excludes unwanted files while including relevant source code
3. Uses appropriate configuration options
4. Includes helpful AI/LLM instructions for each context

Return only the .blobify file content, no explanations."""

    return base_prompt


def _update_blobify_file_prompt_impl(existing_config: str, filesystem_analysis: str, instructions: str) -> str:
    """
    Implementation of .blobify file update prompt.
    """
    base_prompt = """Update the existing .blobify configuration based on the provided instructions and filesystem analysis.

The .blobify file uses this syntax:
- `+pattern` to include files/directories
- `-pattern` to exclude files/directories
- `@option=value` for configuration options
- `[context-name]` to define contexts
- `[child:parent]` for context inheritance
- `## comment` for AI/LLM instructions

"""
    base_prompt += f"Update instructions: {instructions}\n\n"
    base_prompt += f"Current .blobify configuration:\n{existing_config}\n\n"
    base_prompt += f"Current filesystem analysis:\n{filesystem_analysis}\n\n"
    base_prompt += """Update the configuration according to the instructions while:
1. Preserving existing contexts and patterns that are still relevant
2. Adding new contexts or patterns as needed
3. Maintaining proper syntax and inheritance relationships
4. Keeping helpful AI/LLM instructions

Return only the updated .blobify file content, no explanations."""

    return base_prompt


def _act_on_contents_prompt_impl(blobify_output: str, instructions: str) -> str:
    """
    Implementation of act on contents prompt.
    """
    base_prompt = f"""You have been provided with blobified codebase content and specific instructions for analysis or action.

Instructions: {instructions}

The blobified content contains the complete codebase packaged into a single text file with:
- File index showing all discovered files
- Complete file contents with line numbers
- Metadata about file sizes and timestamps
- Exclusion information for ignored files

Analyze the content according to the instructions and provide your response.

BLOBIFIED CODEBASE CONTENT:
{blobify_output}"""

    return base_prompt


def create_mcp_server() -> FastMCP:
    """Create and configure the MCP server for blobify."""
    mcp = FastMCP(
        name="Blobify",
        instructions=(
            "Blobify packages entire codebases into single text files optimized for AI consumption. "
            "It respects .gitignore patterns, supports custom .blobify configuration files with contexts, "
            "applies content filtering, and handles sensitive data scrubbing. Use this server to analyze "
            "project structures, generate configurations, and create AI-ready codebase packages."
        ),
    )

    # Tools
    @mcp.tool()
    async def run_blobify(
        directory: str,
        context: Optional[str] = None,
        enable_scrubbing: bool = True,
        output_line_numbers: bool = True,
        show_excluded: bool = True,
        ctx: Context[ServerSession, None] = None,
    ) -> str:
        """
        Run blobify on a specified directory to package the codebase into a single text file.

        Args:
            directory: Path to the directory to process
            context: Optional .blobify context to use (e.g., 'docs-only', 'backend')
            enable_scrubbing: Whether to enable sensitive data scrubbing (default: True)
            output_line_numbers: Whether to include line numbers in output (default: True)
            show_excluded: Whether to show excluded files in output (default: True)

        Returns:
            String containing the complete blobify output with packaged codebase content
        """
        return await _run_blobify_impl(directory, context, enable_scrubbing, output_line_numbers, show_excluded, ctx)

    @mcp.tool()
    async def update_blobify_file(directory: str, content: str, ctx: Context[ServerSession, None] = None) -> str:
        """
        Create or update a .blobify configuration file in the specified directory.

        Args:
            directory: Path to the directory where .blobify file should be created/updated
            content: Complete content for the .blobify file

        Returns:
            Confirmation message about the file operation
        """
        return await _update_blobify_file_impl(directory, content, ctx)

    @mcp.tool()
    async def analyse_filesystem(directory: str, ctx: Context[ServerSession, None] = None) -> Dict[str, Any]:
        """
        Analyze the filesystem structure of a project directory for blobify configuration.

        This tool scans the directory structure, respects .gitignore patterns, applies built-in
        exclusions, and returns detailed information about discovered files and directories
        to help with .blobify configuration generation.

        Args:
            directory: Path to the project directory to analyze

        Returns:
            Dictionary containing filesystem analysis with file lists, statistics, and metadata
        """
        return await _analyse_filesystem_impl(directory, ctx)

    # Resources
    @mcp.resource("blobify://config/{directory_path}")
    def get_blobify_file(directory_path: str) -> str:
        """
        Get the contents of an existing .blobify configuration file.

        Returns the complete .blobify file content if it exists, or an error message
        if the file is not found. This is useful for understanding current project
        configuration before making updates.
        """
        return _get_blobify_file_impl(directory_path)

    @mcp.resource("blobify://excludes/default")
    def get_default_excludes() -> str:
        """
        Get the built-in exclusion patterns that blobify applies by default.

        Returns a formatted list of all directories and files that blobify excludes
        automatically, such as .git, node_modules, __pycache__, build directories,
        and security-sensitive files.
        """
        return _get_default_excludes_impl()

    @mcp.resource("blobify://contexts/{directory_path}")
    def get_contexts(directory_path: str) -> str:
        """
        List available contexts from a .blobify configuration file.

        Returns information about all defined contexts in the .blobify file,
        including their descriptions and inheritance relationships. This helps
        understand available options when running blobify with specific contexts.
        """
        return _get_contexts_impl(directory_path)

    # Prompts
    @mcp.prompt()
    def generate_blobify_file(filesystem_analysis: str, instructions: str = "") -> str:
        """
        Generate a new .blobify configuration file based on filesystem analysis.

        Args:
            filesystem_analysis: JSON output from the analyse_filesystem tool
            instructions: Optional specific instructions for the configuration
        """
        return _generate_blobify_file_prompt_impl(filesystem_analysis, instructions)

    @mcp.prompt()
    def update_blobify_file_prompt(existing_config: str, filesystem_analysis: str, instructions: str) -> str:
        """
        Update an existing .blobify configuration file based on filesystem analysis and instructions.

        Args:
            existing_config: Current .blobify file content
            filesystem_analysis: JSON output from the analyse_filesystem tool
            instructions: Specific instructions for what to update
        """
        return _update_blobify_file_prompt_impl(existing_config, filesystem_analysis, instructions)

    @mcp.prompt()
    def act_on_contents(blobify_output: str, instructions: str) -> str:
        """
        Provide instructions for acting on blobify output content.

        Args:
            blobify_output: Complete output from the run_blobify tool
            instructions: Specific instructions for what actions to perform
        """
        return _act_on_contents_prompt_impl(blobify_output, instructions)

    return mcp
