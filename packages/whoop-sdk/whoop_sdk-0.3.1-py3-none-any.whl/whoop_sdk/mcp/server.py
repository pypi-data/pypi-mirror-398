"""WHOOP MCP Server - Exposes WHOOP fitness data as MCP tools."""

import json
import logging
from typing import Any

from mcp.server import Server
from mcp.types import Tool, TextContent

from whoop_sdk import Whoop

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("whoop-mcp")

# Initialize the WHOOP client (will use existing credentials)
try:
    whoop_client = Whoop()
    logger.info("WHOOP client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize WHOOP client: {e}")
    whoop_client = None

# Create the MCP server
app = Server("whoop-mcp")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List all available WHOOP tools."""
    return [
        Tool(
            name="whoop_get_recovery",
            description="Get WHOOP recovery data. Recovery scores indicate how ready your body is for strain. Includes HRV, resting heart rate, SpO2, and more.",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "Start date in ISO format (YYYY-MM-DD). Optional."
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date in ISO format (YYYY-MM-DD). Optional."
                    },
                    "limit": {
                        "type": "number",
                        "description": "Maximum number of records to return. Default is 25.",
                        "default": 25
                    }
                }
            }
        ),
        Tool(
            name="whoop_get_sleep",
            description="Get WHOOP sleep data. Includes sleep performance, efficiency, stages, respiratory rate, and more.",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "Start date in ISO format (YYYY-MM-DD). Optional."
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date in ISO format (YYYY-MM-DD). Optional."
                    },
                    "limit": {
                        "type": "number",
                        "description": "Maximum number of records to return. Default is 25.",
                        "default": 25
                    }
                }
            }
        ),
        Tool(
            name="whoop_get_workouts",
            description="Get WHOOP workout data. Includes strain, heart rate stats, calories burned, and activity type.",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "Start date in ISO format (YYYY-MM-DD). Optional."
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date in ISO format (YYYY-MM-DD). Optional."
                    },
                    "limit": {
                        "type": "number",
                        "description": "Maximum number of records to return. Default is 25.",
                        "default": 25
                    }
                }
            }
        ),
        Tool(
            name="whoop_get_cycles",
            description="Get WHOOP physiological cycle data. A cycle represents a 24-hour period of strain and recovery.",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "Start date in ISO format (YYYY-MM-DD). Optional."
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date in ISO format (YYYY-MM-DD). Optional."
                    },
                    "limit": {
                        "type": "number",
                        "description": "Maximum number of records to return. Default is 25.",
                        "default": 25
                    }
                }
            }
        ),
        Tool(
            name="whoop_get_profile",
            description="Get WHOOP user profile information (user ID, email, first name, last name).",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="whoop_get_body_measurements",
            description="Get user body measurements including height, weight, and max heart rate.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""
    if not whoop_client:
        return [TextContent(
            type="text",
            text="Error: WHOOP client not initialized. Please ensure you have valid credentials in ~/.whoop_sdk/"
        )]

    try:
        start_date = arguments.get("start_date")
        end_date = arguments.get("end_date")
        limit = arguments.get("limit", 25)

        if name == "whoop_get_recovery":
            data = whoop_client.get_recovery(start=start_date, end=end_date, limit=limit)
        elif name == "whoop_get_sleep":
            data = whoop_client.get_sleep(start=start_date, end=end_date, limit=limit)
        elif name == "whoop_get_workouts":
            data = whoop_client.get_workouts(start=start_date, end=end_date, limit=limit)
        elif name == "whoop_get_cycles":
            data = whoop_client.get_cycles(start=start_date, end=end_date, limit=limit)
        elif name == "whoop_get_profile":
            data = whoop_client.get_profile()
        elif name == "whoop_get_body_measurements":
            data = whoop_client.get_body_measurements()
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

        return [TextContent(type="text", text=json.dumps(data, indent=2))]

    except Exception as e:
        logger.error(f"Error executing {name}: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """Run the MCP server."""
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        logger.info("WHOOP MCP Server starting...")
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )
