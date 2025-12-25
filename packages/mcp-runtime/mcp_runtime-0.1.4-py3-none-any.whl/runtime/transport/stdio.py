"""STDIO transport for local MCP servers.

Uses subprocess + stdio for local MCP server communication.
"""

import asyncio
import json
import subprocess
from typing import Any, Dict, Optional
from runtime.transport.base import Transport
from runtime.errors import TransportError


class StdioTransport(Transport):
    """STDIO transport for local MCP servers.
    
    Spawns subprocess and communicates via stdin/stdout.
    No retries. Fail fast.
    """
    
    def __init__(self, command: list[str], env: Optional[Dict[str, str]] = None):
        """Initialize STDIO transport.
        
        Args:
            command: Command to execute (list of strings)
            env: Optional environment variables
        """
        self.command = command
        self.env = env
        self.process: Optional[subprocess.Popen] = None
        self._connected = False
        self._request_id = 0
        self._pending_requests: Dict[int, asyncio.Future] = {}
    
    async def connect(self) -> None:
        """Start subprocess and establish connection."""
        if self._connected:
            return
        
        try:
            self.process = subprocess.Popen(
                self.command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=self.env,
                text=False  # Use bytes for binary safety
            )
            
            # Start response reader
            asyncio.create_task(self._read_responses())
            
            self._connected = True
        except Exception as e:
            raise TransportError(f"Failed to start subprocess: {e}") from e
    
    async def disconnect(self) -> None:
        """Terminate subprocess."""
        if self.process:
            try:
                self.process.terminate()
                await asyncio.wait_for(
                    asyncio.to_thread(self.process.wait),
                    timeout=5.0
                )
            except asyncio.TimeoutError:
                self.process.kill()
            except Exception as e:
                raise TransportError(f"Error disconnecting: {e}") from e
            finally:
                self.process = None
                self._connected = False
    
    async def _read_responses(self) -> None:
        """Read responses from stdout."""
        if not self.process or not self.process.stdout:
            return
        
        try:
            while self._connected and self.process:
                # Use to_thread to read blocking I/O
                line = await asyncio.to_thread(self.process.stdout.readline)
                if not line:
                    # Process ended
                    break
                
                line_str = line.decode('utf-8').strip()
                if not line_str:
                    continue
                
                try:
                    response = json.loads(line_str)
                    request_id = response.get('id')
                    if request_id is not None and request_id in self._pending_requests:
                        future = self._pending_requests.pop(request_id)
                        future.set_result(response)
                    # Ignore notifications (no id field)
                except json.JSONDecodeError as e:
                    # Fail fast on malformed JSON
                    for future in self._pending_requests.values():
                        future.set_exception(
                            TransportError(f"Malformed JSON response: {e}")
                        )
                    self._pending_requests.clear()
                    break
                except Exception as e:
                    # Fail fast on any error
                    for future in self._pending_requests.values():
                        future.set_exception(
                            TransportError(f"Error reading response: {e}")
                        )
                    self._pending_requests.clear()
                    break
        except Exception as e:
            # Don't raise, just log - this is a background task
            if self._connected:
                for future in self._pending_requests.values():
                    future.set_exception(
                        TransportError(f"Error in response reader: {e}")
                    )
                self._pending_requests.clear()
    
    async def send_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send JSON-RPC request via stdin."""
        if not self._connected or not self.process or not self.process.stdin:
            raise TransportError("Transport not connected")
        
        self._request_id += 1
        request_id = self._request_id
        
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
        }
        if params is not None:
            request["params"] = params
        
        future = asyncio.Future()
        self._pending_requests[request_id] = future
        
        try:
            request_json = json.dumps(request) + "\n"
            self.process.stdin.write(request_json.encode('utf-8'))
            self.process.stdin.flush()
            
            # Wait for response with timeout
            response = await asyncio.wait_for(future, timeout=30.0)
            
            # Check for JSON-RPC error
            if "error" in response:
                error = response["error"]
                raise TransportError(
                    f"JSON-RPC error: {error.get('message', 'Unknown error')} "
                    f"(code: {error.get('code', 'unknown')})"
                )
            
            return response.get("result", {})
        except asyncio.TimeoutError:
            self._pending_requests.pop(request_id, None)
            raise TransportError(f"Request timeout: {method}")
        except Exception as e:
            self._pending_requests.pop(request_id, None)
            if isinstance(e, TransportError):
                raise
            raise TransportError(f"Error sending request: {e}") from e
    
    async def send_notification(self, method: str, params: Optional[Dict[str, Any]] = None) -> None:
        """Send JSON-RPC notification via stdin (no response expected)."""
        if not self._connected or not self.process or not self.process.stdin:
            raise TransportError("Transport not connected")
        
        request = {
            "jsonrpc": "2.0",
            "method": method,
        }
        if params is not None:
            request["params"] = params
        
        try:
            request_json = json.dumps(request) + "\n"
            self.process.stdin.write(request_json.encode('utf-8'))
            self.process.stdin.flush()
        except Exception as e:
            raise TransportError(f"Error sending notification: {e}") from e
    
    async def initialize(self, client_info: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize MCP session."""
        params = {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": client_info
        }
        return await self.send_request("initialize", params)
    
    @property
    def is_connected(self) -> bool:
        """Check if transport is connected."""
        return self._connected and self.process is not None

