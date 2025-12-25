"""MCP server discovery.

On runtime startup:
- Connect to MCP server
- Discover tools, resources, prompts
- Normalize results with robust type handling
- Cache in memory
"""

import logging
from typing import List, Dict, Any, Optional
from runtime.transport.base import Transport
from runtime.errors import DiscoveryError
from schemas.mcp_types import MCPTool, MCPResource, MCPPrompt, MCPServerInfo
from runtime.utils import (
    safe_str,
    safe_dict,
    safe_list,
    normalize_json_response,
    safe_get
)


class Discoverer:
    """Discovers MCP server capabilities.
    
    Mandatory explicit discovery phase.
    No lazy discovery.
    """
    
    def __init__(self, transport: Transport):
        """Initialize discoverer with transport.
        
        Args:
            transport: Connected transport instance
        """
        self.transport = transport
        self._tools: List[MCPTool] = []
        self._resources: List[MCPResource] = []
        self._prompts: List[MCPPrompt] = []
        self._server_info: MCPServerInfo | None = None
        self._logger = logging.getLogger(__name__)
    
    async def discover_all(self, client_info: Dict[str, str]) -> MCPServerInfo:
        """Perform full discovery of MCP server.
        
        Args:
            client_info: Client information dict
            
        Returns:
            MCPServerInfo: Server information
            
        Raises:
            DiscoveryError: If discovery fails
        """
        try:
            # Initialize session
            init_result = await self.transport.initialize(client_info)
            
            # Normalize init result
            init_result = normalize_json_response(init_result)
            
            # Extract server info with robust handling
            server_info_raw = safe_get(init_result, "serverInfo") or safe_get(init_result, "server_info") or {}
            server_info_raw = safe_dict(server_info_raw, {})
            
            self._server_info = MCPServerInfo(
                name=safe_str(server_info_raw.get("name") or safe_get(init_result, "serverName") or "unknown", "unknown"),
                version=safe_str(server_info_raw.get("version") or safe_get(init_result, "serverVersion") or "unknown", "unknown"),
                protocol_version=safe_str(init_result.get("protocolVersion") or init_result.get("protocol_version") or "unknown", "unknown")
            )
            
            # Send initialized notification (no response expected)
            await self.transport.send_notification("notifications/initialized")
            
            # Discover tools
            await self._discover_tools()
            
            # Discover resources
            await self._discover_resources()
            
            # Discover prompts
            await self._discover_prompts()
            
            return self._server_info
        except Exception as e:
            if isinstance(e, DiscoveryError):
                raise
            raise DiscoveryError(f"Discovery failed: {e}") from e
    
    async def _discover_tools(self) -> None:
        """Discover available tools with robust type handling."""
        try:
            result = await self.transport.send_request("tools/list")
            result = normalize_json_response(result)
            
            # Handle various response formats
            tools_list = safe_get(result, "tools") or safe_get(result, "toolList") or []
            if not isinstance(tools_list, list):
                tools_list = safe_list(tools_list, [])
            
            self._tools = []
            for tool_data in tools_list:
                try:
                    # Normalize tool data
                    tool_data = safe_dict(tool_data, {})
                    
                    # Extract fields with multiple fallback names
                    name = safe_str(tool_data.get("name") or tool_data.get("toolName") or "", "")
                    if not name:
                        self._logger.warning("Skipping tool with missing name")
                        continue
                    
                    description = tool_data.get("description") or tool_data.get("desc")
                    description = safe_str(description) if description else None
                    
                    input_schema = tool_data.get("inputSchema") or tool_data.get("input_schema") or tool_data.get("schema") or {}
                    input_schema = safe_dict(input_schema, {})
                    
                    tool = MCPTool(
                        name=name,
                        description=description,
                        input_schema=input_schema
                    )
                    self._tools.append(tool)
                except (KeyError, ValueError) as e:
                    self._logger.warning(f"Invalid tool data: {e}, skipping tool")
                    continue
        except Exception as e:
            if isinstance(e, DiscoveryError):
                raise
            raise DiscoveryError(f"Failed to discover tools: {e}") from e
    
    async def _discover_resources(self) -> None:
        """Discover available resources with robust type handling."""
        try:
            result = await self.transport.send_request("resources/list")
            result = normalize_json_response(result)
            
            # Handle various response formats
            resources_list = safe_get(result, "resources") or safe_get(result, "resourceList") or []
            if not isinstance(resources_list, list):
                resources_list = safe_list(resources_list, [])
            
            self._resources = []
            for resource_data in resources_list:
                try:
                    # Normalize resource data
                    resource_data = safe_dict(resource_data, {})
                    
                    # Extract fields with multiple fallback names
                    uri = safe_str(resource_data.get("uri") or resource_data.get("url") or "", "")
                    if not uri:
                        self._logger.warning("Skipping resource with missing URI")
                        continue
                    
                    name = safe_str(resource_data.get("name") or resource_data.get("resourceName") or "", "")
                    if not name:
                        name = uri  # Use URI as name if name missing
                    
                    description = resource_data.get("description") or resource_data.get("desc")
                    description = safe_str(description) if description else None
                    
                    mime_type = resource_data.get("mimeType") or resource_data.get("mime_type") or resource_data.get("contentType")
                    mime_type = safe_str(mime_type) if mime_type else None
                    
                    resource = MCPResource(
                        uri=uri,
                        name=name,
                        description=description,
                        mime_type=mime_type
                    )
                    self._resources.append(resource)
                except (KeyError, ValueError) as e:
                    self._logger.warning(f"Invalid resource data: {e}, skipping resource")
                    continue
        except Exception as e:
            if isinstance(e, DiscoveryError):
                raise
            raise DiscoveryError(f"Failed to discover resources: {e}") from e
    
    async def _discover_prompts(self) -> None:
        """Discover available prompts with robust type handling."""
        try:
            result = await self.transport.send_request("prompts/list")
            result = normalize_json_response(result)
            
            # Handle various response formats
            prompts_list = safe_get(result, "prompts") or safe_get(result, "promptList") or []
            if not isinstance(prompts_list, list):
                prompts_list = safe_list(prompts_list, [])
            
            self._prompts = []
            for prompt_data in prompts_list:
                try:
                    # Normalize prompt data
                    prompt_data = safe_dict(prompt_data, {})
                    
                    # Extract fields with multiple fallback names
                    name = safe_str(prompt_data.get("name") or prompt_data.get("promptName") or "", "")
                    if not name:
                        self._logger.warning("Skipping prompt with missing name")
                        continue
                    
                    description = prompt_data.get("description") or prompt_data.get("desc")
                    description = safe_str(description) if description else None
                    
                    arguments = prompt_data.get("arguments") or prompt_data.get("args") or prompt_data.get("parameters") or []
                    arguments = safe_list(arguments, [])
                    
                    prompt = MCPPrompt(
                        name=name,
                        description=description,
                        arguments=arguments
                    )
                    self._prompts.append(prompt)
                except (KeyError, ValueError) as e:
                    self._logger.warning(f"Invalid prompt data: {e}, skipping prompt")
                    continue
        except Exception as e:
            if isinstance(e, DiscoveryError):
                raise
            raise DiscoveryError(f"Failed to discover prompts: {e}") from e
    
    @property
    def tools(self) -> List[MCPTool]:
        """Get discovered tools."""
        return self._tools.copy()
    
    @property
    def resources(self) -> List[MCPResource]:
        """Get discovered resources."""
        return self._resources.copy()
    
    @property
    def prompts(self) -> List[MCPPrompt]:
        """Get discovered prompts."""
        return self._prompts.copy()
    
    @property
    def server_info(self) -> MCPServerInfo | None:
        """Get server information."""
        return self._server_info

