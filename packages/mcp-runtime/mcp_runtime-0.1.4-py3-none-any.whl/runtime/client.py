"""Simple client wrapper for MCP Runtime.

Provides a clean, easy-to-use API for developers to integrate MCP servers
with their LLM models.
"""

from typing import Any, Dict, List, Optional, Union
from runtime.runtime import MCPRuntime
from runtime.transport.base import Transport
from runtime.transport.stdio import StdioTransport
from runtime.transport.http_sse import HttpSSETransport
from runtime.adapter.base import LLMAdapter
from runtime.adapter.openai import OpenAIAdapter
from runtime.adapter.gemini import GeminiAdapter
from runtime.adapter.claude import ClaudeAdapter
from runtime.errors import MCPRuntimeError
from runtime.blueprint import MCPBlueprint, BlueprintManager
from schemas.mcp_types import MCPServerInfo, MCPTool, MCPResource, MCPPrompt, ToolExecutionResult
from runtime.utils import normalize_url


class MCPClient:
    """Simple client for connecting to MCP servers and executing tools, resources, and prompts.
    
    This is the main entry point for developers to use MCP Runtime.
    
    Example:
        ```python
        from runtime import MCPClient
        
        # Connect to a local MCP server
        client = MCPClient.local(
            command=["python", "-m", "my_mcp_server"],
            adapter="openai"
        )
        
        await client.connect()
        
        # Get tools for your LLM
        tools = client.get_tools()
        
        # Execute a tool
        result = await client.call_tool("calculator", {"operation": "add", "a": 5, "b": 3})
        
        await client.disconnect()
        ```
    """
    
    def __init__(self, transport: Transport, adapter: Union[str, LLMAdapter]):
        """Initialize MCP client.
        
        Args:
            transport: Transport instance (StdioTransport or HttpSSETransport)
            adapter: Adapter name ("openai", "gemini", "claude") or LLMAdapter instance
        """
        if isinstance(adapter, str):
            adapter_map = {
                "openai": OpenAIAdapter,
                "gemini": GeminiAdapter,
                "claude": ClaudeAdapter,
            }
            if adapter not in adapter_map:
                raise ValueError(f"Unknown adapter: {adapter}. Choose from: {list(adapter_map.keys())}")
            adapter = adapter_map[adapter]()
        
        self._runtime = MCPRuntime(transport, adapter)
        self._client_info = {"name": "mcp-client", "version": "1.0.0"}
        self._blueprint: Optional[MCPBlueprint] = None
        self._llm_tools_cache: Optional[List[Dict[str, Any]]] = None
    
    @classmethod
    def local(
        cls,
        command: List[str],
        adapter: Union[str, LLMAdapter] = "openai",
        env: Optional[Dict[str, str]] = None,
        client_name: str = "mcp-client",
        client_version: str = "1.0.0"
    ) -> "MCPClient":
        """Create client for local MCP server (stdio transport).
        
        Args:
            command: Command to run MCP server (e.g., ["python", "-m", "my_server"])
            adapter: Adapter name or instance
            env: Optional environment variables for subprocess
            client_name: Client name for MCP handshake
            client_version: Client version for MCP handshake
            
        Returns:
            MCPClient instance
        """
        transport = StdioTransport(command, env)
        client = cls(transport, adapter)
        client._client_info = {"name": client_name, "version": client_version}
        return client
    
    @classmethod
    def remote(
        cls,
        base_url: str,
        adapter: Union[str, LLMAdapter] = "openai",
        headers: Optional[Dict[str, str]] = None,
        client_name: str = "mcp-client",
        client_version: str = "1.0.0"
    ) -> "MCPClient":
        """Create client for remote MCP server (HTTP/SSE transport).
        
        Args:
            base_url: Base URL of MCP server (e.g., "https://example.com/mcp" or "https://example.com/mcp/sse")
                     Will automatically normalize and handle various formats
            adapter: Adapter name or instance
            headers: Optional HTTP headers
            client_name: Client name for MCP handshake
            client_version: Client version for MCP handshake
            
        Returns:
            MCPClient instance
        """
        # Normalize URL - handles various formats automatically
        try:
            normalized_url = normalize_url(base_url)
        except Exception as e:
            raise ValueError(f"Invalid base URL: {base_url}") from e
        
        transport = HttpSSETransport(normalized_url, headers)
        client = cls(transport, adapter)
        client._client_info = {"name": client_name, "version": client_version}
        return client
    
    async def connect(self, use_blueprint: Optional[str] = None) -> MCPServerInfo:
        """Connect to MCP server and discover capabilities.
        
        Args:
            use_blueprint: Optional path to blueprint file to load instead of discovering.
                          If provided, capabilities will be loaded from file and transport
                          will still connect for tool execution.
        
        Returns:
            Server information
            
        Raises:
            MCPRuntimeError: If connection fails
        """
        if use_blueprint:
            # Load blueprint from file
            self._blueprint = BlueprintManager.load(use_blueprint)
            server_info, tools, resources, prompts = self._blueprint.to_runtime_capabilities()
            
            # Connect transport (needed for tool execution)
            await self._runtime.transport.connect()
            
            # Initialize runtime with blueprint data
            from runtime.execution.tool_executor import ToolExecutor
            from runtime.execution.resource_resolver import ResourceResolver
            from runtime.execution.prompt_expander import PromptExpander
            
            self._runtime._server_info = server_info
            self._runtime._tools = tools
            self._runtime._resources = resources
            self._runtime._prompts = prompts
            self._runtime.tool_executor = ToolExecutor(self._runtime.transport)
            self._runtime.resource_resolver = ResourceResolver(self._runtime.transport)
            self._runtime.prompt_expander = PromptExpander(self._runtime.transport)
            self._runtime._started = True
            
            # Clear LLM tools cache
            self._llm_tools_cache = None
            
            return server_info
        else:
            # Normal discovery
            server_info = await self._runtime.start(self._client_info)
            # Clear LLM tools cache after discovery
            self._llm_tools_cache = None
            return server_info
    
    async def disconnect(self) -> None:
        """Disconnect from MCP server."""
        await self._runtime.stop()
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Get tools in LLM format.
        
        Cached for performance - tools are only converted once per session.
        
        Returns:
            List of tool definitions ready for LLM API
        """
        if self._llm_tools_cache is None:
            self._llm_tools_cache = self._runtime.get_llm_tools()
        return self._llm_tools_cache
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> ToolExecutionResult:
        """Execute a tool call.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments
            
        Returns:
            ToolExecutionResult with execution result
            
        Raises:
            MCPRuntimeError: If execution fails
        """
        return await self._runtime.execute_tool_call(tool_name, arguments)
    
    async def read_resource(
        self,
        resource_name: str,
        uri_arguments: Dict[str, str]
    ) -> Dict[str, Any]:
        """Read a resource.
        
        Args:
            resource_name: Name of the resource
            uri_arguments: Arguments to fill URI template
            
        Returns:
            Resource content
            
        Raises:
            MCPRuntimeError: If resource read fails
        """
        if not self._runtime.resource_resolver:
            raise MCPRuntimeError("Runtime not connected")
        
        # Find resource
        resource = None
        for r in self._runtime.resources:
            if r.name == resource_name:
                resource = r
                break
        
        if not resource:
            raise ValueError(f"Resource not found: {resource_name}")
        
        return await self._runtime.resource_resolver.read(resource, uri_arguments)
    
    async def expand_prompt(
        self,
        prompt_name: str,
        arguments: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Expand a prompt template.
        
        Args:
            prompt_name: Name of the prompt
            arguments: Arguments for prompt template
            
        Returns:
            Expanded prompt messages
            
        Raises:
            MCPRuntimeError: If prompt expansion fails
        """
        if not self._runtime.prompt_expander:
            raise MCPRuntimeError("Runtime not connected")
        
        # Find prompt
        prompt = None
        for p in self._runtime.prompts:
            if p.name == prompt_name:
                prompt = p
                break
        
        if not prompt:
            raise ValueError(f"Prompt not found: {prompt_name}")
        
        return await self._runtime.prompt_expander.expand(prompt, arguments)
    
    def parse_tool_calls(self, llm_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse tool calls from LLM response.
        
        Args:
            llm_response: LLM API response
            
        Returns:
            List of tool call dicts with 'name' and 'arguments' keys
        """
        return self._runtime.parse_llm_tool_calls(llm_response)
    
    def format_tool_result(self, tool_name: str, result: ToolExecutionResult) -> Dict[str, Any]:
        """Format tool execution result for LLM.
        
        Args:
            tool_name: Name of the tool
            result: Tool execution result
            
        Returns:
            Formatted result dict for LLM
        """
        return self._runtime.format_tool_result(tool_name, result)
    
    @property
    def server_info(self) -> Optional[MCPServerInfo]:
        """Get server information."""
        return self._runtime.server_info
    
    @property
    def tools(self) -> List[MCPTool]:
        """Get discovered tools."""
        return self._runtime.tools
    
    @property
    def resources(self) -> List[MCPResource]:
        """Get discovered resources."""
        return self._runtime.resources
    
    @property
    def prompts(self) -> List[MCPPrompt]:
        """Get discovered prompts."""
        return self._runtime.prompts
    
    @property
    def is_connected(self) -> bool:
        """Check if client is connected."""
        return self._runtime.is_started
    
    def save_blueprint(self, file_path: Optional[str] = None) -> str:
        """Save current capabilities as blueprint to file.
        
        Args:
            file_path: Optional path to save blueprint. If not provided,
                      uses default path based on server name.
        
        Returns:
            Path where blueprint was saved
            
        Raises:
            MCPRuntimeError: If not connected or no capabilities discovered
        """
        if not self._runtime.is_started:
            raise MCPRuntimeError("Not connected. Call connect() first.")
        
        if not self._runtime.server_info:
            raise MCPRuntimeError("No server info available")
        
        blueprint = MCPBlueprint.from_capabilities(
            self._runtime.server_info,
            self._runtime.tools,
            self._runtime.resources,
            self._runtime.prompts
        )
        
        if file_path is None:
            file_path = BlueprintManager.get_default_path(
                self._runtime.server_info.name
            )
        
        BlueprintManager.save(blueprint, file_path)
        self._blueprint = blueprint
        
        return file_path
    
    def load_blueprint(self, file_path: str) -> None:
        """Load blueprint from file and set capabilities.
        
        Note: This only loads the blueprint data. You still need to call
        connect() with use_blueprint parameter to use it.
        
        Args:
            file_path: Path to blueprint file
        """
        self._blueprint = BlueprintManager.load(file_path)
    
    @property
    def blueprint(self) -> Optional[MCPBlueprint]:
        """Get current blueprint if available."""
        return self._blueprint

