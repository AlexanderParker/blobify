"""
MCP (Model Context Protocol) server for blobify.

This module provides an MCP server interface for blobify, allowing AI agents to:
- Analyze project filesystem structures
- Generate and update .blobify configuration files
- Run blobify to package codebases for AI consumption
- Access blobify resources and metadata

The server exposes tools for filesystem analysis and blobify execution,
resources for configuration and metadata access, and prompts for
AI-assisted configuration generation.
"""

from .server import create_mcp_server

__all__ = ["create_mcp_server"]
