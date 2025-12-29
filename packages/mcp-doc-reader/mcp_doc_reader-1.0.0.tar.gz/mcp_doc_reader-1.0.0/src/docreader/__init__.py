"""
MCP Doc Reader - A Model Context Protocol server for reading documents.

Supports reading PDF, Excel (.xlsx, .xls), and Word (.docx) files.
"""

import asyncio
from .server import run_server

__version__ = "1.0.0"

def main():
    """Entry point for the MCP server."""
    asyncio.run(run_server())

__all__ = ["main", "__version__"]
