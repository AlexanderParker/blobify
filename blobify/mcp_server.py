#!/usr/bin/env python3
"""
MCP Server for Blobify - Package codebases into single text files for AI consumption.

This MCP server provides tools for:
- Packaging entire codebases into text files
- Listing available contexts from .blobify files
- Applying content filters for specific analysis needs
- Managing blobify configurations
"""

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

# MCP server imports
try:
    from mcp.server import Server
    from mcp.server.models import InitializationOptions
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        Resource,
        Tool,
        TextContent,
        ImageContent,
        EmbeddedResource,
        CallToolResult,
        ListResourcesResult,
        ListToolsResult,
        ReadResourceResult,
    )
except ImportError:
    print("Error: MCP package not found. Install with: pip install mcp", file=sys.stderr)
    sys.exit(1)

# Blobify imports
try:
    from blobify.main import main as blobify_main
    from blobify.config import get_available_contexts, list_available_contexts
    from blobify.file_scanner import scan_files
    from blobify.git_utils import is_git_repository
except ImportError:
    print("Error: Blobify package not found. Make sure blobify is installed.", file=sys.stderr)
    sys.exit(1)


# Server configuration
SERVER_NAME = "blobify-mcp-server"
SERVER_VERSION = "1.0.0"

# Initialize the MCP server
server = Server(SERVER_NAME)


# Tool definitions
@server.list_tools()
async def list_tools() -> List[Tool]:
    """List available blobify tools."""
    return [
        Tool(
            name="blobify_package",
            description=(
                "Package a codebase directory into a single text file for AI analysis. "
                "Supports gitignore patterns, .blobify configuration, content filters, and context selection."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "Directory to package (absolute or relative path)"},
                    "context": {"type": "string", "description": "Context from .blobify file to use (optional)"},
                    "filters": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": 'Content filters in CSV format: "name","regex","filepattern" (optional)',
                    },
                    "output_filename": {
                        "type": "string",
                        "description": "Output filename (optional, defaults to temporary file)",
                    },
                    "enable_scrubbing": {
                        "type": "boolean",
                        "description": "Enable sensitive data scrubbing (default: true)",
                    },
                    "output_line_numbers": {
                        "type": "boolean",
                        "description": "Include line numbers in output (default: true)",
                    },
                    "output_index": {"type": "boolean", "description": "Include file index section (default: true)"},
                    "output_content": {"type": "boolean", "description": "Include file contents (default: true)"},
                    "output_metadata": {"type": "boolean", "description": "Include file metadata (default: true)"},
                    "show_excluded": {
                        "type": "boolean",
                        "description": "Show excluded files in output (default: true)",
                    },
                    "suppress_timestamps": {
                        "type": "boolean",
                        "description": "Suppress timestamps for reproducible output (default: false)",
                    },
                    "debug": {"type": "boolean", "description": "Enable debug output (default: false)"},
                },
                "required": ["directory"],
            },
        ),
        Tool(
            name="blobify_list_contexts",
            description="List available contexts from a .blobify configuration file in a directory.",
            inputSchema={
                "type": "object",
                "properties": {"directory": {"type": "string", "description": "Directory containing .blobify file"}},
                "required": ["directory"],
            },
        ),
        Tool(
            name="blobify_scan_files",
            description="Scan a directory and return information about discovered files without generating output.",
            inputSchema={
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "Directory to scan"},
                    "context": {"type": "string", "description": "Context from .blobify file to use (optional)"},
                    "debug": {"type": "boolean", "description": "Enable debug output (default: false)"},
                },
                "required": ["directory"],
            },
        ),
        Tool(
            name="blobify_create_config",
            description="Create a .blobify configuration file with specified patterns and options.",
            inputSchema={
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "Directory where .blobify file should be created"},
                    "config": {"type": "string", "description": "Configuration content for .blobify file"},
                    "overwrite": {
                        "type": "boolean",
                        "description": "Overwrite existing .blobify file (default: false)",
                    },
                },
                "required": ["directory", "config"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
    """Handle tool calls."""
    try:
        if name == "blobify_package":
            return await handle_blobify_package(arguments)
        elif name == "blobify_list_contexts":
            return await handle_list_contexts(arguments)
        elif name == "blobify_scan_files":
            return await handle_scan_files(arguments)
        elif name == "blobify_create_config":
            return await handle_create_config(arguments)
        else:
            return CallToolResult(content=[TextContent(type="text", text=f"Unknown tool: {name}")], isError=True)
    except Exception as e:
        return CallToolResult(content=[TextContent(type="text", text=f"Error executing tool {name}: {str(e)}")], isError=True)


async def handle_blobify_package(arguments: Dict[str, Any]) -> CallToolResult:
    """Handle blobify_package tool call."""
    directory = arguments["directory"]

    # Validate directory exists
    dir_path = Path(directory).resolve()
    if not dir_path.exists():
        return CallToolResult(content=[TextContent(type="text", text=f"Directory does not exist: {directory}")], isError=True)

    if not dir_path.is_dir():
        return CallToolResult(content=[TextContent(type="text", text=f"Path is not a directory: {directory}")], isError=True)

    # Prepare blobify arguments
    argv = ["bfy", str(dir_path)]

    # Handle optional arguments
    if "context" in arguments and arguments["context"]:
        argv.extend(["-x", arguments["context"]])

    if "filters" in arguments and arguments["filters"]:
        for filter_arg in arguments["filters"]:
            argv.extend(["--filter", filter_arg])

    # Determine output file
    output_file = arguments.get("output_filename")
    if not output_file:
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False)
        output_file = temp_file.name
        temp_file.close()

    argv.extend(["--output-filename", output_file])

    # Add boolean options
    bool_options = {
        "enable_scrubbing": True,
        "output_line_numbers": True,
        "output_index": True,
        "output_content": True,
        "output_metadata": True,
        "show_excluded": True,
        "suppress_timestamps": False,
        "debug": False,
    }

    for option, default in bool_options.items():
        if option in arguments:
            value = arguments[option]
        else:
            value = default

        option_name = option.replace("_", "-")
        argv.extend([f"--{option_name}={str(value).lower()}"])

    # Execute blobify
    original_argv = sys.argv
    try:
        sys.argv = argv
        blobify_main()

        # Read the output file
        output_path = Path(output_file)
        if output_path.exists():
            content = output_path.read_text(encoding="utf-8")

            # Clean up temporary file if we created it
            if not arguments.get("output_filename"):
                output_path.unlink()

            return CallToolResult(content=[TextContent(type="text", text=f"Successfully packaged {directory}\n\nOutput:\n{content}")])
        else:
            return CallToolResult(content=[TextContent(type="text", text="Error: Output file was not created")], isError=True)

    except SystemExit:
        # Blobify may call sys.exit, which is normal
        output_path = Path(output_file)
        if output_path.exists():
            content = output_path.read_text(encoding="utf-8")

            # Clean up temporary file if we created it
            if not arguments.get("output_filename"):
                output_path.unlink()

            return CallToolResult(content=[TextContent(type="text", text=f"Successfully packaged {directory}\n\nOutput:\n{content}")])
        else:
            return CallToolResult(content=[TextContent(type="text", text="Error: Blobify execution failed")], isError=True)
    finally:
        sys.argv = original_argv


