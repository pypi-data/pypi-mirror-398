"""Canonical internal types for MCP Runtime.

All external MCP protocol data must be normalized into these types.
No inference beyond schemas. Strict validation only.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from enum import Enum


class TransportType(str, Enum):
    """Supported transport types."""
    STDIO = "stdio"
    HTTP_SSE = "http_sse"


@dataclass(frozen=True)
class MCPTool:
    """Canonical representation of an MCP tool.
    
    Tools are executable functions with JSON schemas.
    Treated as black boxes - no semantic inference.
    """
    name: str
    description: Optional[str]
    input_schema: Dict[str, Any]  # JSON Schema
    
    def __post_init__(self):
        """Validate tool structure."""
        if not self.name:
            raise ValueError("Tool name cannot be empty")
        if not isinstance(self.input_schema, dict):
            raise ValueError("Tool input_schema must be a dict")


@dataclass(frozen=True)
class MCPResource:
    """Canonical representation of an MCP resource.
    
    Resources are read-only, addressable data (URI-based).
    No mutation allowed.
    """
    uri: str
    name: str
    description: Optional[str]
    mime_type: Optional[str]
    
    def __post_init__(self):
        """Validate resource structure."""
        if not self.uri:
            raise ValueError("Resource URI cannot be empty")
        if not self.name:
            raise ValueError("Resource name cannot be empty")


@dataclass(frozen=True)
class MCPPrompt:
    """Canonical representation of an MCP prompt.
    
    Prompts are templates that expand to text.
    Runtime does not execute prompts - LLM decides usage.
    """
    name: str
    description: Optional[str]
    arguments: List[Dict[str, Any]]  # Argument definitions
    
    def __post_init__(self):
        """Validate prompt structure."""
        if not self.name:
            raise ValueError("Prompt name cannot be empty")
        if not isinstance(self.arguments, list):
            raise ValueError("Prompt arguments must be a list")


@dataclass(frozen=True)
class MCPServerInfo:
    """Information about an MCP server."""
    name: str
    version: str
    protocol_version: str
    
    def __post_init__(self):
        """Validate server info structure."""
        if not self.name:
            raise ValueError("Server name cannot be empty")
        if not self.version:
            raise ValueError("Server version cannot be empty")
        if not self.protocol_version:
            raise ValueError("Protocol version cannot be empty")


@dataclass(frozen=True)
class ToolExecutionResult:
    """Result of tool execution.
    
    Results are returned unmodified from MCP server.
    No transformation or inference.
    """
    content: List[Dict[str, Any]]  # MCP content format
    is_error: bool
    
    def __post_init__(self):
        """Validate result structure."""
        if not isinstance(self.content, list):
            raise ValueError("Tool execution result content must be a list")


@dataclass(frozen=True)
class ResourceReadResult:
    """Result of reading a resource.
    
    Resources are read-only. No mutation.
    """
    contents: List[Dict[str, Any]]  # MCP content format
    mime_type: Optional[str]
    
    def __post_init__(self):
        """Validate result structure."""
        if not isinstance(self.contents, list):
            raise ValueError("Resource read result contents must be a list")


@dataclass(frozen=True)
class PromptExpansionResult:
    """Result of expanding a prompt.
    
    Prompts expand to text only.
    """
    messages: List[Dict[str, Any]]  # MCP message format
    
    def __post_init__(self):
        """Validate result structure."""
        if not isinstance(self.messages, list):
            raise ValueError("Prompt expansion result messages must be a list")

