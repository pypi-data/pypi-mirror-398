"""WHOOP MCP Server - Exposes WHOOP fitness data as MCP tools."""

import json
import logging
from datetime import datetime
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


def format_date(date_str: str | None) -> str | None:
    """Validate and format date string to ISO format."""
    if not date_str:
        return None
    try:
        # Try to parse the date
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.isoformat()
    except ValueError:
        raise ValueError(f"Invalid date format: {date_str}. Use ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)")


def format_response(data: dict, data_type: str) -> str:
    """Format API response into a readable string."""
    records = data.get("records", [])

    if not records:
        return f"No {data_type} data found."

    # Create a summary
    summary = f"Found {len(records)} {data_type} record(s):\n\n"

    # Format each record based on type
    for i, record in enumerate(records, 1):
        summary += f"Record {i}:\n"

        if data_type == "recovery":
            score = record.get("score", {})
            summary += f"  Recovery Score: {score.get('recovery_score', 'N/A')}\n"
            summary += f"  HRV: {score.get('hrv_rmssd_milli', 'N/A')} ms\n"
            summary += f"  Resting HR: {score.get('resting_heart_rate', 'N/A')} bpm\n"
            summary += f"  SpO2: {score.get('spo2_percentage', 'N/A')}%\n"

        elif data_type == "sleep":
            score = record.get("score", {})
            summary += f"  Sleep Performance: {score.get('sleep_performance_percentage', 'N/A')}%\n"
            summary += f"  Sleep Efficiency: {score.get('sleep_efficiency_percentage', 'N/A')}%\n"
            summary += f"  Respiratory Rate: {score.get('respiratory_rate', 'N/A')} rpm\n"

        elif data_type == "workout":
            score = record.get("score", {})
            summary += f"  Strain: {score.get('strain', 'N/A')}\n"
            summary += f"  Average HR: {score.get('average_heart_rate', 'N/A')} bpm\n"
            summary += f"  Max HR: {score.get('max_heart_rate', 'N/A')} bpm\n"
            summary += f"  Kilojoules: {score.get('kilojoule', 'N/A')}\n"

        elif data_type == "cycle":
            score = record.get("score", {})
            summary += f"  Strain: {score.get('strain', 'N/A')}\n"
            summary += f"  Kilojoules: {score.get('kilojoule', 'N/A')}\n"

        summary += f"  Created: {record.get('created_at', 'N/A')}\n\n"

    # Add raw JSON at the end
    summary += "\n--- Raw JSON Data ---\n"
    summary += json.dumps(data, indent=2)

    return summary


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
                        "description": "Start date in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS). Optional."
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS). Optional."
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
                        "description": "Start date in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS). Optional."
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS). Optional."
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
                        "description": "Start date in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS). Optional."
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS). Optional."
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
                        "description": "Start date in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS). Optional."
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS). Optional."
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
        # Extract common parameters
        start_date = arguments.get("start_date")
        end_date = arguments.get("end_date")
        limit = arguments.get("limit", 25)

        # Validate dates if provided
        if start_date:
            start_date = format_date(start_date)
        if end_date:
            end_date = format_date(end_date)

        # Route to appropriate handler
        if name == "whoop_get_recovery":
            data = whoop_client.get_recovery(start=start_date, end=end_date, limit=limit)
            response = format_response(data, "recovery")

        elif name == "whoop_get_sleep":
            data = whoop_client.get_sleep(start=start_date, end=end_date, limit=limit)
            response = format_response(data, "sleep")

        elif name == "whoop_get_workouts":
            data = whoop_client.get_workouts(start=start_date, end=end_date, limit=limit)
            response = format_response(data, "workout")

        elif name == "whoop_get_cycles":
            data = whoop_client.get_cycles(start=start_date, end=end_date, limit=limit)
            response = format_response(data, "cycle")

        elif name == "whoop_get_profile":
            data = whoop_client.get_profile()
            response = f"WHOOP User Profile:\n\n{json.dumps(data, indent=2)}"

        elif name == "whoop_get_body_measurements":
            data = whoop_client.get_body_measurements()
            response = f"Body Measurements:\n\n{json.dumps(data, indent=2)}"

        else:
            response = f"Unknown tool: {name}"

        return [TextContent(type="text", text=response)]

    except Exception as e:
        logger.error(f"Error executing {name}: {e}")
        return [TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]


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