async def handle_list_contexts(arguments: Dict[str, Any]) -> CallToolResult:
    """Handle blobify_list_contexts tool call."""
    directory = arguments["directory"]

    # Validate directory exists
    dir_path = Path(directory).resolve()
    if not dir_path.exists():
        return CallToolResult(content=[TextContent(type="text", text=f"Directory does not exist: {directory}")], isError=True)

    # Check if it's a git repository
    git_root = is_git_repository(dir_path)
    if not git_root:
        return CallToolResult(
            content=[TextContent(type="text", text="No git repository found - contexts require a .blobify file in a git repository.")],
            isError=False,
        )

    # Get available contexts
    contexts = get_available_contexts(git_root)

    if not contexts:
        return CallToolResult(content=[TextContent(type="text", text="No contexts found in .blobify file.")], isError=False)

    # Format context information
    from blobify.config import get_context_descriptions, _get_context_inheritance_info

    descriptions = get_context_descriptions(git_root)
    inheritance_info = _get_context_inheritance_info(git_root)

    result_lines = ["Available contexts:"]
    for context in sorted(contexts):
        line_parts = [f"  {context}"]

        if context in inheritance_info:
            line_parts.append(f" (inherits from {inheritance_info[context]})")

        if context in descriptions:
            line_parts.append(f": {descriptions[context]}")

        result_lines.append("".join(line_parts))

    result_text = "\n".join(result_lines)

    return CallToolResult(content=[TextContent(type="text", text=result_text)])


