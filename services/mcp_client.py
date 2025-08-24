"""
MCP (Model Context Protocol) client for tool calling and external service integration.
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
import aiohttp
import websockets

logger = logging.getLogger(__name__)


@dataclass
class MCPTool:
    """Represents an MCP tool."""
    name: str
    description: str
    input_schema: Dict[str, Any]
    handler: Callable


class MCPClient:
    """Client for interacting with MCP servers."""
    
    def __init__(self, server_url: str = "ws://localhost:3000"):
        """Initialize the MCP client.
        
        Args:
            server_url: WebSocket URL of the MCP server
        """
        self.server_url = server_url
        self.websocket = None
        self.tools: Dict[str, MCPTool] = {}
        self.message_id = 0
        
    async def connect(self):
        """Connect to the MCP server."""
        try:
            self.websocket = await websockets.connect(self.server_url)
            logger.info(f"Connected to MCP server at {self.server_url}")
            
            # Initialize the connection
            await self._send_message({
                "jsonrpc": "2.0",
                "id": self._get_next_id(),
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "clientInfo": {
                        "name": "Agentic AI Architect",
                        "version": "1.0.0"
                    }
                }
            })
            
            # Get available tools
            await self._list_tools()
            
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {str(e)}")
            raise
    
    async def disconnect(self):
        """Disconnect from the MCP server."""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
            logger.info("Disconnected from MCP server")
    
    async def _send_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Send a message to the MCP server.
        
        Args:
            message: Message to send
            
        Returns:
            Response from the server
        """
        if not self.websocket:
            raise ConnectionError("Not connected to MCP server")
        
        try:
            await self.websocket.send(json.dumps(message))
            response = await self.websocket.recv()
            return json.loads(response)
        except Exception as e:
            logger.error(f"Failed to send/receive message: {str(e)}")
            raise
    
    def _get_next_id(self) -> int:
        """Get the next message ID."""
        self.message_id += 1
        return self.message_id
    
    async def _list_tools(self):
        """List available tools from the MCP server."""
        try:
            response = await self._send_message({
                "jsonrpc": "2.0",
                "id": self._get_next_id(),
                "method": "tools/list"
            })
            
            if "result" in response and "tools" in response["result"]:
                for tool_info in response["result"]["tools"]:
                    tool = MCPTool(
                        name=tool_info["name"],
                        description=tool_info.get("description", ""),
                        input_schema=tool_info.get("inputSchema", {}),
                        handler=self._create_tool_handler(tool_info["name"])
                    )
                    self.tools[tool.name] = tool
                    
                logger.info(f"Registered {len(self.tools)} MCP tools")
            
        except Exception as e:
            logger.error(f"Failed to list tools: {str(e)}")
    
    def _create_tool_handler(self, tool_name: str) -> Callable:
        """Create a handler for an MCP tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tool handler function
        """
        async def handler(**kwargs):
            return await self._call_tool(tool_name, kwargs)
        
        return handler
    
    async def _call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call an MCP tool.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Arguments for the tool
            
        Returns:
            Tool result
        """
        try:
            response = await self._send_message({
                "jsonrpc": "2.0",
                "id": self._get_next_id(),
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            })
            
            if "result" in response:
                return response["result"]["content"]
            elif "error" in response:
                logger.error(f"Tool {tool_name} failed: {response['error']}")
                return None
            else:
                logger.warning(f"Unexpected response from tool {tool_name}: {response}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to call tool {tool_name}: {str(e)}")
            return None
    
    def get_tool(self, tool_name: str) -> Optional[MCPTool]:
        """Get a tool by name.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            MCPTool if found, None otherwise
        """
        return self.tools.get(tool_name)
    
    def list_available_tools(self) -> List[str]:
        """List names of available tools.
        
        Returns:
            List of tool names
        """
        return list(self.tools.keys())
    
    async def call_tool(self, tool_name: str, **kwargs) -> Any:
        """Call an MCP tool with arguments.
        
        Args:
            tool_name: Name of the tool to call
            **kwargs: Arguments for the tool
            
        Returns:
            Tool result
        """
        tool = self.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found")
        
        return await tool.handler(**kwargs)
    
    async def register_custom_tool(self, tool: MCPTool):
        """Register a custom tool.
        
        Args:
            tool: MCPTool to register
        """
        self.tools[tool.name] = tool
        logger.info(f"Registered custom tool: {tool.name}")
    
    async def health_check(self) -> bool:
        """Check if the MCP server is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            response = await self._send_message({
                "jsonrpc": "2.0",
                "id": self._get_next_id(),
                "method": "ping"
            })
            return "result" in response
        except Exception:
            return False


