"""MCP Runtime - Infrastructure-level runtime for consuming MCP servers.

Simple API for developers to integrate MCP servers with their LLM models.
"""

from runtime.client import MCPClient
from runtime.runtime import MCPRuntime
from runtime.transport.stdio import StdioTransport
from runtime.transport.http_sse import HttpSSETransport
from runtime.adapter.openai import OpenAIAdapter
from runtime.adapter.gemini import GeminiAdapter
from runtime.adapter.claude import ClaudeAdapter
from runtime.blueprint import MCPBlueprint, BlueprintManager
from runtime.errors import (
    MCPRuntimeError,
    TransportError,
    DiscoveryError,
    ExecutionError,
    ValidationError,
    AdapterError,
    TimeoutError
)

__all__ = [
    # Main client API
    "MCPClient",
    
    # Core runtime (advanced usage)
    "MCPRuntime",
    
    # Transports
    "StdioTransport",
    "HttpSSETransport",
    
    # Adapters
    "OpenAIAdapter",
    "GeminiAdapter",
    "ClaudeAdapter",
    
    # Blueprint management
    "MCPBlueprint",
    "BlueprintManager",
    
    # Errors
    "MCPRuntimeError",
    "TransportError",
    "DiscoveryError",
    "ExecutionError",
    "ValidationError",
    "AdapterError",
    "TimeoutError",
]

__version__ = "0.1.4"
