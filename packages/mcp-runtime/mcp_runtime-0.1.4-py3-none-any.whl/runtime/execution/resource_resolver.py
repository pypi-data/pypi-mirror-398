"""Resource resolution engine.

Resources are read-only.
No mutation.
No inference.
URI templates must be filled explicitly.
No caching in v1.
"""

from typing import Any, Dict
from runtime.transport.base import Transport
from runtime.errors import ExecutionError
from schemas.mcp_types import MCPResource, ResourceReadResult


class ResourceResolver:
    """Resolves MCP resources.
    
    Resources are read-only. No mutation. No inference.
    """
    
    def __init__(self, transport: Transport):
        """Initialize resource resolver.
        
        Args:
            transport: Connected transport instance
        """
        self.transport = transport
    
    async def read(
        self,
        resource: MCPResource,
        uri_arguments: Dict[str, str] | None = None
    ) -> ResourceReadResult:
        """Read a resource.
        
        Args:
            resource: Resource to read
            uri: Full URI (with template variables filled)
            uri_arguments: Optional URI template arguments
            
        Returns:
            ResourceReadResult: Resource contents
            
        Raises:
            ExecutionError: If reading fails
        """
        # Build URI (fill template if needed)
        uri = resource.uri
        if uri_arguments:
            # Simple template substitution
            for key, value in uri_arguments.items():
                uri = uri.replace(f"{{{key}}}", value)
        
        try:
            result = await self.transport.send_request(
                "resources/read",
                {
                    "uri": uri
                }
            )
            
            contents = result.get("contents", [])
            mime_type = result.get("mimeType")
            
            return ResourceReadResult(
                contents=contents,
                mime_type=mime_type
            )
        except Exception as e:
            raise ExecutionError(f"Resource read failed: {e}") from e
    
    def find_resource(self, uri: str, resources: list[MCPResource]) -> MCPResource | None:
        """Find resource by URI (exact match or template match).
        
        Args:
            uri: Resource URI
            resources: List of available resources
            
        Returns:
            MCPResource if found, None otherwise
        """
        for resource in resources:
            if resource.uri == uri:
                return resource
            # Simple template matching (basic check)
            if "{" in resource.uri:
                # Could implement more sophisticated template matching
                base_uri = resource.uri.split("{")[0]
                if uri.startswith(base_uri):
                    return resource
        return None

