"""WHOOP MCP Server - Exposes WHOOP fitness data as MCP tools."""

import asyncio
from whoop_sdk.mcp.server import main as async_main


def main():
    """Entry point for the whoop-mcp command."""
    asyncio.run(async_main())


__all__ = ["main"]
