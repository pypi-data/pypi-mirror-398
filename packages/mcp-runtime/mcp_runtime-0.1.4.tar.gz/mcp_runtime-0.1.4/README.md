# mcp-runtime

**Simple Python library to connect LLM models with MCP (Model Context Protocol) servers**

`mcp-runtime` provides a clean, easy-to-use API for developers to integrate MCP servers with their LLM models. It handles tools, resources, and prompts from any MCP server.

## Features

- ✅ **Simple API** - Easy-to-use `MCPClient` class
- ✅ **LLM Adapters** - Support for OpenAI, Gemini, and Claude
- ✅ **Transport Options** - Local (stdio) and remote (HTTP/SSE) MCP servers
- ✅ **Full MCP Support** - Tools, resources, and prompts
- ✅ **Blueprint Caching** - Save/load server capabilities for faster startup
- ✅ **Optimized Performance** - Schema caching, tool format caching
- ✅ **Hosted Server Support** - Works with GitHub MCP, NeonDB MCP, and any HTTP/SSE server
- ✅ **Type Safe** - Full type hints and proper error handling

## Installation

```bash
pip install mcp-runtime
```

For LLM adapter support:

```bash
# OpenAI
pip install mcp-runtime[openai]

# Gemini
pip install mcp-runtime[gemini]

# Claude
pip install mcp-runtime[claude]
```

## Quick Start

### Basic Usage

```python
import asyncio
from runtime import MCPClient

async def main():
    # Connect to a local MCP server
    client = MCPClient.local(
        command=["python", "-m", "my_mcp_server"],
        adapter="openai"  # or "gemini", "claude"
    )
    
    # Connect and discover capabilities
    await client.connect()
    
    # Get tools for your LLM
    tools = client.get_tools()
    
    # Execute a tool
    result = await client.call_tool("calculator", {
        "operation": "multiply",
        "a": 15,
        "b": 23
    })
    print(result.content)
    
    # Disconnect
    await client.disconnect()

asyncio.run(main())
```

### Connect to Remote MCP Server

```python
# Connect to a remote MCP server (HTTP/SSE)
client = MCPClient.remote(
    base_url="https://example.com/mcp",
    adapter="openai",
    headers={"Authorization": "Bearer token"}
)

await client.connect()
```

### Using with LLM APIs

```python
import asyncio
from runtime import MCPClient
import google.generativeai as genai  # or openai, anthropic

async def main():
    # Create MCP client
    client = MCPClient.local(
        command=["python", "-m", "my_mcp_server"],
        adapter="gemini"  # Optimized for Gemini!
    )
    
    await client.connect()
    
    # Get tools in LLM format (cached for performance)
    tools = client.get_tools()
    
    # Configure Gemini with tools
    model = genai.GenerativeModel(
        model_name="gemini-pro",
        tools=tools
    )
    
    # Make request
    response = model.generate_content("Calculate 15 * 23")
    
    # Parse tool calls from response
    tool_calls = client.parse_tool_calls(response)
    
    # Execute tool calls
    for tool_call in tool_calls:
        result = await client.call_tool(
            tool_call["name"],
            tool_call["arguments"]
        )
        
        # Format result for Gemini
        tool_result = client.format_tool_result(
            tool_call["name"],
            result
        )
        
        # Continue conversation with tool result
        # ...
    
    await client.disconnect()

asyncio.run(main())
```

### Blueprint Caching (Save/Load Capabilities)

Save server capabilities once, reuse them later for faster startup:

```python
from runtime import MCPClient

# First run: Discover and save
client = MCPClient.local(
    command=["python", "-m", "my_mcp_server"],
    adapter="gemini"
)
await client.connect()

# Save blueprint for future use
blueprint_path = client.save_blueprint()
print(f"Saved to: {blueprint_path}")

# Second run: Load from blueprint (much faster!)
client2 = MCPClient.local(
    command=["python", "-m", "my_mcp_server"],
    adapter="gemini"
)
await client2.connect(use_blueprint=blueprint_path)  # Skips discovery!

# Tools are ready immediately
tools = client2.get_tools()
```

### Hosted MCP Servers

Works with any hosted MCP server (GitHub, NeonDB, etc.):

```python
# Connect to hosted server
client = MCPClient.remote(
    base_url="https://your-mcp-server.com/mcp",
    adapter="gemini",
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)

await client.connect()

# Save blueprint for this hosted server
blueprint_path = client.save_blueprint()

# Next time, load from blueprint
await client.connect(use_blueprint=blueprint_path)
```

## API Reference

### MCPClient

Main client class for connecting to MCP servers.

#### Methods

- `connect()` - Connect to MCP server and discover capabilities
- `disconnect()` - Disconnect from MCP server
- `get_tools()` - Get tools in LLM format
- `call_tool(name, arguments)` - Execute a tool call
- `read_resource(name, uri_arguments)` - Read a resource
- `expand_prompt(name, arguments)` - Expand a prompt template
- `parse_tool_calls(llm_response)` - Parse tool calls from LLM response
- `format_tool_result(tool_name, result)` - Format tool result for LLM

#### Properties

- `server_info` - Server information
- `tools` - List of discovered tools
- `resources` - List of discovered resources
- `prompts` - List of discovered prompts
- `is_connected` - Connection status

#### Factory Methods

- `MCPClient.local(command, adapter, ...)` - Create client for local MCP server
- `MCPClient.remote(base_url, adapter, ...)` - Create client for remote MCP server

## Examples

See `examples/example.py` for a complete working example.

## Architecture

```
mcp-runtime/
│
├── runtime/
│   ├── client.py          # Main MCPClient class
│   ├── runtime.py          # Core runtime (advanced usage)
│   ├── transport/          # Transport implementations
│   ├── adapter/            # LLM adapters
│   └── execution/          # Tool/resource/prompt execution
│
└── schemas/
    └── mcp_types.py        # Type definitions
```

## Supported LLM Providers

- **OpenAI** - GPT-4, GPT-3.5 with function calling
- **Google Gemini** - Gemini Pro with function calling
- **Anthropic Claude** - Claude with tool use

## Transport Options

- **StdioTransport** - Local MCP servers via subprocess
- **HttpSSETransport** - Remote MCP servers via HTTP/SSE

## Error Handling

All errors inherit from `MCPRuntimeError`:

```python
from runtime import MCPRuntimeError, TransportError, ExecutionError

try:
    await client.call_tool("calculator", {"operation": "divide", "a": 10, "b": 0})
except ExecutionError as e:
    print(f"Tool execution failed: {e}")
```

## License

MIT

## Contributing

Contributions welcome! Please ensure:

1. Code follows the existing style
2. Type hints included
3. Error handling is explicit
4. Tests included (if applicable)
