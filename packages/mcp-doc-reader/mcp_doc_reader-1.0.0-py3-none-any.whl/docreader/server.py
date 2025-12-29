"""
MCP Server implementation for document reading.
"""

import asyncio
import os
import sys
import logging

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

from .readers.pdf_reader import get_pdf_content
from .readers.excel_reader import get_excel_content
from .readers.word_reader import get_word_content

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_encoding():
    """Configure UTF-8 encoding for cross-platform compatibility."""
    if sys.platform == "win32":
        try:
            # Reconfigure all standard streams for UTF-8 on Windows
            sys.stdin.reconfigure(encoding='utf-8', errors='replace')
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
            os.environ['PYTHONIOENCODING'] = 'utf-8'
        except Exception as e:
            logger.warning(f"Failed to reconfigure stdio streams: {e}")


# Initialize server
server = Server("DocReader")


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available document reading tools."""
    return [
        types.Tool(
            name="read_pdf",
            description="Read text content from a PDF file.",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Absolute path to the PDF file."
                    }
                },
                "required": ["file_path"]
            }
        ),
        types.Tool(
            name="read_excel",
            description="Read content from an Excel file (.xlsx or .xls).",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Absolute path to the Excel file."
                    }
                },
                "required": ["file_path"]
            }
        ),
        types.Tool(
            name="read_word",
            description="Read text content from a Word file (.docx).",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Absolute path to the Word file."
                    }
                },
                "required": ["file_path"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool calls for document reading."""
    logger.info(f"Tool called: {name} with args: {arguments}")
    
    try:
        if not arguments:
            raise ValueError("Missing arguments")
        
        file_path = arguments.get("file_path")
        if not file_path:
            raise ValueError("Missing file_path argument")

        content = ""
        # Run synchronous file IO in a thread to prevent blocking the event loop
        if name == "read_pdf":
            content = await asyncio.to_thread(get_pdf_content, file_path)
        elif name == "read_excel":
            content = await asyncio.to_thread(get_excel_content, file_path)
        elif name == "read_word":
            content = await asyncio.to_thread(get_word_content, file_path)
        else:
            raise ValueError(f"Unknown tool: {name}")
            
        logger.info(f"Tool {name} execution successful. Content length: {len(content)}")
        return [types.TextContent(type="text", text=content)]

    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}")
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


async def run_server():
    """Run the MCP server."""
    logger.info("Starting DocReader MCP Server...")
    
    # Setup encoding for cross-platform compatibility
    setup_encoding()
    
    # Run the server using stdin/stdout
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="DocReader",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )
