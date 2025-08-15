"""
Entry point for running the blobify MCP server.

This module provides the command-line interface for starting the MCP server
with various transport options.
"""

import argparse
import asyncio
import sys

from .server import create_mcp_server


def main():
    """Main entry point for the MCP server."""
    parser = argparse.ArgumentParser(description="Blobify MCP Server - Provides Model Context Protocol interface for blobify")
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http"],
        default="stdio",
        help="Transport method to use (default: stdio)",
    )
    parser.add_argument("--host", default="localhost", help="Host to bind to for HTTP transport (default: localhost)")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to for HTTP transport (default: 8000)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    # Create the MCP server
    mcp = create_mcp_server()

    try:
        if args.transport == "stdio":
            # Run with stdio transport (default)
            mcp.run(transport="stdio")
        elif args.transport == "streamable-http":
            # Run with streamable HTTP transport
            mcp.run(transport="streamable-http", host=args.host, port=args.port)
    except KeyboardInterrupt:
        print("\nShutting down MCP server...", file=sys.stderr)
    except Exception as e:
        print(f"Error running MCP server: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
