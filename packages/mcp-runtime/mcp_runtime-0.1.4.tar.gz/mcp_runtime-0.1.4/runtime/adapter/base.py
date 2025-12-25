"""Base adapter interface for LLM integrations.

Adapters must:
- Convert MCP tools → LLM tool/function schema
- Parse LLM tool calls
- Invoke execution engine

Adapters must NOT:
- Add memory
- Add agent loops
- Modify tool behavior
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List
from schemas.mcp_types import MCPTool


class LLMAdapter(ABC):
    """Abstract base class for LLM adapters.
    
    Adapters bridge MCP tools/resources/prompts with LLM APIs.
    No magic. No inference. Strict conversion only.
    """
    
    @abstractmethod
    def convert_tools_to_llm_format(self, tools: List[MCPTool]) -> List[Dict[str, Any]]:
        """Convert MCP tools to LLM tool/function schema.
        
        Args:
            tools: List of MCP tools
            
        Returns:
            List of LLM tool definitions
        """
        pass
    
    @abstractmethod
    def parse_tool_call(self, llm_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse tool calls from LLM response.
        
        Args:
            llm_response: LLM API response
            
        Returns:
            List of tool call dicts with 'name' and 'arguments' keys
        """
        pass
    
    @abstractmethod
    def format_tool_result(self, tool_name: str, result: Any) -> Dict[str, Any]:
        """Format tool execution result for LLM.
        
        Args:
            tool_name: Name of the tool
            result: ToolExecutionResult
            
        Returns:
            Formatted result dict for LLM
        """
        pass

