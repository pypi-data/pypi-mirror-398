#!/usr/bin/env python3
"""MCP Server for capturing screenshots from OCP CAD Viewer."""

import asyncio
import base64
import logging
import tempfile
import os
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ImageContent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ocp-viewer-mcp")

# Create server instance
server = Server("ocp-viewer")

# Thread pool for running sync code
executor = ThreadPoolExecutor(max_workers=1)


def capture_screenshot_sync(port: int, filepath: str) -> bytes:
    """Synchronously capture screenshot using ocp_vscode."""
    from ocp_vscode import save_screenshot
    
    # Remove file if it exists
    if os.path.exists(filepath):
        os.unlink(filepath)
    
    logger.info(f"Calling save_screenshot({filepath}, port={port})")
    save_screenshot(filepath, port=port, polling=True)
    
    # Additional wait to ensure file is fully written
    time.sleep(0.5)
    
    # Check if file was created
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Screenshot was not saved to {filepath}")
    
    # Read the file
    with open(filepath, "rb") as f:
        return f.read()


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="capture_ocp_screenshot",
            description="Capture a screenshot of the OCP CAD Viewer. Use this to see the current 3D model being displayed.",
            inputSchema={
                "type": "object",
                "properties": {
                    "port": {
                        "type": "integer",
                        "description": "The port number where OCP viewer is running",
                        "default": 3939
                    },
                    "wait_ms": {
                        "type": "integer",
                        "description": "Milliseconds to wait for the 3D scene to render",
                        "default": 1000
                    }
                },
                "required": []
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent | ImageContent]:
    """Handle tool calls."""
    if name != "capture_ocp_screenshot":
        return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    port = arguments.get("port", 3939)
    wait_ms = arguments.get("wait_ms", 1000)
    
    # Create temp file path
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, f"ocp_screenshot_{int(time.time())}.png")
    
    try:
        # Initial wait for any pending render
        await asyncio.sleep(wait_ms / 1000)
        
        # Run the synchronous capture in a thread pool
        loop = asyncio.get_event_loop()
        screenshot_bytes = await loop.run_in_executor(
            executor, 
            capture_screenshot_sync, 
            port, 
            temp_path
        )
        
        # Encode as base64
        screenshot_b64 = base64.standard_b64encode(screenshot_bytes).decode("utf-8")
        
        logger.info(f"Screenshot captured ({len(screenshot_bytes)} bytes)")
        
        return [
            ImageContent(
                type="image",
                data=screenshot_b64,
                mimeType="image/png"
            )
        ]
        
    except ImportError as e:
        logger.error(f"ocp_vscode not available: {e}")
        return [TextContent(
            type="text",
            text=f"Error: ocp_vscode is not installed. Details: {e}"
        )]
    except FileNotFoundError as e:
        logger.error(f"Screenshot file not found: {e}")
        return [TextContent(
            type="text",
            text=f"Screenshot was not saved. Make sure the OCP viewer is open and has a model displayed. Error: {e}"
        )]
    except Exception as e:
        logger.error(f"Error capturing screenshot: {e}", exc_info=True)
        return [TextContent(
            type="text",
            text=f"Error capturing screenshot: {str(e)}"
        )]
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except:
                pass


async def async_main():
    """Run the MCP server (async entry point)."""
    logger.info("Starting OCP Viewer MCP Server...")
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main():
    """Run the MCP server (sync entry point for CLI)."""
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
