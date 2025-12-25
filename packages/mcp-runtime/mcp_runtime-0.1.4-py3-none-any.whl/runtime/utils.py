"""Utility functions for robust data handling and URL normalization.

Provides smart type conversion, URL normalization, and error handling utilities
to make the runtime bulletproof against various server implementations.
"""

import re
from typing import Any, Dict, Optional, Union
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode


def normalize_url(base_url: str) -> str:
    """Normalize and validate MCP server URL.
    
    Handles various URL formats:
    - URLs with/without trailing slashes
    - URLs with/without /sse endpoint
    - URLs with/without protocol
    - Relative paths
    
    Args:
        base_url: Raw URL from user
        
    Returns:
        Normalized base URL (without /sse, without trailing slash)
        
    Examples:
        "https://example.com/mcp" -> "https://example.com/mcp"
        "https://example.com/mcp/" -> "https://example.com/mcp"
        "https://example.com/mcp/sse" -> "https://example.com/mcp"
        "example.com/mcp" -> "https://example.com/mcp"
    """
    if not base_url or not isinstance(base_url, str):
        raise ValueError("URL must be a non-empty string")
    
    # Remove whitespace
    base_url = base_url.strip()
    
    # Remove /sse endpoint if present (we'll add it when needed)
    base_url = re.sub(r'/sse/?$', '', base_url, flags=re.IGNORECASE)
    
    # Remove trailing slashes
    base_url = base_url.rstrip('/')
    
    # Add protocol if missing
    if not base_url.startswith(('http://', 'https://')):
        # Default to https for security
        base_url = f"https://{base_url}"
    
    # Validate URL structure
    try:
        parsed = urlparse(base_url)
        if not parsed.netloc:
            raise ValueError(f"Invalid URL: missing hostname in {base_url}")
        
        # Reconstruct URL with normalized path
        normalized = urlunparse((
            parsed.scheme or 'https',
            parsed.netloc,
            parsed.path.rstrip('/') or '/',
            parsed.params,
            parsed.query,
            parsed.fragment
        ))
        
        return normalized.rstrip('/')
    except Exception as e:
        raise ValueError(f"Invalid URL format: {base_url}") from e


def get_sse_url(base_url: str) -> str:
    """Get SSE endpoint URL from base URL.
    
    Args:
        base_url: Normalized base URL
        
    Returns:
        Full SSE endpoint URL
    """
    base_url = normalize_url(base_url)
    return f"{base_url}/sse"


def safe_str(value: Any, default: str = "") -> str:
    """Safely convert any value to string.
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        
    Returns:
        String representation of value
    """
    if value is None:
        return default
    try:
        if isinstance(value, str):
            return value
        if isinstance(value, (int, float, bool)):
            return str(value)
        if isinstance(value, bytes):
            return value.decode('utf-8', errors='replace')
        return str(value)
    except Exception:
        return default


def safe_int(value: Any, default: int = 0) -> int:
    """Safely convert any value to integer.
    
    Handles:
    - String numbers ("123", "45.0")
    - Float numbers (45.0 -> 45)
    - Integer numbers
    - None/empty values
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        
    Returns:
        Integer value
    """
    if value is None:
        return default
    
    try:
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            if value.is_integer():
                return int(value)
            return default  # Can't convert non-integer float
        if isinstance(value, bool):
            return 1 if value else 0
        if isinstance(value, str):
            # Remove whitespace
            value = value.strip()
            if not value:
                return default
            # Try direct conversion
            try:
                return int(value)
            except ValueError:
                # Try float first, then int
                try:
                    float_val = float(value)
                    if float_val.is_integer():
                        return int(float_val)
                except ValueError:
                    pass
                return default
        # For other types, try conversion
        return int(value)
    except (ValueError, TypeError, OverflowError):
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert any value to float.
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        
    Returns:
        Float value
    """
    if value is None:
        return default
    
    try:
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, bool):
            return 1.0 if value else 0.0
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return default
            return float(value)
        return float(value)
    except (ValueError, TypeError, OverflowError):
        return default


def safe_bool(value: Any, default: bool = False) -> bool:
    """Safely convert any value to boolean.
    
    Handles:
    - String "true"/"false" (case insensitive)
    - String "1"/"0"
    - Integer 1/0
    - Boolean values
    - None -> False
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        
    Returns:
        Boolean value
    """
    if value is None:
        return default
    
    try:
        if isinstance(value, bool):
            return value
        if isinstance(value, int):
            return bool(value)
        if isinstance(value, str):
            value = value.strip().lower()
            if value in ('true', '1', 'yes', 'on'):
                return True
            if value in ('false', '0', 'no', 'off', ''):
                return False
        # Try direct conversion
        return bool(value)
    except Exception:
        return default


def safe_dict(value: Any, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Safely convert any value to dictionary.
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        
    Returns:
        Dictionary value
    """
    if default is None:
        default = {}
    
    if value is None:
        return default
    
    try:
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            import json
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return default
        # Try to convert to dict
        if hasattr(value, '__dict__'):
            return vars(value)
        if hasattr(value, 'dict'):
            return value.dict()
        return default
    except Exception:
        return default


