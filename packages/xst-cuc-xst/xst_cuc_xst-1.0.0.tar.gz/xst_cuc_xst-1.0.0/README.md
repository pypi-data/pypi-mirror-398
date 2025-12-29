# mcp-time-server

[![PyPI version](https://badge.fury.io/py/mcp-time-server.svg)](https://badge.fury.io/py/mcp-time-server)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Model Context Protocol (MCP) Server implementation that provides a tool to get the current time with optional timezone support.

## Overview

The `mcp-time-server` is a lightweight MCP Server implementation that follows the Model Context Protocol (MCP) guidelines. It provides a clean API for tool registration and execution, with a focus on simplicity and ease of use.

## Features

- **Current Time Tool**: `get_current_time` tool to retrieve current time information
- **Timezone Support**: Optional timezone offset and timezone name parameters
- **Clean API**: Proper tool registration and execution system
- **Error Handling**: Comprehensive error handling for invalid tools and parameters
- **Well Documented**: Clear comments and documentation throughout
- **Zero Dependencies**: No external dependencies required

## Installation

```bash
pip install mcp-time-server
```

## Usage

### Basic Usage

```python
from mcp_time_server import MCPServer

# Create MCP Server instance
server = MCPServer()

# Execute get_current_time tool with default UTC time
result = server.execute_tool("get_current_time")
print(result)
```

### With Timezone Parameters

```python
# Get time in UTC+8 (Asia/Shanghai)
result = server.execute_tool(
    "get_current_time",
    timezone_offset=8,
    timezone_name="Asia/Shanghai"
)

# Get time in UTC-5 (America/New_York)
result = server.execute_tool(
    "get_current_time",
    timezone_offset=-5,
    timezone_name="America/New_York"
)
```

### Available Tools

```python
# List all available tools
tools = server.list_tools()
print(tools)
```

### Server Information

```python
# Get server implementation information
server_info = server.get_server_info()
print(server_info)
```

## Tool Parameters

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `timezone_offset` | number | UTC offset in hours (e.g., 8 for UTC+8, -5 for UTC-5) | 0 |
| `timezone_name` | string | Timezone name for display purposes | Generated from offset |

## Response Format

```json
{
  "current_time": "2025-12-26T11:16:58.143220+00:00",
  "time_zone": "UTC+0.0",
  "formatted_time": "2025-12-26 11:16:58",
  "timestamp": 1766747818.143357,
  "utc_time": "2025-12-26T11:16:58.143220+00:00",
  "timezone_offset": 0
}
```

## Console Script

The package provides a console script to run the server demonstration:

```bash
mcp-time-server
```

This will show the server initialization, available tools, and test cases for different timezone configurations.

## Implementation Details

- The server follows the MCP protocol for tool registration and execution
- Tools are registered with JSON Schema defining their parameters
- Tool handlers are called with the provided parameters
- Comprehensive error handling ensures graceful failure
- The implementation is modular and extensible for adding new tools

## Requirements

- Python 3.7+
- No additional dependencies required

## License

MIT License

## Project Structure

```
mcp-time-server/
├── mcp_time_server/
│   ├── __init__.py    # Package metadata and exports
│   └── server.py      # Main server implementation
├── setup.py           # Package configuration
├── README.md          # This file
└── LICENSE            # License file
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

If you encounter any issues or have questions, please open an issue on the [GitHub repository](https://github.com/yourusername/mcp-time-server).
