"""Main MCP Runtime.

Runtime Flow (must match exactly):
1. Runtime start
2. Connect transport
3. Discovery phase
4. Expose tools to LLM
5. LLM response
6. If tool call → execute tool
7. Return result
8. Repeat

No hidden logic.
"""

import asyncio
from typing import Any, Dict, List, Optional
from runtime.transport.base import Transport
from runtime.discovery.discoverer import Discoverer
from runtime.execution.tool_executor import ToolExecutor
from runtime.execution.resource_resolver import ResourceResolver
from runtime.execution.prompt_expander import PromptExpander
from runtime.adapter.base import LLMAdapter
from runtime.errors import MCPRuntimeError
from schemas.mcp_types import (
    MCPServerInfo,
    MCPTool,
    MCPResource,
    MCPPrompt,
    ToolExecutionResult
)


class MCPRuntime:
    """MCP Runtime - Infrastructure-level runtime for consuming MCP servers.
    
    Strict. Boring. Explicit. Correct.
    """
    
    def __init__(self, transport: Transport, adapter: LLMAdapter):
        """Initialize MCP Runtime.
        
        Args:
            transport: Transport instance (not yet connected)
            adapter: LLM adapter instance
        """
        self.transport = transport
        self.adapter = adapter
        
        # Discovery components
        self.discoverer: Optional[Discoverer] = None
        
        # Execution components
        self.tool_executor: Optional[ToolExecutor] = None
        self.resource_resolver: Optional[ResourceResolver] = None
        self.prompt_expander: Optional[PromptExpander] = None
        
        # Discovered capabilities (cached)
        self._server_info: Optional[MCPServerInfo] = None
        self._tools: List[MCPTool] = []
        self._resources: List[MCPResource] = []
        self._prompts: List[MCPPrompt] = []
        
        self._started = False
    
    async def start(self, client_info: Dict[str, str]) -> MCPServerInfo:
        """Start runtime.
        
        Flow:
        1. Connect transport
        2. Discovery phase
        3. Initialize execution components
        
        Args:
            client_info: Client information dict
            
        Returns:
            MCPServerInfo: Server information
            
        Raises:
            MCPRuntimeError: If startup fails
        """
        if self._started:
            raise MCPRuntimeError("Runtime already started")
        
        try:
            # Step 1: Connect transport
            await self.transport.connect()
            
            # Step 2: Discovery phase
            self.discoverer = Discoverer(self.transport)
            self._server_info = await self.discoverer.discover_all(client_info)
            
            # Cache discovered capabilities
            self._tools = self.discoverer.tools
            self._resources = self.discoverer.resources
            self._prompts = self.discoverer.prompts
            
            # Step 3: Initialize execution components
            self.tool_executor = ToolExecutor(self.transport)
            self.resource_resolver = ResourceResolver(self.transport)
            self.prompt_expander = PromptExpander(self.transport)
            
            self._started = True
            
            return self._server_info
        except Exception as e:
            if isinstance(e, MCPRuntimeError):
                raise
            raise MCPRuntimeError(f"Runtime startup failed: {e}") from e
    
    async def stop(self) -> None:
        """Stop runtime and disconnect transport."""
        if not self._started:
            return
        
        try:
            await self.transport.disconnect()
        finally:
            self._started = False
            self.discoverer = None
            self.tool_executor = None
            self.resource_resolver = None
            self.prompt_expander = None
    
    def get_llm_tools(self) -> List[Dict[str, Any]]:
        """Get tools in LLM format.
        
        Returns:
            List of tool definitions in LLM adapter format
        """
        if not self._started:
            raise MCPRuntimeError("Runtime not started")
        
        return self.adapter.convert_tools_to_llm_format(self._tools)
    
    async def execute_tool_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> ToolExecutionResult:
        """Execute a tool call.
        
        Args:
            tool_name: Name of tool to execute
            arguments: Tool arguments
            
        Returns:
            ToolExecutionResult: Execution result
            
        Raises:
            MCPRuntimeError: If execution fails
        """
        if not self._started or not self.tool_executor:
            raise MCPRuntimeError("Runtime not started")
        
        # Find tool
        tool = self.tool_executor.find_tool(tool_name, self._tools)
        if not tool:
            raise MCPRuntimeError(f"Tool not found: {tool_name}")
        
        # Execute
        return await self.tool_executor.execute(tool, arguments)
    
    def parse_llm_tool_calls(self, llm_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse tool calls from LLM response.
        
        Args:
            llm_response: LLM API response
            
        Returns:
            List of tool call dicts
        """
        return self.adapter.parse_tool_call(llm_response)
    
    def format_tool_result(
        self,
        tool_name: str,
        result: ToolExecutionResult
    ) -> Dict[str, Any]:
        """Format tool execution result for LLM.
        
        Args:
            tool_name: Name of the tool
            result: Tool execution result
            
        Returns:
            Formatted result dict for LLM
        """
        return self.adapter.format_tool_result(tool_name, result)
    
    @property
    def server_info(self) -> Optional[MCPServerInfo]:
        """Get server information."""
        return self._server_info
    
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
    def is_started(self) -> bool:
        """Check if runtime is started."""
        return self._started

