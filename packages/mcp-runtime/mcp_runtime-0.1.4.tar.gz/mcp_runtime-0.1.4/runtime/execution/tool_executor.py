"""Tool execution engine.

Execution flow:
LLM tool call → smart type coercion → schema validation → MCP execute request → raw result → return to LLM

Rules:
- Smart type coercion before validation (handles string->int, float->int, etc.)
- Schema mismatch = hard error (after coercion)
- Return results unmodified
"""

import json
import logging
from typing import Any, Dict, Optional
from jsonschema import validate, ValidationError as JSONSchemaValidationError
from runtime.transport.base import Transport
from runtime.errors import ExecutionError, ValidationError
from schemas.mcp_types import MCPTool, ToolExecutionResult
from runtime.utils import (
    coerce_to_schema_type,
    safe_dict,
    safe_list,
    safe_get
)


class ToolExecutor:
    """Executes MCP tools.
    
    Smart type coercion before validation. Handles various data type formats.
    """
    
    def __init__(self, transport: Transport):
        """Initialize tool executor.
        
        Args:
            transport: Connected transport instance
        """
        self.transport = transport
        self._logger = logging.getLogger(__name__)
    
    def _coerce_arguments(self, arguments: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        """Coerce arguments to match schema types.
        
        Handles common type mismatches:
        - String numbers -> integers/floats
        - Float integers -> integers
        - String booleans -> booleans
        - etc.
        
        Args:
            arguments: Raw arguments dict
            schema: JSON schema
            
        Returns:
            Coerced arguments dict
        """
        if not isinstance(arguments, dict):
            arguments = safe_dict(arguments, {})
        
        if not isinstance(schema, dict):
            return arguments
        
        properties = schema.get("properties", {})
        coerced = {}
        
        for key, value in arguments.items():
            if key in properties:
                prop_schema = properties[key]
                prop_type = prop_schema.get("type")
                
                # Coerce based on schema type
                if prop_type:
                    coerced_value = coerce_to_schema_type(value, prop_type, prop_schema)
                    coerced[key] = coerced_value
                else:
                    # No type specified, use as-is
                    coerced[key] = value
            else:
                # Key not in schema - include anyway (might be additionalProperties)
                coerced[key] = value
        
        return coerced
    
    async def execute(
        self,
        tool: MCPTool,
        arguments: Dict[str, Any]
    ) -> ToolExecutionResult:
        """Execute a tool with given arguments.
        
        Args:
            tool: Tool to execute
            arguments: Tool arguments (from LLM)
            
        Returns:
            ToolExecutionResult: Execution result (unmodified)
            
        Raises:
            ValidationError: If arguments don't match schema (after coercion)
            ExecutionError: If execution fails
        """
        # Ensure arguments is a dict
        if not isinstance(arguments, dict):
            arguments = safe_dict(arguments, {})
        
        # Coerce arguments to match schema types
        try:
            coerced_args = self._coerce_arguments(arguments, tool.input_schema)
        except Exception as e:
            self._logger.warning(f"Type coercion failed for tool '{tool.name}': {e}, using original arguments")
            coerced_args = arguments
        
        # Validate coerced arguments against schema
        try:
            validate(instance=coerced_args, schema=tool.input_schema)
        except JSONSchemaValidationError as e:
            # Try original arguments if coercion failed validation
            if coerced_args != arguments:
                try:
                    validate(instance=arguments, schema=tool.input_schema)
                    coerced_args = arguments
                except JSONSchemaValidationError:
                    pass
            
            # If still fails, raise error
            try:
                validate(instance=coerced_args, schema=tool.input_schema)
            except JSONSchemaValidationError:
                raise ValidationError(
                    f"Tool '{tool.name}' argument validation failed: {e.message}"
                ) from e
        
        # Execute via MCP
        try:
            result = await self.transport.send_request(
                "tools/call",
                {
                    "name": tool.name,
                    "arguments": coerced_args
                }
            )
            
            # Normalize result - handle various response formats
            if not isinstance(result, dict):
                result = safe_dict(result, {})
            
            # Extract content and isError with multiple fallback names
            content = safe_get(result, "content") or safe_get(result, "contents") or safe_get(result, "result") or []
            if not isinstance(content, list):
                content = safe_list(content, [])
            
            # Handle isError in various formats
            is_error = False
            if "isError" in result:
                is_error = bool(result["isError"])
            elif "is_error" in result:
                is_error = bool(result["is_error"])
            elif "error" in result:
                is_error = bool(result["error"])
            
            return ToolExecutionResult(
                content=content,
                is_error=is_error
            )
        except Exception as e:
            if isinstance(e, (ValidationError, ExecutionError)):
                raise
            raise ExecutionError(f"Tool execution failed: {e}") from e
    
    def find_tool(self, name: str, tools: list[MCPTool]) -> MCPTool | None:
        """Find tool by name.
        
        Args:
            name: Tool name
            tools: List of available tools
            
        Returns:
            MCPTool if found, None otherwise
        """
        for tool in tools:
            if tool.name == name:
                return tool
        return None

