# MCP Server Implementation for Time Tool
# Model Context Protocol (MCP) Server that provides current time functionality
# with optional timezone support

import time
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List, Union


class MCPServer:
    """
    Model Context Protocol (MCP) Server implementation
    
    This server provides a tool to get the current time with optional timezone support.
    It follows the MCP protocol for tool registration and execution.
    """
    
    def __init__(self):
        """
        Initialize the MCP Server with core configuration and tool registry
        """
        self.implementation = {
            "name": "time-tool-mcp-server",
            "version": "1.0.0",
            "description": "MCP Server providing current time functionality with timezone support"
        }
        
        self.tools: Dict[str, Dict[str, Any]] = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        """
        Register default tools provided by this MCP Server
        """
        # Register current time tool
        self.register_tool(
            name="get_current_time",
            description="获取当前时间，支持可选的时区配置",
            parameters={
                "type": "object",
                "properties": {
                    "timezone_offset": {
                        "type": "number",
                        "description": "UTC时区偏移量（小时），例如UTC+8为8，UTC-5为-5",
                        "default": 0
                    },
                    "timezone_name": {
                        "type": "string",
                        "description": "时区名称（用于显示）",
                        "default": "UTC"
                    }
                },
                "required": []
            },
            handler=self._handle_get_current_time
        )
    
    def register_tool(
        self, 
        name: str, 
        description: str, 
        parameters: Dict[str, Any],
        handler: callable
    ):
        """
        Register a new tool with the MCP Server
        
        Args:
            name: Unique name of the tool
            description: Description of what the tool does
            parameters: JSON Schema defining the tool's parameters
            handler: Callable function to execute when the tool is invoked
        """
        self.tools[name] = {
            "name": name,
            "description": description,
            "parameters": parameters,
            "handler": handler
        }
    
    def _handle_get_current_time(self, **kwargs) -> Dict[str, Any]:
        """
        Handler for the get_current_time tool
        
        Args:
            timezone_offset: UTC offset in hours (default: 0)
            timezone_name: Timezone name for display (default: "UTC")
            
        Returns:
            Dictionary containing current time information
        """
        # Get parameters with defaults
        timezone_offset = kwargs.get("timezone_offset", 0)
        timezone_name = kwargs.get("timezone_name", None)
        
        # Get current UTC time
        utc_now = datetime.now(timezone.utc)
        
        # Apply timezone offset if specified
        tz = timezone(timedelta(hours=timezone_offset))
        local_time = utc_now.astimezone(tz)
        
        # Use provided timezone name or generate from offset
        if timezone_name is None:
            timezone_name = f"UTC{timezone_offset:+03.1f}"
        
        return {
            "current_time": local_time.isoformat(),
            "time_zone": timezone_name,
            "formatted_time": local_time.strftime("%Y-%m-%d %H:%M:%S"),
            "timestamp": time.time(),
            "utc_time": utc_now.isoformat(),
            "timezone_offset": timezone_offset
        }
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """
        List all registered tools with their metadata
        
        Returns:
            List of tool specifications
        """
        return [{
            "name": tool["name"],
            "description": tool["description"],
            "parameters": tool["parameters"]
        } for tool in self.tools.values()]
    
    def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a registered tool with the provided parameters
        
        Args:
            tool_name: Name of the tool to execute
            **kwargs: Parameters to pass to the tool
            
        Returns:
            Tool execution result with status and output
        """
        # Check if tool exists
        if tool_name not in self.tools:
            return {
                "status": "error",
                "error": f"Tool '{tool_name}' not found",
                "available_tools": list(self.tools.keys())
            }
        
        try:
            # Execute the tool handler
            tool = self.tools[tool_name]
            result = tool["handler"](**kwargs)
            
            return {
                "status": "success",
                "tool": tool_name,
                "result": result,
                "timestamp": time.time()
            }
        except Exception as e:
            return {
                "status": "error",
                "tool": tool_name,
                "error": str(e),
                "timestamp": time.time()
            }
    
    def get_server_info(self) -> Dict[str, Any]:
        """
        Get server implementation information
        
        Returns:
            Server implementation details
        """
        return self.implementation


def main():
    """
    Main function for console script entry point
    """
    # Create MCP Server instance
    mcp_server = MCPServer()
    
    print("=== MCP Server 初始化完成 ===")
    print(f"服务器: {mcp_server.implementation['name']} v{mcp_server.implementation['version']}")
    print(f"描述: {mcp_server.implementation['description']}")
    
    # 列出所有可用工具
    print("\n=== 可用工具列表 ===")
    for tool in mcp_server.list_tools():
        print(f"\n工具名称: {tool['name']}")
        print(f"工具描述: {tool['description']}")
        print(f"参数定义: {tool['parameters']}")
    
    # 测试工具调用 - 场景1: 默认UTC时间
    print("\n" + "="*50)
    print("测试场景1: 获取默认UTC时间")
    result = mcp_server.execute_tool("get_current_time")
    if result["status"] == "success":
        print("执行成功:")
        for key, value in result["result"].items():
            print(f"  {key}: {value}")
    
    # 测试工具调用 - 场景2: UTC+8时间（北京时间）
    print("\n" + "="*50)
    print("测试场景2: 获取UTC+8时间（北京时间）")
    result = mcp_server.execute_tool(
        "get_current_time",
        timezone_offset=8,
        timezone_name="Asia/Shanghai"
    )
    if result["status"] == "success":
        print("执行成功:")
        for key, value in result["result"].items():
            print(f"  {key}: {value}")
    
    # 测试工具调用 - 场景3: UTC-5时间（纽约时间）
    print("\n" + "="*50)
    print("测试场景3: 获取UTC-5时间（纽约时间）")
    result = mcp_server.execute_tool(
        "get_current_time",
        timezone_offset=-5,
        timezone_name="America/New_York"
    )
    if result["status"] == "success":
        print("执行成功:")
        for key, value in result["result"].items():
            print(f"  {key}: {value}")
    
    print("\n=== MCP Server 演示完成 ===")
    print("可以通过调用 server.execute_tool('get_current_time', **kwargs) 来使用时间工具")

# Example usage and testing
if __name__ == "__main__":
    main()