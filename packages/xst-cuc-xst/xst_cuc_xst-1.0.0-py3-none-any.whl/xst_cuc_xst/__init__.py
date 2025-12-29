# MCP Time Server Package
# Model Context Protocol (MCP) Server providing current time functionality

from .server import MCPServer

__version__ = "1.0.0"
__author__ = "Your Name"
__description__ = "MCP Server implementation providing current time functionality with timezone support"

__all__ = [
    "MCPServer",
    "__version__",
    "__author__",
    "__description__"
]