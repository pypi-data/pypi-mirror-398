"""Base transport interface for MCP Runtime."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from runtime.errors import TransportError


class Transport(ABC):
    """Abstract base class for MCP transport implementations.
    
    Transport layer handles:
    - Connection to MCP server
    - Sending requests
    - Receiving responses
    - No retries in v1
    - Fail fast on errors
    """
    
    @abstractmethod
    async def connect(self) -> None:
        """Connect to MCP server.
        
        Raises:
            TransportError: If connection fails
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from MCP server."""
        pass
    
    @abstractmethod
    async def send_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send a JSON-RPC request to MCP server.
        
        Args:
            method: JSON-RPC method name
            params: Optional parameters
            
        Returns:
            JSON-RPC response dict
            
        Raises:
            TransportError: If request fails or response is malformed
        """
        pass
    
    @abstractmethod
    async def send_notification(self, method: str, params: Optional[Dict[str, Any]] = None) -> None:
        """Send a JSON-RPC notification to MCP server.
        
        Notifications don't expect a response.
        
        Args:
            method: JSON-RPC method name
            params: Optional parameters
            
        Raises:
            TransportError: If sending fails
        """
        pass
    
    @abstractmethod
    async def initialize(self, client_info: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize MCP session.
        
        Args:
            client_info: Client information dict
            
        Returns:
            Server capabilities and info
            
        Raises:
            TransportError: If initialization fails
        """
        pass
    
    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if transport is connected."""
        pass

