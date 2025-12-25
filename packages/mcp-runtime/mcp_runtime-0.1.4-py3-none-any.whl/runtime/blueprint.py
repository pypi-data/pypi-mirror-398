"""Blueprint manager for caching MCP server capabilities.

Allows saving and loading tools, resources, and prompts to avoid
re-discovering them on every connection.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
from schemas.mcp_types import MCPServerInfo, MCPTool, MCPResource, MCPPrompt


@dataclass
class MCPBlueprint:
    """Blueprint containing MCP server capabilities."""
    server_info: Dict[str, Any]
    tools: List[Dict[str, Any]]
    resources: List[Dict[str, Any]]
    prompts: List[Dict[str, Any]]
    version: str = "1.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert blueprint to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPBlueprint":
        """Create blueprint from dictionary."""
        return cls(**data)
    
    @classmethod
    def from_capabilities(
        cls,
        server_info: MCPServerInfo,
        tools: List[MCPTool],
        resources: List[MCPResource],
        prompts: List[MCPPrompt]
    ) -> "MCPBlueprint":
        """Create blueprint from runtime capabilities."""
        return cls(
            server_info={
                "name": server_info.name,
                "version": server_info.version,
                "protocol_version": server_info.protocol_version
            },
            tools=[asdict(tool) for tool in tools],
            resources=[asdict(resource) for resource in resources],
            prompts=[asdict(prompt) for prompt in prompts]
        )
    
    def to_runtime_capabilities(
        self
    ) -> tuple[MCPServerInfo, List[MCPTool], List[MCPResource], List[MCPPrompt]]:
        """Convert blueprint back to runtime capabilities."""
        server_info = MCPServerInfo(
            name=self.server_info["name"],
            version=self.server_info["version"],
            protocol_version=self.server_info["protocol_version"]
        )
        
        tools = [MCPTool(**tool) for tool in self.tools]
        resources = [MCPResource(**resource) for resource in self.resources]
        prompts = [MCPPrompt(**prompt) for prompt in self.prompts]
        
        return server_info, tools, resources, prompts


class BlueprintManager:
    """Manager for saving and loading MCP blueprints."""
    
    @staticmethod
    def save(blueprint: MCPBlueprint, file_path: str) -> None:
        """Save blueprint to JSON file.
        
        Args:
            blueprint: Blueprint to save
            file_path: Path to save blueprint file
        """
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(blueprint.to_dict(), f, indent=2, ensure_ascii=False)
    
    @staticmethod
    def load(file_path: str) -> MCPBlueprint:
        """Load blueprint from JSON file.
        
        Args:
            file_path: Path to blueprint file
            
        Returns:
            Loaded blueprint
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is invalid
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Blueprint file not found: {file_path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return MCPBlueprint.from_dict(data)
    
    @staticmethod
    def get_default_path(server_name: str, base_dir: Optional[str] = None) -> str:
        """Get default blueprint file path for a server.
        
        Args:
            server_name: Name of the MCP server
            base_dir: Base directory for blueprints (default: ~/.mcp-runtime/blueprints)
            
        Returns:
            Default file path
        """
        if base_dir:
            base = Path(base_dir)
        else:
            base = Path.home() / ".mcp-runtime" / "blueprints"
        
        base.mkdir(parents=True, exist_ok=True)
        
        # Sanitize server name for filename
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in server_name)
        return str(base / f"{safe_name}.json")

