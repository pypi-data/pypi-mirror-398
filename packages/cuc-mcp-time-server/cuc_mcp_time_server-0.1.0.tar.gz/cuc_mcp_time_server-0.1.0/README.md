# MCP Time Server

A Model Context Protocol (MCP) time server that provides current time information. This server implements the MCP protocol and offers a tool to get the current time with optional timezone support.

## Features

- Provides current time information via MCP protocol
- Supports optional timezone parameter
- Easy to install and use
- Lightweight implementation

## Installation

You can install MCP Time Server using pip:

```bash
pip install mcp-time-server
```

## Usage

### Running the Server

To start the MCP Time Server, simply run:

```bash
python -m time_server
```

Or use the command-line entry point:

```bash
mcp-time-server
```

### Using the Server

The server provides a tool called `get_current_time` that can be called via the MCP protocol.

#### Example using an MCP client:

```python
import requests
import json

# Example using JSON-RPC over HTTP
url = "http://localhost:8000"

# Request without timezone
payload = {
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
        "name": "get_current_time",
        "arguments": {}
    },
    "id": 1
}

response = requests.post(url, json=payload)
print(response.json())

# Request with timezone
payload_with_tz = {
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
        "name": "get_current_time",
        "arguments": {
            "timezone": "Asia/Shanghai"
        }
    },
    "id": 1
}

response = requests.post(url, json=payload_with_tz)
print(response.json())
```

## API Reference

### `get_current_time(timezone: Optional[str] = None)`

Get the current time.

- **Parameters:**
  - `timezone` (Optional[str]): Timezone string (e.g., "Asia/Shanghai", "America/New_York"). If not provided, uses system default timezone.

- **Returns:**
  - Formatted time string in the format: "YYYY-MM-DD HH:MM:SS.SSSSSS TIMEZONE"

- **Example:**
  - `get_current_time()` → "2023-06-15 14:30:45.123456 UTC"
  - `get_current_time("Asia/Shanghai")` → "2023-06-15 22:30:45.123456 CST"

## Configuration

The server can be configured using command-line arguments or environment variables. Refer to the documentation for more details.

## Requirements

- Python 3.7+
- pytz
- fastmcp

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
