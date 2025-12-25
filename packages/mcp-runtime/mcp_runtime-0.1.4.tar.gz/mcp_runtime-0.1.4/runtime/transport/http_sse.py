"""HTTP/SSE transport for remote MCP servers.

Uses HTTP with Server-Sent Events for remote MCP server communication.
Robust URL handling and type conversion for maximum compatibility.
"""

import asyncio
import json
import logging
from typing import Any, Dict, Optional, List
from urllib.parse import parse_qs, unquote, urlparse, urlencode
import aiohttp
from runtime.transport.base import Transport
from runtime.errors import TransportError
from runtime.utils import (
    normalize_url,
    get_sse_url,
    safe_str,
    safe_int,
    extract_session_id,
    normalize_request_id,
    normalize_json_response,
    safe_get
)


class HttpSSETransport(Transport):
    """HTTP/SSE transport for remote MCP servers.
    
    Communicates via HTTP POST for requests and SSE for responses.
    No retries. Fail fast.
    """
    
    def __init__(self, base_url: str, headers: Optional[Dict[str, str]] = None):
        """Initialize HTTP/SSE transport.
        
        Args:
            base_url: Base URL of MCP server (e.g., "https://example.com/mcp" or "https://example.com/mcp/sse")
                     Will automatically normalize and handle various formats
            headers: Optional HTTP headers
        """
        # Normalize URL - handles various formats automatically
        try:
            self.base_url = normalize_url(base_url)
        except Exception as e:
            raise ValueError(f"Invalid base URL: {base_url}") from e
        
        # Normalize headers - ensure all values are strings
        self.headers = {}
        if headers:
            for key, value in headers.items():
                self.headers[safe_str(key)] = safe_str(value)
        
        self.session: Optional[aiohttp.ClientSession] = None
        self._connected = False
        self._request_id = 0
        self._pending_requests: Dict[int, asyncio.Future] = {}
        self._sse_task: Optional[asyncio.Task] = None
        self._session_id: Optional[str] = None
        self._message_path: Optional[str] = None
        self._endpoint_event = asyncio.Event()
        self._sse_error: Optional[Exception] = None
        self._logger = logging.getLogger(__name__)
    
    async def connect(self) -> None:
        """Establish HTTP connection and start SSE listener."""
        if self._connected:
            return
        
        try:
            self.session = aiohttp.ClientSession()
            
            # Start SSE listener
            self._sse_task = asyncio.create_task(self._listen_sse())
            
            # Wait for endpoint event to get session_id
            try:
                await asyncio.wait_for(self._endpoint_event.wait(), timeout=10.0)
            except asyncio.TimeoutError:
                # Check if there was an SSE connection error
                if self._sse_error:
                    raise TransportError(f"SSE connection failed: {self._sse_error}") from self._sse_error
                raise TransportError("Timeout waiting for SSE endpoint event. The server may not be responding or may not be sending the endpoint event.")
            
            # Check if there was an error during SSE connection
            if self._sse_error:
                raise TransportError(f"SSE connection error: {self._sse_error}") from self._sse_error
            
            if not self._session_id:
                raise TransportError("Failed to extract session_id from SSE endpoint")
            
            self._connected = True
        except Exception as e:
            if self._sse_task:
                self._sse_task.cancel()
            if self.session:
                await self.session.close()
                self.session = None
            raise TransportError(f"Failed to connect: {e}") from e
    
    async def disconnect(self) -> None:
        """Close HTTP session."""
        self._connected = False
        self._session_id = None
        self._message_path = None
        self._endpoint_event.clear()
        self._sse_error = None
        
        if self._sse_task:
            self._sse_task.cancel()
            try:
                await self._sse_task
            except asyncio.CancelledError:
                pass
        
        if self.session:
            await self.session.close()
            self.session = None
    
    async def _listen_sse(self) -> None:
        """Listen to Server-Sent Events for responses.
        
        Tries multiple SSE endpoint URLs if the first one fails.
        """
        if not self.session:
            return
        
        # Try multiple SSE endpoint variations
        sse_urls = [
            get_sse_url(self.base_url),  # Standard: /sse
            f"{self.base_url}/sse",      # Direct
            f"{self.base_url}/events",   # Alternative endpoint
            f"{self.base_url}/stream",   # Alternative endpoint
            self.base_url,               # Base URL itself (some servers)
        ]
        
        current_event = None
        current_data = None
        last_error = None
        
        # Try each URL until one works
        for sse_url in sse_urls:
            try:
                self._logger.debug(f"Trying SSE endpoint: {sse_url}")
                async with self.session.get(sse_url, headers=self.headers, timeout=aiohttp.ClientTimeout(total=15)) as response:
                    # Handle non-200 status codes
                    if response.status not in (200, 201, 204):
                        error_text = ""
                        try:
                            error_text = await response.text()
                        except Exception:
                            pass
                        
                        # If this is not the last URL, try next one
                        if sse_url != sse_urls[-1]:
                            last_error = f"Status {response.status}: {error_text[:200] if error_text else 'No details'}"
                            self._logger.debug(f"SSE endpoint {sse_url} failed: {last_error}, trying next...")
                            continue
                        
                        # Last URL failed, set error
                        error_msg = f"SSE connection failed with status {response.status}"
                        if error_text:
                            error_msg += f": {error_text[:500]}"
                        self._sse_error = TransportError(error_msg)
                        self._endpoint_event.set()
                        return
                    
                    # Success! Process SSE stream
                    self._logger.debug(f"SSE connection successful: {sse_url}")
                    
                    # Check response headers for session info (some servers might send it here)
                    # Try multiple header names
                    header_names = ['Location', 'X-Session-Id', 'X-Session-ID', 'Session-Id', 'Session-ID']
                    location_header = None
                    for header_name in header_names:
                        location_header = response.headers.get(header_name)
                        if location_header:
                            break
                    
                    if location_header:
                        session_id = extract_session_id(safe_str(location_header))
                        if session_id:
                            self._session_id = session_id
                            self._message_path = "/message"
                            self._endpoint_event.set()
                            self._logger.debug(f"Extracted session_id from header: {session_id[:20]}...")
                            # Continue to read SSE stream for endpoint event
                
                # Read SSE stream as text, line by line
                buffer = ""
                async for chunk in response.content.iter_any():
                    # Decode chunk and add to buffer
                    chunk_str = chunk.decode('utf-8', errors='replace')
                    buffer += chunk_str
                    
                    # Process complete lines
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        line = line.rstrip('\r')
                        
                        # Skip empty lines and comments (but process event before skipping)
                        if not line or line.startswith(':'):
                            # Empty line signals end of event - process it if we have both event and data
                            if current_event and current_data is not None:
                                await self._process_sse_event(current_event, current_data)
                                current_event = None
                                current_data = None
                            continue
                        
                        # Parse SSE event type
                        if line.startswith('event: '):
                            # Process previous event if any (before starting new event)
                            if current_event and current_data is not None:
                                await self._process_sse_event(current_event, current_data)
                            current_event = line[7:].strip()
                            current_data = None
                            continue
                        
                        # Parse SSE data (can be multi-line)
                        if line.startswith('data: '):
                            data_str = line[6:]  # Remove 'data: ' prefix
                            if current_data is None:
                                current_data = data_str
                            else:
                                # Multi-line data - append with newline
                                current_data += '\n' + data_str
                            
                            # Process immediately if we have both event type and data
                            # This matches the server's format: event: endpoint\n data: /message?session_id=...
                            if current_event and current_data is not None:
                                await self._process_sse_event(current_event, current_data)
                                # Reset state after processing
                                current_event = None
                                current_data = None
                            continue
                
                    # Process any remaining event at end of stream
                    if current_event and current_data is not None:
                        await self._process_sse_event(current_event, current_data)
                    
                    # Successfully connected and processed events
                    return
                    
            except aiohttp.ClientError as e:
                # Network error - try next URL if available
                last_error = str(e)
                if sse_url != sse_urls[-1]:
                    self._logger.debug(f"Network error on {sse_url}: {last_error}, trying next...")
                    continue
                # Last URL failed
                self._sse_error = TransportError(f"SSE connection failed: {last_error}")
                self._endpoint_event.set()
                return
            except Exception as e:
                # Other errors - try next URL if available
                last_error = str(e)
                if sse_url != sse_urls[-1]:
                    self._logger.debug(f"Error on {sse_url}: {last_error}, trying next...")
                    continue
                # Last URL failed
                self._sse_error = e
                self._endpoint_event.set()
                return
        
        # All URLs failed
        if last_error:
            self._sse_error = TransportError(f"All SSE endpoints failed. Last error: {last_error}")
        else:
            self._sse_error = TransportError("All SSE endpoints failed")
        self._endpoint_event.set()
        
        if self._connected:
            for future in self._pending_requests.values():
                future.set_exception(self._sse_error)
            self._pending_requests.clear()
    
    async def _process_sse_event(self, event_type: str, data: str) -> None:
        """Process a complete SSE event with robust parsing."""
        if not event_type or not isinstance(event_type, str):
            return
        
        event_type = event_type.strip().lower()
        data = safe_str(data, "")
        
        if event_type == 'endpoint':
            # Extract session_id from endpoint URI with multiple fallback methods
            try:
                # Method 1: Try URL parsing
                endpoint_uri = unquote(data)
                
                # Handle both absolute URLs and relative paths
                if endpoint_uri.startswith(('http://', 'https://')):
                    parsed = urlparse(endpoint_uri)
                    query_params = parse_qs(parsed.query)
                    self._message_path = parsed.path or "/message"
                else:
                    # Relative path format: /message?session_id=abc123
                    if '?' in endpoint_uri:
                        path_part, query_part = endpoint_uri.split('?', 1)
                        self._message_path = path_part or "/message"
                        query_params = parse_qs(query_part)
                    else:
                        # No query string - just path
                        self._message_path = endpoint_uri or "/message"
                        query_params = {}
                
                # Extract session_id from query params
                session_id = None
                for key in ['session_id', 'sessionId', 'session-id', 'sid']:
                    if key in query_params:
                        session_id = safe_str(query_params[key][0] if query_params[key] else None)
                        if session_id:
                            break
                
                # Method 2: Try utility function extraction
                if not session_id:
                    session_id = extract_session_id(data)
                
                # Method 3: Manual regex extraction
                if not session_id and 'session_id=' in data.lower():
                    try:
                        import re
                        match = re.search(r'session_id["\s:=]+([^\s&?\'"<>]+)', data, re.IGNORECASE)
                        if match:
                            session_id = unquote(match.group(1).strip())
                    except Exception:
                        pass
                
                if session_id:
                    self._session_id = session_id
                    self._message_path = self._message_path or "/message"
                    self._endpoint_event.set()
                    self._logger.debug(f"Extracted session_id from endpoint: {session_id[:20]}...")
                else:
                    # No session_id found - log warning but set event to avoid timeout
                    self._logger.warning(f"No session_id found in endpoint URI: {endpoint_uri}")
                    # Some servers might not send session_id in endpoint event
                    # Set a placeholder and try to continue
                    self._message_path = self._message_path or "/message"
                    self._endpoint_event.set()
                    
            except Exception as e:
                # If endpoint parsing fails, try manual extraction
                self._logger.warning(f"Failed to parse endpoint URI: {e}, data: {data[:100]}")
                session_id = extract_session_id(data)
                if session_id:
                    self._session_id = session_id
                    self._message_path = "/message"
                    self._endpoint_event.set()
                else:
                    # Set event anyway to avoid timeout
                    self._message_path = "/message"
                    self._endpoint_event.set()
                
        elif event_type == 'message':
            # Handle message event (JSON-RPC responses) with robust parsing
            try:
                # Try to parse JSON with multiple fallbacks
                response_data = None
                
                # Method 1: Direct JSON parsing
                try:
                    response_data = json.loads(data)
                except json.JSONDecodeError:
                    # Method 2: Try to fix common JSON issues
                    try:
                        # Remove BOM if present
                        data_clean = data.lstrip('\ufeff')
                        # Try parsing again
                        response_data = json.loads(data_clean)
                    except json.JSONDecodeError:
                        # Method 3: Try to extract JSON from text
                        try:
                            import re
                            json_match = re.search(r'\{.*\}', data, re.DOTALL)
                            if json_match:
                                response_data = json.loads(json_match.group(0))
                        except Exception:
                            pass
                
                if not response_data:
                    self._logger.warning(f"Failed to parse JSON from SSE message: {data[:200]}")
                    return
                
                # Normalize response data
                response_data = normalize_json_response(response_data)
                
                # Extract request ID with type normalization
                request_id_raw = response_data.get('id')
                request_id = normalize_request_id(request_id_raw)
                
                # Handle both integer and string request IDs
                if request_id in self._pending_requests:
                    future = self._pending_requests.pop(request_id)
                    future.set_result(response_data)
                elif request_id_raw in self._pending_requests:
                    # Try with raw ID (might be string)
                    future = self._pending_requests.pop(request_id_raw)
                    future.set_result(response_data)
                else:
                    # Request ID not found - might be a notification or error
                    self._logger.debug(f"Received message with unknown request_id: {request_id}")
                    
            except Exception as e:
                # Log error but don't fail all pending requests
                self._logger.error(f"Error processing SSE message event: {e}")
                # Only fail if it's a critical JSON error
                if isinstance(e, json.JSONDecodeError):
                    self._logger.warning(f"Malformed JSON in SSE message: {data[:200]}")
    
    async def send_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send JSON-RPC request via HTTP POST with robust error handling."""
        if not self._connected or not self.session:
            raise TransportError("Transport not connected")
        
        if not method or not isinstance(method, str):
            raise ValueError("Method must be a non-empty string")
        
        # Increment and normalize request ID
        self._request_id += 1
        request_id = self._request_id
        
        # Build request with normalized data
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": safe_str(method),
        }
        if params is not None:
            # Ensure params is a dict
            if not isinstance(params, dict):
                params = safe_dict(params, {})
            request["params"] = params
        
        future = asyncio.Future()
        self._pending_requests[request_id] = future
        
        try:
            # Use the message path from endpoint event, or default to /message
            message_path = safe_str(self._message_path, "/message")
            session_id = safe_str(self._session_id)
            
            if not session_id:
                # Try to get session_id from headers or other sources
                session_id = safe_str(self.headers.get('X-Session-Id') or self.headers.get('Session-Id'))
                if not session_id:
                    raise TransportError("Session ID not available")
            
            # Build URL with proper encoding
            request_url = f"{self.base_url}{message_path}?session_id={session_id}"
            
            # Ensure headers are all strings
            request_headers = {
                "Content-Type": "application/json",
            }
            for key, value in self.headers.items():
                request_headers[safe_str(key)] = safe_str(value)
            
            self._logger.debug(f"Sending request: {method} (id: {request_id})")
            
            async with self.session.post(
                request_url,
                json=request,
                headers=request_headers,
                allow_redirects=True,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                # Accept multiple success status codes
                if response.status not in (200, 201, 202, 204):
                    # Try to get error details from response
                    error_text = ""
                    try:
                        error_text = await response.text()
                    except Exception:
                        pass
                    
                    # Try to parse JSON error if available
                    error_details = error_text[:500] if error_text else 'No error details'
                    try:
                        error_json = json.loads(error_text)
                        if isinstance(error_json, dict):
                            error_msg = error_json.get('message') or error_json.get('error') or error_details
                            error_details = error_msg
                    except Exception:
                        pass
                    
                    raise TransportError(
                        f"HTTP request failed: {response.status}. "
                        f"URL: {request_url}, Response: {error_details}"
                    )
            
            # Wait for response via SSE with timeout
            try:
                response_data = await asyncio.wait_for(future, timeout=30.0)
            except asyncio.TimeoutError:
                self._pending_requests.pop(request_id, None)
                raise TransportError(f"Request timeout: {method} (id: {request_id})")
            
            # Normalize response data
            response_data = normalize_json_response(response_data)
            
            # Check for JSON-RPC error
            if "error" in response_data:
                error = response_data["error"]
                if isinstance(error, dict):
                    error_msg = safe_str(error.get('message', 'Unknown error'))
                    error_code = safe_str(error.get('code', 'unknown'))
                    raise TransportError(f"JSON-RPC error: {error_msg} (code: {error_code})")
                else:
                    raise TransportError(f"JSON-RPC error: {safe_str(error)}")
            
            result = response_data.get("result", {})
            return safe_dict(result, {})
            
        except asyncio.TimeoutError:
            self._pending_requests.pop(request_id, None)
            raise TransportError(f"Request timeout: {method}")
        except Exception as e:
            self._pending_requests.pop(request_id, None)
            if isinstance(e, TransportError):
                raise
            raise TransportError(f"Error sending request: {e}") from e
    
    async def send_notification(self, method: str, params: Optional[Dict[str, Any]] = None) -> None:
        """Send JSON-RPC notification via HTTP (no response expected) with robust error handling."""
        if not self._connected or not self.session:
            raise TransportError("Transport not connected")
        
        if not method or not isinstance(method, str):
            raise ValueError("Method must be a non-empty string")
        
        # Build request with normalized data
        request = {
            "jsonrpc": "2.0",
            "method": safe_str(method),
        }
        if params is not None:
            # Ensure params is a dict
            if not isinstance(params, dict):
                params = safe_dict(params, {})
            request["params"] = params
        
        try:
            # Use the message path from endpoint event, or default to /message
            message_path = safe_str(self._message_path, "/message")
            session_id = safe_str(self._session_id)
            
            if not session_id:
                # Try to get session_id from headers
                session_id = safe_str(self.headers.get('X-Session-Id') or self.headers.get('Session-Id'))
                if not session_id:
                    raise TransportError("Session ID not available")
            
            # Build URL with proper encoding
            request_url = f"{self.base_url}{message_path}?session_id={session_id}"
            
            # Ensure headers are all strings
            request_headers = {
                "Content-Type": "application/json",
            }
            for key, value in self.headers.items():
                request_headers[safe_str(key)] = safe_str(value)
            
            self._logger.debug(f"Sending notification: {method}")
            
            async with self.session.post(
                request_url,
                json=request,
                headers=request_headers,
                allow_redirects=True,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                # Accept multiple success status codes
                if response.status not in (200, 201, 202, 204):
                    error_text = ""
                    try:
                        error_text = await response.text()
                    except Exception:
                        pass
                    raise TransportError(
                        f"HTTP notification failed: {response.status}. "
                        f"Response: {error_text[:200] if error_text else 'No details'}"
                    )
        except Exception as e:
            if isinstance(e, TransportError):
                raise
            raise TransportError(f"Error sending notification: {e}") from e
    
    async def initialize(self, client_info: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize MCP session with robust data handling."""
        # Normalize client_info to ensure all values are proper types
        normalized_client_info = {}
        if client_info:
            for key, value in client_info.items():
                normalized_client_info[safe_str(key)] = safe_str(value)
        else:
            normalized_client_info = {"name": "mcp-client", "version": "1.0.0"}
        
        params = {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": normalized_client_info
        }
        return await self.send_request("initialize", params)
    
    @property
    def is_connected(self) -> bool:
        """Check if transport is connected."""
        return self._connected and self.session is not None

