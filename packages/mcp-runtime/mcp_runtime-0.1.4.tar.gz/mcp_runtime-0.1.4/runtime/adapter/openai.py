"""OpenAI adapter for MCP Runtime.

Converts MCP tools to OpenAI function calling format.
Robust type handling and error recovery.
"""

import json
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


class OpenAIAdapter(LLMAdapter):
    """OpenAI adapter for function calling.
    
    Converts MCP tools to OpenAI function format.
    Parses OpenAI tool calls with robust type handling.
    """
    
    def __init__(self):
        """Initialize OpenAI adapter."""
        self._logger = logging.getLogger(__name__)
    
    def convert_tools_to_llm_format(self, tools: List[MCPTool]) -> List[Dict[str, Any]]:
        """Convert MCP tools to OpenAI function format.
        
        Args:
            tools: List of MCP tools
            
        Returns:
            List of OpenAI function definitions
        """
        functions = []
        for tool in tools:
            function_def = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.input_schema
                }
            }
            functions.append(function_def)
        return functions
    
    def parse_tool_call(self, llm_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse tool calls from OpenAI response with robust handling.
        
        Args:
            llm_response: OpenAI API response (ChatCompletion or dict)
            
        Returns:
            List of tool call dicts with 'name' and 'arguments' keys
        """
        tool_calls = []
        
        # Normalize response
        llm_response = normalize_json_response(llm_response)
        
        try:
            # Handle both old and new OpenAI API formats
            choices = safe_list(llm_response.get("choices", []), [])
            if not choices:
                return tool_calls
            
            message = safe_dict(choices[0].get("message", {}), {})
            tool_call_list = safe_list(message.get("tool_calls", []), [])
            
            for tool_call in tool_call_list:
                tool_call = safe_dict(tool_call, {})
                function = safe_dict(tool_call.get("function", {}), {})
                arguments = function.get("arguments")
                
                # Parse arguments if it's a string (JSON)
                if isinstance(arguments, str):
                    try:
                        arguments = json.loads(arguments)
                    except json.JSONDecodeError:
                        arguments = {}
                elif arguments is None:
                    arguments = {}
                else:
                    arguments = safe_dict(arguments, {})
                
                name = safe_str(function.get("name") or function.get("functionName") or "", "")
                if not name:
                    continue
                
                tool_calls.append({
                    "id": safe_str(tool_call.get("id"), ""),
                    "name": name,
                    "arguments": arguments
                })
        except Exception as e:
            self._logger.warning(f"Failed to parse OpenAI tool calls: {e}")
        
        return tool_calls
    
    def format_tool_result(self, tool_name: str, result: ToolExecutionResult) -> Dict[str, Any]:
        """Format tool execution result for OpenAI with robust handling.
        
        Args:
            tool_name: Name of the tool
            result: ToolExecutionResult
            
        Returns:
            OpenAI tool result format
        """
        tool_name = safe_str(tool_name, "")
        
        # Convert MCP content to text with robust handling
        content_parts = []
        if not isinstance(result.content, list):
            result.content = safe_list(result.content, [])
        
        for item in result.content:
            if not isinstance(item, dict):
                item = safe_dict(item, {})
            
            item_type = safe_str(item.get("type") or item.get("contentType") or "", "").lower()
            
            if item_type == "text":
                text = safe_str(item.get("text") or item.get("content") or item.get("value") or "", "")
                if text:
                    content_parts.append(text)
            elif item_type == "image":
                # OpenAI doesn't support images in tool results directly
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
            "role": "tool",
            "name": tool_name,
            "content": content
        }

