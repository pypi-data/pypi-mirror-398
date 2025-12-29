"""Entry point for running the WHOOP MCP server as a module."""

import asyncio
from whoop_sdk.mcp.server import main

if __name__ == "__main__":
    asyncio.run(main())
