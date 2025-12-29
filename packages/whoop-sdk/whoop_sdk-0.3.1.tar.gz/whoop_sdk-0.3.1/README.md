# Whoop SDK

A modern Python SDK for the WHOOP Developer API (v2). Easily integrate WHOOP fitness data into your Python applications with simple authentication and intuitive API calls. Includes an MCP server for AI assistant integration (Claude, Cursor, etc.).

> ** Disclaimer**: This is an unofficial SDK and is not affiliated with, endorsed by, or supported by WHOOP. Use at your own risk. The WHOOP team is not responsible for any issues that may arise from using this SDK. 

## Prerequisites

- Python 3.10 or higher
- A WHOOP developer account and application

## Getting Started

### 1. Create a WHOOP Developer Application

Before using this SDK, you'll need to create a developer application on WHOOP's platform:

1. Visit the [WHOOP Developer Portal](https://developer.whoop.com/)
2. Sign up or log in to your WHOOP account
3. Create a new application
4. Note down your **Client ID** and **Client Secret**
5. Add BOTH redirect URIs to your application:
   - `http://localhost:8080` (for automated OAuth flow)
   - `https://www.google.com` (fallback for manual authorization)

The SDK will request the following scopes:
- `offline` - For refresh token access
- `read:profile` - Read user profile information
- `read:recovery` - Read recovery data
- `read:sleep` - Read sleep data
- `read:workout` - Read workout data
- `read:cycles` - Read cycle data
- `read:body_measurement` - Read body measurements

### 2. Installation

Install the SDK from PyPI:

```bash
pip install whoop-sdk
```

### 3. Configuration & Authentication

The SDK supports two ways to provide your credentials:

#### Option 1: Environment Variables (Recommended)
```bash
export WHOOP_CLIENT_ID="your_client_id_here"
export WHOOP_CLIENT_SECRET="your_client_secret_here"
```

#### Option 2: Interactive Setup
If no environment variables are found, the SDK will prompt you for credentials on first run. Credentials are automatically saved to your home directory in `.whoop_sdk/settings.json` after interactive setup.

> - **Windows**: `C:\Users\YourUsername\.whoop_sdk\`
> - **macOS**: `/Users/YourUsername/.whoop_sdk/`
> - **Linux**: `/home/YourUsername/.whoop_sdk/`

### 4. OAuth Authentication Flow

When you call `whoop.login()`, the SDK uses an **automated OAuth flow** that requires no manual copy-paste:

1. The SDK starts a localhost server on port 8080 to capture the OAuth callback
2. Your browser automatically opens to the WHOOP authorization page
3. After you approve access, the authorization completes automatically
4. You can close the browser window - no need to copy any codes!

**Manual Fallback**: If the automated flow is unavailable (e.g., port 8080 is in use), the SDK automatically falls back to a manual method where you'll copy the authorization code from the redirect URL. This backup method uses `https://www.google.com` as the redirect URI.

Important: Ensure BOTH redirect URIs are whitelisted in your WHOOP app settings: `http://localhost:8080` and `https://www.google.com`.

The SDK automatically manages token refresh, so you only need to complete the OAuth flow once. Tokens are saved to `.whoop_sdk/config.json` for future use and automatically rotated for you.

### 5. Quick Start

Here's a basic example to get you started:

```python
from whoop_sdk import Whoop

# Initialize and authenticate
whoop = Whoop()
whoop.login()

# Your tokens are now saved and ready to use!
```

## API Usage Examples

### Get User Profile
```python
# Get basic profile information
profile = whoop.get_profile()
print(f"Hello {profile['first_name']} {profile['last_name']}!")
print(f"User ID: {profile['user_id']}")
print(f"Email: {profile['email']}")
```

### Get Body Measurements
```python
# Body measurements (single object, not paginated)
body = whoop.get_body_measurements()
print(f"Height: {body.get('height_meter')} m")
print(f"Weight: {body.get('weight_kilogram')} kg")
print(f"Max Heart Rate: {body.get('max_heart_rate')} bpm")
```

## Pagination

All list-style endpoints support pagination with the following defaults:

- **Default page size**: 10 records per page (WHOOP API default)
- **Default max pages**: 3 pages maximum (30 records total)
- **Maximum page size**: 25 records per page (WHOOP API limit)

**Important**: Even when you specify a date range, the default pagination limits still apply. For example, if you request data for more than a 30-day period, you'll only get the first 30 records (3 pages × 10 records) unless you explicitly set `max_pages=None` or increase the `limit` parameter.

**Parameters**:
- `limit`: Controls page size (1-25, default: 10)
- `max_pages`: Maximum number of pages to fetch (default: 3, use `None` for unlimited)
- `start` / `end`: ISO8601 date range filters (optional)

### Get Recovery Data
```python
# Example with limit parameter
recovery = whoop.get_recovery(limit=25, max_pages=1)  # Max page size, but only 1 page
print(f"Found {len(recovery.get('records', []))} recovery records") # Will return 25 latest recovery records
```

### Get Sleep Data
```python
from whoop_sdk import Whoop

whoop = Whoop()
whoop.login()

# Example with max_pages parameter
sleep_data = whoop.get_sleep(max_pages=5)  # Fetch up to 5 pages
print(f"Found {len(sleep_data.get('records', []))} sleep records") # Will return up to last 50 records
```
#### Get Single Sleep by ID
```python
sleep_id = sleep_data.get('records', [])[0].get('id')
first_sleep = whoop.get_sleep_by_id(sleep_id)
print(first_sleep)
```

### Get Workout Data
```python
from datetime import datetime, timedelta
# Note: Even with a date range, default pagination applies: 10 records per page, max 3 pages (30 records max total)
end_date = datetime.now()
start_date = end_date - timedelta(days=14)

workout_data = whoop.get_workouts(
    start=start_date.isoformat() + "Z",
    end=end_date.isoformat() + "Z"
)
print(f"Found {len(workout_data.get('records', []))} workout records")
```

#### Get Single Workout by ID
```python
workout_id = workout_data.get('records', [])[0].get('id')
first_workout = whoop.get_workout_by_id(workout_id)
print(first_workout)
```


### Get Cycles
```python
# Get cycles with default settings
cycle_data = whoop.get_cycles()
print(f"Found {len(cycles.get('records', []))} cycle records") # Should return last 30 records, but not. Inquiry open with Whoop team
```

#### Get Single Cycle by ID
```python
cycle_id = cycle_data.get('records', [])[0].get('id')
first_cycle = whoop.get_cycle_by_id(cycle_id)
print(first_cycle)
```

### Get Sleep and Recovery by Cycle ID

Fetch the sleep or recovery associated with a given cycle:

```python
from whoop_sdk import Whoop

whoop = Whoop()
whoop.login()

# First, get a cycle ID
cycles = whoop.get_cycles()
cycle_id = cycles['records'][0]['id'] if cycles.get('records') else None

if cycle_id:
    # Sleep for a specific cycle
    sleep_for_cycle = whoop.get_sleep_by_cycle_id(cycle_id)
    print(f"Sleep score: {sleep_for_cycle.get('score', {}).get('sleep_performance_percentage')}")
    
    # Recovery for a specific cycle
    recovery_for_cycle = whoop.get_recovery_by_cycle_id(cycle_id)
    print(f"Recovery score: {recovery_for_cycle.get('score', {}).get('recovery_score')}")
```

## MCP Server

The SDK includes an MCP (Model Context Protocol) server that allows AI assistants like Claude and Cursor to access your WHOOP data directly.

### Running the MCP Server

```bash
# Using uvx (no installation required)
uvx whoop-mcp

# Or if installed locally
uv run whoop-mcp

# Or as a Python module
python -m whoop_sdk.mcp
```

### Configuration

The MCP server uses the same credentials as the SDK (`~/.whoop_sdk/config.json`). Make sure you've authenticated with the SDK first by running `whoop.login()`.

#### Claude Desktop

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "whoop": {
      "command": "uvx",
      "args": ["--from", "whoop-sdk", "whoop-mcp"]
    }
  }
}
```

> **Note**: If Claude Desktop can't find `uvx`, use the full path (run `which uvx` to find it).

#### Cursor

Add to your Cursor MCP config (`.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "whoop": {
      "command": "uvx",
      "args": ["--from", "whoop-sdk", "whoop-mcp"]
    }
  }
}
```

### Available Tools

| Tool | Description |
|------|-------------|
| `whoop_get_recovery` | Get recovery data with optional date range |
| `whoop_get_sleep` | Get sleep data with optional date range |
| `whoop_get_workouts` | Get workout data with optional date range |
| `whoop_get_cycles` | Get physiological cycle data with optional date range |
| `whoop_get_profile` | Get user profile information |
| `whoop_get_body_measurements` | Get body measurements (height, weight, max HR) |

All data tools support optional `start_date`, `end_date` (ISO format), and `limit` parameters.

## Next Steps

Upcoming features we're working on:

- **Rate Limit Support**: Automatic handling of API rate limits with intelligent retry logic and exponential backoff. The SDK will automatically detect rate limit responses (429) and retry requests with appropriate delays.

- **Webhook Integration**: Cloud-deployable webhook receiver that listens for WHOOP events and automatically fetches new data as it becomes available. Perfect for real-time data processing and serverless deployments.

- **Enhanced Error Handling**: Comprehensive error handling with custom exception classes for different error types (authentication errors, API errors, network errors, validation errors). Better error messages with context and improved handling of edge cases throughout the SDK.

Stay tuned for updates!

## Open Source

This project is open source and welcomes contributions from the community! 

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Repository

- **Homepage**: https://github.com/ericfflynn/whoop-sdk


## Documentation

More detailed documentation and API reference coming soon. For now, check out the source code in the `whoop_sdk` package for available methods and functionality.
