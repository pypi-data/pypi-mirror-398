"""Transport layer for MCP Runtime.

Supports:
- Local process (stdio)
- Remote HTTP/SSE

No retries in v1.
No schema inference.
Fail fast on malformed responses.
"""