async def handle_scan_files(arguments: Dict[str, Any]) -> CallToolResult:
    """Handle blobify_scan_files tool call."""
    directory = arguments["directory"]
    context = arguments.get("context")
    debug = arguments.get("debug", False)

    # Validate directory exists
    dir_path = Path(directory).resolve()
    if not dir_path.exists():
        return CallToolResult(content=[TextContent(type="text", text=f"Directory does not exist: {directory}")], isError=True)

    # Scan files
    discovery_context = scan_files(dir_path, context=context, debug=debug)

    # Format results
    all_files = discovery_context["all_files"]
    included_files = discovery_context["included_files"]
    git_ignored_files = discovery_context["git_ignored_files"]
    blobify_excluded_files = discovery_context["blobify_excluded_files"]
    gitignored_directories = discovery_context["gitignored_directories"]

    result = {
        "summary": {
            "total_files": len(all_files),
            "included_files": len(included_files),
            "git_ignored_files": len(git_ignored_files),
            "blobify_excluded_files": len(blobify_excluded_files),
            "gitignored_directories": len(gitignored_directories),
        },
        "included_files": [str(f["relative_path"]) for f in included_files],
        "git_ignored_files": [str(f["relative_path"]) for f in git_ignored_files],
        "blobify_excluded_files": [str(f["relative_path"]) for f in blobify_excluded_files],
        "gitignored_directories": [str(d) for d in gitignored_directories],
    }

    result_text = f"File scan results for {directory}:\n\n"
    result_text += f"Summary:\n"
    result_text += f"  Total files discovered: {result['summary']['total_files']}\n"
    result_text += f"  Included files: {result['summary']['included_files']}\n"
    result_text += f"  Git ignored files: {result['summary']['git_ignored_files']}\n"
    result_text += f"  Blobify excluded files: {result['summary']['blobify_excluded_files']}\n"
    result_text += f"  Git ignored directories: {result['summary']['gitignored_directories']}\n\n"

    if result["included_files"]:
        result_text += "Included files:\n"
        for file_path in result["included_files"]:
            result_text += f"  {file_path}\n"
        result_text += "\n"

    if result["git_ignored_files"]:
        result_text += "Git ignored files:\n"
        for file_path in result["git_ignored_files"]:
            result_text += f"  {file_path}\n"
        result_text += "\n"

    if result["blobify_excluded_files"]:
        result_text += "Blobify excluded files:\n"
        for file_path in result["blobify_excluded_files"]:
            result_text += f"  {file_path}\n"
        result_text += "\n"

    if result["gitignored_directories"]:
        result_text += "Git ignored directories:\n"
        for dir_path in result["gitignored_directories"]:
            result_text += f"  {dir_path}\n"

    return CallToolResult(content=[TextContent(type="text", text=result_text)])


async def handle_create_config(arguments: Dict[str, Any]) -> CallToolResult:
    """Handle blobify_create_config tool call."""
    directory = arguments["directory"]
    config_content = arguments["config"]
    overwrite = arguments.get("overwrite", False)

    # Validate directory exists
    dir_path = Path(directory).resolve()
    if not dir_path.exists():
        return CallToolResult(content=[TextContent(type="text", text=f"Directory does not exist: {directory}")], isError=True)

    blobify_file = dir_path / ".blobify"

    # Check if file exists and overwrite flag
    if blobify_file.exists() and not overwrite:
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f".blobify file already exists at {blobify_file}. Use overwrite=true to replace it.",
                )
            ],
            isError=True,
        )

    # Write the configuration
    try:
        blobify_file.write_text(config_content, encoding="utf-8")

        return CallToolResult(content=[TextContent(type="text", text=f"Successfully created .blobify file at {blobify_file}")])
    except Exception as e:
        return CallToolResult(content=[TextContent(type="text", text=f"Error writing .blobify file: {str(e)}")], isError=True)


# Resource definitions (for future expansion)
@server.list_resources()
async def list_resources() -> ListResourcesResult:
    """List available resources."""
    return ListResourcesResult(resources=[])


@server.read_resource()
async def read_resource(uri: str) -> ReadResourceResult:
    """Read a specific resource."""
    return ReadResourceResult(contents=[TextContent(type="text", text=f"Resource not found: {uri}")])


def main():
    """Run the MCP server."""
    parser = argparse.ArgumentParser(description="Blobify MCP Server")
    parser.add_argument("--version", action="version", version=f"{SERVER_NAME} {SERVER_VERSION}")

    args = parser.parse_args()

    # Run the server
    stdio_server(server)


if __name__ == "__main__":
    main()
