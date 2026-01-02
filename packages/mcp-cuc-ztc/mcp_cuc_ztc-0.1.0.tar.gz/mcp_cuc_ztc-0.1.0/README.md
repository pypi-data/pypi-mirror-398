# MCP Time Server

An MCP Server that provides a tool to get the current time with optional timezone support.

## Features

- Provides a `get_current_time` tool to retrieve the current time
- Supports optional timezone parameter
- Simple and lightweight implementation
- Built using the Model Context Protocol (MCP)

## Installation

```bash
pip install mcp-time-server
```

## Usage

### Running the Server

```bash
mcp-time-server
```

This will start the MCP Server using the STDIO transport, which is suitable for local process communication.

### Using the `get_current_time` Tool

The server exposes a single tool called `get_current_time` that can be used by MCP clients.

#### Parameters

- `timezone` (optional): A timezone string, e.g., "Asia/Shanghai", "America/New_York"
  - If not provided, the system's default timezone will be used

#### Return Value

A formatted string representing the current time in the format: `YYYY-MM-DD HH:MM:SS.SSSSSS TIMEZONE`

#### Examples

```python
# Get current time in system default timezone
result = await mcp_client.call_tool("get_current_time")
# Example output: "2023-12-25 13:45:30.123456 EST"

# Get current time in a specific timezone
result = await mcp_client.call_tool("get_current_time", timezone="Asia/Shanghai")
# Example output: "2023-12-26 02:45:30.123456 CST"
```

## Project Structure

```
mcp-time-server/
├── mcp_time_server/
│   ├── __init__.py      # Package initialization
│   └── main.py          # Main server implementation
├── pyproject.toml       # Project configuration
├── README.md            # This file
├── LICENSE              # License file
└── .gitignore           # Git ignore file
```

## License

MIT License - see the LICENSE file for details.

## About MCP

The Model Context Protocol (MCP) is an open-source standard for connecting AI applications to external systems. For more information, visit [modelcontextprotocol.io](https://modelcontextprotocol.io).
