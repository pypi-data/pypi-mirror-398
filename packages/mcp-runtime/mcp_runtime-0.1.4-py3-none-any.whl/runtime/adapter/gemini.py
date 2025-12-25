"""Google Gemini adapter for MCP Runtime.

Converts MCP tools to Gemini function calling format.
Optimized with schema caching for better performance.
Robust type handling and error recovery.
"""

import json
import logging
from typing import Any, Dict, List, Optional
from runtime.adapter.base import LLMAdapter
from schemas.mcp_types import MCPTool, ToolExecutionResult
from runtime.utils import (
    safe_str,
    safe_dict,
    safe_list,
    normalize_json_response,
    coerce_to_schema_type
)

# Try to import genai for proper schema conversion
try:
    import google.generativeai as genai
    try:
        import google.generativeai.protos as protos
        HAS_PROTOS = True
    except ImportError:
        HAS_PROTOS = False
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False
    HAS_PROTOS = False


class GeminiAdapter(LLMAdapter):
    """Google Gemini adapter for function calling.
    
    Converts MCP tools to Gemini function format.
    Parses Gemini tool calls.
    Optimized with schema caching.
    """
    
    def __init__(self):
        """Initialize Gemini adapter with caching."""
        self._schema_cache: Dict[str, Dict[str, Any]] = {}
        self._tools_cache: Optional[List[Dict[str, Any]]] = None
        self._cached_tools_hash: Optional[str] = None
        self._logger = logging.getLogger(__name__)
    
    def _get_schema_hash(self, schema: Dict[str, Any]) -> str:
        """Generate hash for schema caching."""
        return json.dumps(schema, sort_keys=True)
    
    def _clean_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Clean JSON schema to remove fields not supported by Gemini.
        
        Gemini doesn't support: default, examples, etc.
        Also ensures proper JSON Schema structure for Gemini compatibility.
        Recursively processes nested schemas to ensure all types are valid.
        
        Args:
            schema: JSON schema dict
            
        Returns:
            Cleaned schema dict
        """
        if not isinstance(schema, dict):
            return schema
        
        # Check cache first
        schema_hash = self._get_schema_hash(schema)
        if schema_hash in self._schema_cache:
            return self._schema_cache[schema_hash]
        
        cleaned = {}
        for key, value in schema.items():
            # Skip unsupported fields that Gemini doesn't handle well
            if key in ["default", "examples", "$schema", "$id", "$defs", "definitions"]:
                continue
            
            if key == "properties" and isinstance(value, dict):
                # Recursively clean properties
                cleaned_props = {}
                for prop_name, prop_schema in value.items():
                    cleaned_prop = self._clean_schema(prop_schema)
                    # Ensure each property has a type if it has properties or items
                    if isinstance(cleaned_prop, dict):
                        if ("properties" in cleaned_prop or "items" in cleaned_prop) and "type" not in cleaned_prop:
                            # Add type based on what's present
                            if "properties" in cleaned_prop:
                                cleaned_prop["type"] = "object"
                            elif "items" in cleaned_prop:
                                cleaned_prop["type"] = "array"
                    cleaned_props[prop_name] = cleaned_prop
                cleaned[key] = cleaned_props
            elif key == "items":
                # Handle array items - can be dict or list
                if isinstance(value, dict):
                    cleaned[key] = self._clean_schema(value)
                elif isinstance(value, list):
                    # Array of schemas (tuple validation)
                    cleaned[key] = [self._clean_schema(item) if isinstance(item, dict) else item for item in value]
                else:
                    cleaned[key] = value
            elif key in ["anyOf", "oneOf", "allOf"]:
                # Recursively clean union types
                if isinstance(value, list):
                    cleaned[key] = [self._clean_schema(item) if isinstance(item, dict) else item for item in value]
                else:
                    cleaned[key] = self._clean_schema(value) if isinstance(value, dict) else value
            elif key == "type":
                # Ensure type is a valid JSON Schema type
                # Gemini expects standard JSON Schema types as strings
                valid_types = ["string", "number", "integer", "boolean", "array", "object", "null"]
                if isinstance(value, str) and value in valid_types:
                    cleaned[key] = value
                elif isinstance(value, list):
                    # Handle multiple types (union type)
                    cleaned[key] = [t for t in value if t in valid_types]
                else:
                    # Skip invalid types
                    continue
            elif key == "required" and isinstance(value, list):
                # Keep required fields as-is
                cleaned[key] = value
            elif key in ["description", "title", "enum", "const", "minimum", "maximum", "minLength", "maxLength", "pattern", "format"]:
                # Keep these supported fields
                cleaned[key] = value
            else:
                # For other fields, try to clean recursively if it's a dict
                if isinstance(value, dict):
                    cleaned[key] = self._clean_schema(value)
                elif isinstance(value, list):
                    cleaned[key] = [self._clean_schema(item) if isinstance(item, dict) else item for item in value]
                else:
                    cleaned[key] = value
        
        # Cache cleaned schema
        self._schema_cache[schema_hash] = cleaned
        return cleaned
    
    def _ensure_object_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure schema has proper object structure for Gemini.
        
        Gemini expects the root schema to be an object schema if it has properties.
        
        Args:
            schema: JSON schema dict
            
        Returns:
            Schema with proper object structure
        """
        if not isinstance(schema, dict):
            return {"type": "object", "properties": {}}
        
        # If schema has properties but no type, add type: "object"
        if "properties" in schema and "type" not in schema:
            return {"type": "object", **schema}
        
        # If schema is empty, return default object schema
        if not schema:
            return {"type": "object", "properties": {}}
        
        return schema
    
    def convert_tools_to_llm_format(self, tools: List[MCPTool]) -> List[Dict[str, Any]]:
        """Convert MCP tools to Gemini function format.
        
        Optimized with caching to avoid re-processing same tools.
        Uses proper JSON Schema format compatible with Gemini's protobuf conversion.
        Tries to use genai.types helper functions if available for proper conversion.
        
        Args:
            tools: List of MCP tools
            
        Returns:
            List of Gemini function definitions (dict format that Gemini can convert)
        """
        # Generate hash for current tools list
        tools_hash = json.dumps(
            [(t.name, t.description, self._get_schema_hash(t.input_schema)) for t in tools],
            sort_keys=True
        )
        
        # Return cached result if tools haven't changed
        if self._tools_cache is not None and self._cached_tools_hash == tools_hash:
            return self._tools_cache
        
        function_declarations = []
        for tool in tools:
            # Clean schema to remove unsupported fields (uses cache internally)
            cleaned_schema = self._clean_schema(tool.input_schema)
            # Ensure proper object structure for Gemini
            cleaned_schema = self._ensure_object_schema(cleaned_schema)
            
            # Try to use genai.types.FunctionDeclaration if available for proper conversion
            # Otherwise fall back to dict format
            if HAS_GENAI:
                try:
                    from google.generativeai.types import FunctionDeclaration
                    # Use FunctionDeclaration for proper protobuf conversion
                    function_decl = FunctionDeclaration(
                        name=tool.name,
                        description=tool.description or "",
                        parameters=cleaned_schema
                    )
                    # Convert to dict for caching (FunctionDeclaration can be serialized)
                    function_declarations.append({
                        "name": tool.name,
                        "description": tool.description or "",
                        "parameters": cleaned_schema
                    })
                except (ImportError, AttributeError, TypeError):
                    # Fall back to dict format if FunctionDeclaration doesn't work
                    function_decl = {
                        "name": tool.name,
                        "description": tool.description or "",
                        "parameters": cleaned_schema
                    }
                    function_declarations.append(function_decl)
            else:
                # Standard dict format
                function_decl = {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": cleaned_schema
                }
                function_declarations.append(function_decl)
        
        # Cache result
        self._tools_cache = function_declarations
        self._cached_tools_hash = tools_hash
        
        return function_declarations
    
    def _normalize_arguments(self, arguments: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize arguments based on schema types.
        
        Converts floats to ints when schema expects integers.
        This handles cases where APIs send 3.0 instead of 3.
        
        Args:
            arguments: Raw arguments dict
            schema: JSON schema for validation
            
        Returns:
            Normalized arguments dict
        """
        normalized = {}
        properties = schema.get("properties", {})
        
        for key, value in arguments.items():
            if key in properties:
                prop_schema = properties[key]
                prop_type = prop_schema.get("type")
                
                # Convert float to int if schema expects integer
                if prop_type == "integer" and isinstance(value, float):
                    if value.is_integer():
                        normalized[key] = int(value)
                    else:
                        normalized[key] = value  # Keep as float if not whole number
                else:
                    normalized[key] = value
            else:
                normalized[key] = value
        
        return normalized
    
    def parse_tool_call(self, llm_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse tool calls from Gemini response with robust handling.
        
        Supports both Gemini 2.5 Flash and older versions.
        Handles various response formats and data types.
        
        Args:
            llm_response: Gemini API response (dict or response object)
            
        Returns:
            List of tool call dicts with 'name' and 'arguments' keys
        """
        tool_calls = []
        
        # Normalize response to dict if needed
        if not isinstance(llm_response, dict):
            llm_response = normalize_json_response(llm_response)
        
        # Handle response object (Gemini 2.5 Flash)
        if hasattr(llm_response, 'candidates'):
            try:
                candidates = llm_response.candidates
                if candidates:
                    for candidate in candidates:
                        if hasattr(candidate, 'content') and candidate.content:
                            if hasattr(candidate.content, 'parts'):
                                for part in candidate.content.parts:
                                    if hasattr(part, 'function_call'):
                                        try:
                                            func_call = part.function_call
                                            name = safe_str(getattr(func_call, 'name', None) or '', '')
                                            if not name:
                                                continue
                                            
                                            # Extract arguments with multiple fallbacks
                                            args = {}
                                            if hasattr(func_call, 'args'):
                                                args_raw = func_call.args
                                                # Handle protobuf message
                                                if hasattr(args_raw, 'items'):
                                                    args = dict(args_raw.items())
                                                elif isinstance(args_raw, dict):
                                                    args = args_raw
                                                else:
                                                    # Try to convert
                                                    try:
                                                        import json
                                                        args = json.loads(str(args_raw))
                                                    except Exception:
                                                        args = safe_dict(args_raw, {})
                                            
                                            tool_calls.append({
                                                "name": name,
                                                "arguments": args
                                            })
                                        except Exception as e:
                                            self._logger.warning(f"Failed to parse function call from part: {e}")
                                            continue
            except Exception as e:
                self._logger.warning(f"Failed to parse candidates from response object: {e}")
        
        # Handle dict response (older format or parsed)
        if not tool_calls:
            try:
                candidates = safe_list(llm_response.get("candidates", []), [])
                if not candidates:
                    return tool_calls
                
                # Try first candidate
                candidate = safe_dict(candidates[0] if candidates else {}, {})
                content = safe_dict(candidate.get("content", {}), {})
                parts = safe_list(content.get("parts", []), [])
                
                for part in parts:
                    part = safe_dict(part, {})
                    
                    # Try multiple function call formats
                    func_call = None
                    if "functionCall" in part:
                        func_call = safe_dict(part["functionCall"], {})
                    elif "function_call" in part:
                        func_call = safe_dict(part["function_call"], {})
                    elif "functionCall" in part:
                        func_call = safe_dict(part["functionCall"], {})
                    
                    if func_call:
                        name = safe_str(func_call.get("name") or func_call.get("functionName") or "", "")
                        if not name:
                            continue
                        
                        args = func_call.get("args") or func_call.get("arguments") or func_call.get("parameters") or {}
                        args = safe_dict(args, {})
                        
                        tool_calls.append({
                            "name": name,
                            "arguments": args
                        })
            except Exception as e:
                self._logger.warning(f"Failed to parse tool calls from dict response: {e}")
        
        return tool_calls
    
    def format_tool_result(self, tool_name: str, result: ToolExecutionResult) -> Dict[str, Any]:
        """Format tool execution result for Gemini with robust handling.
        
        Returns proper Gemini API format: Part object with function_response.
        Handles various content types and formats.
        
        Args:
            tool_name: Name of the tool
            result: ToolExecutionResult
            
        Returns:
            Gemini function response format (Part object)
        """
        # Ensure tool_name is string
        tool_name = safe_str(tool_name, "")
        
        # Convert MCP content to structured response
        response_data: Dict[str, Any] = {}
        
        # Process content items with robust type handling
        text_parts = []
        if not isinstance(result.content, list):
            result.content = safe_list(result.content, [])
        
        for item in result.content:
            if not isinstance(item, dict):
                item = safe_dict(item, {})
            
            item_type = safe_str(item.get("type") or item.get("contentType") or "", "").lower()
            
            if item_type == "text":
                text = safe_str(item.get("text") or item.get("content") or item.get("value") or "", "")
                if text:
                    text_parts.append(text)
            elif item_type == "image":
                # Gemini supports images in responses
                if "image" not in response_data:
                    response_data["image"] = []
                image_data = {
                    "data": safe_str(item.get("data") or item.get("imageData") or "", ""),
                    "mime_type": safe_str(item.get("mimeType") or item.get("mime_type") or item.get("contentType") or "image/png", "image/png")
                }
                if image_data["data"]:
                    response_data["image"].append(image_data)
            else:
                # Unknown type - try to extract text
                text = safe_str(item.get("text") or item.get("content") or item.get("value") or str(item), "")
                if text:
                    text_parts.append(text)
        
        # Add text if available
        if text_parts:
            response_data["result"] = "\n".join(text_parts)
        elif not response_data:
            # Ensure we always have a result
            response_data["result"] = ""
        
        # Mark as error if needed
        if result.is_error:
            response_data["error"] = True
        
        # Return Gemini Part format
        return {
            "function_response": {
                "name": tool_name,
                "response": response_data
            }
        }

