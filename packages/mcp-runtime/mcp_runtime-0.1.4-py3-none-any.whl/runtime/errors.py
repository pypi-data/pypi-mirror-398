"""Error types for MCP Runtime.

Fail loudly. No swallowed exceptions.
"""


class MCPRuntimeError(Exception):
    """Base exception for MCP Runtime errors."""
    pass


class TransportError(MCPRuntimeError):
    """Transport layer errors (connection, I/O, etc.)."""
    pass


class DiscoveryError(MCPRuntimeError):
    """Errors during discovery phase."""
    pass


class ExecutionError(MCPRuntimeError):
    """Errors during tool/resource/prompt execution."""
    pass


class ValidationError(MCPRuntimeError):
    """Schema validation errors."""
    pass


class AdapterError(MCPRuntimeError):
    """LLM adapter errors."""
    pass


class TimeoutError(MCPRuntimeError):
    """Timeout errors."""
    pass