class MCPToolRegistry:
    """Registry for managing MCP tools."""
    
    def __init__(self):
        self.tools: Dict[str, MCPTool] = {}
    
    def register_tool(self, tool: MCPTool):
        """Register a tool.
        
        Args:
            tool: MCPTool to register
        """
        self.tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")
    
    def get_tool(self, tool_name: str) -> Optional[MCPTool]:
        """Get a tool by name.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            MCPTool if found, None otherwise
        """
        return self.tools.get(tool_name)
    
    def list_tools(self) -> List[str]:
        """List all registered tool names.
        
        Returns:
            List of tool names
        """
        return list(self.tools.keys())


# Example custom tools for the Agentic AI Architect system

async def generate_user_stories_tool(feature_description: str, priority: str, **kwargs) -> str:
    """Generate user stories for a feature.
    
    Args:
        feature_description: Description of the feature
        priority: Priority of the feature
        **kwargs: Additional arguments
        
    Returns:
        Generated user stories in JSON format
    """
    # This would integrate with an LLM to generate stories
    return f"Generated user stories for {feature_description} with priority {priority}"

async def create_ddd_model_tool(domain_description: str, **kwargs) -> str:
    """Create a DDD model for a domain.
    
    Args:
        domain_description: Description of the domain
        **kwargs: Additional arguments
        
    Returns:
        DDD model in Context Mapper DSL format
    """
    # This would integrate with an LLM to generate DDD models
    return f"Generated DDD model for domain: {domain_description}"

async def generate_openapi_spec_tool(api_description: str, **kwargs) -> str:
    """Generate OpenAPI specification.
    
    Args:
        api_description: Description of the API
        **kwargs: Additional arguments
        
    Returns:
        OpenAPI 3.0 specification in JSON format
    """
    # This would integrate with an LLM to generate OpenAPI specs
    return f"Generated OpenAPI spec for: {api_description}"

async def scaffold_spring_boot_tool(service_name: str, package_name: str, **kwargs) -> str:
    """Scaffold a Spring Boot service.
    
    Args:
        service_name: Name of the service
        package_name: Java package name
        **kwargs: Additional arguments
        
    Returns:
        Path to the generated Spring Boot project
    """
    # This would generate Spring Boot project structure
    return f"Scaffolded Spring Boot service: {service_name} in package {package_name}"

async def create_helm_chart_tool(service_name: str, image: str, **kwargs) -> str:
    """Create a Helm chart for a service.
    
    Args:
        service_name: Name of the service
        image: Docker image name
        **kwargs: Additional arguments
        
    Returns:
        Path to the generated Helm chart
    """
    # This would generate Helm chart structure
    return f"Created Helm chart for service: {service_name} with image {image}"


# Register default tools
def register_default_tools(registry: MCPToolRegistry):
    """Register default tools with the registry.
    
    Args:
        registry: MCPToolRegistry instance
    """
    tools = [
        MCPTool(
            name="generate_user_stories",
            description="Generate user stories for a feature",
            input_schema={
                "type": "object",
                "properties": {
                    "feature_description": {"type": "string"},
                    "priority": {"type": "string", "enum": ["Low", "Medium", "High", "Critical"]}
                },
                "required": ["feature_description", "priority"]
            },
            handler=generate_user_stories_tool
        ),
        MCPTool(
            name="create_ddd_model",
            description="Create a DDD model for a domain",
            input_schema={
                "type": "object",
                "properties": {
                    "domain_description": {"type": "string"}
                },
                "required": ["domain_description"]
            },
            handler=create_ddd_model_tool
        ),
        MCPTool(
            name="generate_openapi_spec",
            description="Generate OpenAPI 3.0 specification",
            input_schema={
                "type": "object",
                "properties": {
                    "api_description": {"type": "string"}
                },
                "required": ["api_description"]
            },
            handler=generate_openapi_spec_tool
        ),
        MCPTool(
            name="scaffold_spring_boot",
            description="Scaffold a Spring Boot service",
            input_schema={
                "type": "object",
                "properties": {
                    "service_name": {"type": "string"},
                    "package_name": {"type": "string"}
                },
                "required": ["service_name", "package_name"]
            },
            handler=scaffold_spring_boot_tool
        ),
        MCPTool(
            name="create_helm_chart",
            description="Create a Helm chart for a service",
            input_schema={
                "type": "object",
                "properties": {
                    "service_name": {"type": "string"},
                    "image": {"type": "string"}
                },
                "required": ["service_name", "image"]
            },
            handler=create_helm_chart_tool
        )
    ]
    
    for tool in tools:
        registry.register_tool(tool)
