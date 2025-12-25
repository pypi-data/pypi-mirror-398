"""Anthropic Claude adapter for MCP Runtime.

Converts MCP tools to Claude function calling format.
Robust type handling and error recovery.
"""

import logging
from typing import Any, Dict, List
from runtime.adapter.base import LLMAdapter
from schemas.mcp_types import MCPTool, ToolExecutionResult
from runtime.utils import (
    safe_str,
    safe_dict,
    safe_list,
    normalize_json_response
)


class ClaudeAdapter(LLMAdapter):
    """Anthropic Claude adapter for function calling.
    
    Converts MCP tools to Claude function format.
    Parses Claude tool calls with robust type handling.
    """
    
    def __init__(self):
        """Initialize Claude adapter."""
        self._logger = logging.getLogger(__name__)
    
    def convert_tools_to_llm_format(self, tools: List[MCPTool]) -> List[Dict[str, Any]]:
        """Convert MCP tools to Claude function format.
        
        Args:
            tools: List of MCP tools
            
        Returns:
            List of Claude tool definitions
        """
        tool_definitions = []
        for tool in tools:
            tool_def = {
                "name": tool.name,
                "description": tool.description or "",
                "input_schema": tool.input_schema
            }
            tool_definitions.append(tool_def)
        return tool_definitions
    
    def parse_tool_call(self, llm_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse tool calls from Claude response with robust handling.
        
        Args:
            llm_response: Claude API response (dict or response object)
            
        Returns:
            List of tool call dicts with 'name' and 'arguments' keys
        """
        tool_calls = []
        
        # Normalize response
        llm_response = normalize_json_response(llm_response)
        
        try:
            content = safe_list(llm_response.get("content", []), [])
            
            for item in content:
                if not isinstance(item, dict):
                    item = safe_dict(item, {})
                
                item_type = safe_str(item.get("type") or item.get("contentType") or "", "").lower()
                
                if item_type == "tool_use":
                    name = safe_str(item.get("name") or item.get("toolName") or "", "")
                    if not name:
                        continue
                    
                    # Handle arguments/input with multiple fallbacks
                    arguments = item.get("input") or item.get("arguments") or item.get("parameters") or {}
                    arguments = safe_dict(arguments, {})
                    
                    tool_calls.append({
                        "id": safe_str(item.get("id"), ""),
                        "name": name,
                        "arguments": arguments
                    })
        except Exception as e:
            self._logger.warning(f"Failed to parse Claude tool calls: {e}")
        
        return tool_calls
    
    def format_tool_result(self, tool_name: str, result: ToolExecutionResult) -> Dict[str, Any]:
        """Format tool execution result for Claude with robust handling.
        
        Args:
            tool_name: Name of the tool
            result: ToolExecutionResult
            
        Returns:
            Claude tool result format
        """
        tool_name = safe_str(tool_name, "")
        
        # Convert MCP content to text with robust handling
        content_parts = []
        if not isinstance(result.content, list):
            result.content = safe_list(result.content, [])
        
        tool_use_id = None
        for item in result.content:
            if not isinstance(item, dict):
                item = safe_dict(item, {})
            
            # Extract tool_use_id if present
            if not tool_use_id:
                tool_use_id = safe_str(item.get("id") or item.get("tool_use_id"), "")
            
            item_type = safe_str(item.get("type") or item.get("contentType") or "", "").lower()
            
            if item_type == "text":
                text = safe_str(item.get("text") or item.get("content") or item.get("value") or "", "")
                if text:
                    content_parts.append(text)
            elif item_type == "image":
                image_data = safe_str(item.get("data") or item.get("imageData") or "", "")
                content_parts.append(f"[Image: {image_data[:50]}...]" if len(image_data) > 50 else f"[Image: {image_data}]")
            else:
                # Unknown type - try to extract text
                text = safe_str(item.get("text") or item.get("content") or item.get("value") or str(item), "")
                if text:
                    content_parts.append(text)
        
        content = "\n".join(content_parts) if content_parts else ""
        
        if result.is_error:
            content = f"Error: {content}" if content else "Error occurred"
        
        return {
            "type": "tool_result",
            "tool_use_id": tool_use_id,
            "content": content,
            "is_error": result.is_error
        }