def safe_list(value: Any, default: Optional[list] = None) -> list:
    """Safely convert any value to list.
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        
    Returns:
        List value
    """
    if default is None:
        default = []
    
    if value is None:
        return default
    
    try:
        if isinstance(value, list):
            return value
        if isinstance(value, tuple):
            return list(value)
        if isinstance(value, (str, bytes)):
            # Try JSON parsing
            import json
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                pass
        # Try iteration
        try:
            return list(value)
        except TypeError:
            return [value]  # Single value as list
    except Exception:
        return default


def extract_session_id(data: str, fallback: Optional[str] = None) -> Optional[str]:
    """Extract session ID from various formats.
    
    Handles:
    - Query parameters: ?session_id=abc123
    - URL-encoded: session_id%3Dabc123
    - Headers: X-Session-Id: abc123
    - JSON: {"session_id": "abc123"}
    - Plain text: session_id=abc123
    
    Args:
        data: String containing session ID
        fallback: Fallback value if extraction fails
        
    Returns:
        Extracted session ID or fallback
    """
    if not data or not isinstance(data, str):
        return fallback
    
    # Try multiple extraction methods
    patterns = [
        r'session_id["\s:=]+([^\s&?\'"<>]+)',  # session_id=value or session_id: value
        r'sessionId["\s:=]+([^\s&?\'"<>]+)',   # sessionId=value (camelCase)
        r'session-id["\s:=]+([^\s&?\'"<>]+)',  # session-id=value (kebab-case)
        r'["\']session_id["\']\s*:\s*["\']([^"\']+)["\']',  # JSON: "session_id": "value"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, data, re.IGNORECASE)
        if match:
            session_id = match.group(1).strip()
            if session_id:
                # URL decode if needed
                try:
                    from urllib.parse import unquote
                    session_id = unquote(session_id)
                except Exception:
                    pass
                return session_id
    
    # Try query parameter parsing
    try:
        from urllib.parse import parse_qs, unquote
        if '?' in data:
            _, query = data.split('?', 1)
            params = parse_qs(query)
            for key in ['session_id', 'sessionId', 'session-id']:
                if key in params:
                    value = params[key][0] if params[key] else None
                    if value:
                        return unquote(value)
    except Exception:
        pass
    
    return fallback


def normalize_request_id(request_id: Any) -> int:
    """Normalize request ID to integer.
    
    Handles various formats:
    - Integer: 123
    - String: "123", "123.0"
    - Float: 123.0
    
    Args:
        request_id: Request ID in any format
        
    Returns:
        Integer request ID
    """
    return safe_int(request_id, default=0)


def coerce_to_schema_type(value: Any, schema_type: str, schema: Optional[Dict[str, Any]] = None) -> Any:
    """Coerce value to match schema type.
    
    Args:
        value: Value to coerce
        schema_type: Expected type from schema ("string", "integer", "number", "boolean", "array", "object")
        schema: Full schema dict for additional context
        
    Returns:
        Coerced value
    """
    if value is None:
        return None
    
    try:
        if schema_type == "string":
            return safe_str(value)
        elif schema_type == "integer":
            return safe_int(value)
        elif schema_type == "number":
            return safe_float(value)
        elif schema_type == "boolean":
            return safe_bool(value)
        elif schema_type == "array":
            return safe_list(value)
        elif schema_type == "object":
            return safe_dict(value)
        else:
            # Unknown type, return as-is
            return value
    except Exception:
        # If coercion fails, return original value
        return value


def normalize_json_response(response: Any) -> Dict[str, Any]:
    """Normalize JSON response to dictionary.
    
    Handles:
    - Dict objects
    - String JSON
    - Response objects with .json() method
    - Objects with __dict__
    
    Args:
        response: Response in any format
        
    Returns:
        Normalized dictionary
    """
    if isinstance(response, dict):
        return response
    
    if isinstance(response, str):
        try:
            import json
            return json.loads(response)
        except json.JSONDecodeError:
            return {}
    
    # Try to get JSON from response object
    if hasattr(response, 'json'):
        try:
            return response.json()
        except Exception:
            pass
    
    if hasattr(response, '__dict__'):
        return vars(response)
    
    if hasattr(response, 'dict'):
        try:
            return response.dict()
        except Exception:
            pass
    
    # Try to convert to dict
    try:
        return dict(response)
    except (TypeError, ValueError):
        return {}


def safe_get(data: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    """Safely get nested dictionary value.
    
    Args:
        data: Dictionary to search
        keys: Nested keys (e.g., "a", "b", "c" for data["a"]["b"]["c"])
        default: Default value if key not found
        
    Returns:
        Value or default
    """
    if not isinstance(data, dict):
        return default
    
    current = data
    for key in keys:
        if not isinstance(current, dict):
            return default
        if key not in current:
            return default
        current = current[key]
    
    return current

