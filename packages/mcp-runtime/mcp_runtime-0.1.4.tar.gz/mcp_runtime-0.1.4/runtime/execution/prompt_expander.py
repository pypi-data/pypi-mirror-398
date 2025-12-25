"""Prompt expansion engine.

Prompts only expand to text.
Runtime does not execute prompts.
LLM decides usage.
"""

from typing import Any, Dict
from runtime.transport.base import Transport
from runtime.errors import ExecutionError
from schemas.mcp_types import MCPPrompt, PromptExpansionResult


class PromptExpander:
    """Expands MCP prompts.
    
    Prompts expand to text only. Runtime does not execute prompts.
    """
    
    def __init__(self, transport: Transport):
        """Initialize prompt expander.
        
        Args:
            transport: Connected transport instance
        """
        self.transport = transport
    
    async def expand(
        self,
        prompt: MCPPrompt,
        arguments: Dict[str, Any] | None = None
    ) -> PromptExpansionResult:
        """Expand a prompt with given arguments.
        
        Args:
            prompt: Prompt to expand
            arguments: Optional prompt arguments
            
        Returns:
            PromptExpansionResult: Expanded prompt messages
            
        Raises:
            ExecutionError: If expansion fails
        """
        try:
            params = {
                "name": prompt.name
            }
            if arguments:
                params["arguments"] = arguments
            
            result = await self.transport.send_request(
                "prompts/get",
                params
            )
            
            messages = result.get("messages", [])
            
            return PromptExpansionResult(
                messages=messages
            )
        except Exception as e:
            raise ExecutionError(f"Prompt expansion failed: {e}") from e
    
    def find_prompt(self, name: str, prompts: list[MCPPrompt]) -> MCPPrompt | None:
        """Find prompt by name.
        
        Args:
            name: Prompt name
            prompts: List of available prompts
            
        Returns:
            MCPPrompt if found, None otherwise
        """
        for prompt in prompts:
            if prompt.name == name:
                return prompt
        return None

