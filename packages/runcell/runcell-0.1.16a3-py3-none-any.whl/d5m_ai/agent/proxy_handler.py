"""
Agent Proxy Handler for Remote Backend Architecture

This handler acts as a proxy between the frontend WebSocket and a remote backend server.
Architecture: frontend --- (websocket) --- jupyter backend (proxy) --- (websocket) --- remote server

The jupyter backend now serves as:
- WebSocket proxy for agent/LLM communication with remote server
- Local tool host for shell execution, cell execution, etc.
- Message router between frontend and remote backend
"""

import asyncio
import json
import os
import re
import ssl
import uuid
import websockets
import certifi
from tornado.websocket import WebSocketHandler
from typing import Optional
import tornado

from .config import handler_registry
from .image_processor import ImageProcessor
from .websocket_tool_executor import WebSocketToolExecutor
from .tool_registry import get_tool_meta
from ..utils import build_remote_backend_url
from ..auth.token_handler import get_current_user_token_string
from .._version import __version__ as client_version


class AIJLAgentProxyHandler(WebSocketHandler):
    """
    WebSocket proxy handler that bridges frontend to remote backend server.
    
    Responsibilities:
    • Accept user messages from frontend and forward to remote backend
    • Handle local tool execution (cell execution, shell commands, etc.) 
    • Route tool results between frontend, local tools, and remote backend
    • Manage WebSocket connections to both frontend and remote backend
    • Handle image processing and temporary files locally
    """

    def initialize(self, **kwargs):
        self.connection_id: str = str(uuid.uuid4())
        self.current_request_id: str | None = None

        # Frontend WebSocket connection state
        self._is_closed = False
        self.waiter: asyncio.Future | None = None
        
        # Remote backend connection
        self.remote_websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.remote_url = build_remote_backend_url("agent")
        self._remote_connection_lock = asyncio.Lock()
        
        # Server base URL for API calls
        self.server_url = os.environ.get("SERVER_URL", "http://localhost:8888")
        
        # Token-based authentication (replaces access key system)
        print("[PROXY] Token authentication enabled - will forward tokens to remote backend")
        
        # Initialize local components (for tool execution)
        self.image_processor = ImageProcessor(self.connection_id, self.server_url)
        self.tool_executor = WebSocketToolExecutor(self)

        # Track pending frontend requests for agent mode detection
        self._pending_frontend_requests = set()
        
        # Flag to prevent duplicate disconnection notifications
        self._remote_disconnection_notified = False
        
        # Register this handler globally
        handler_registry[self.connection_id] = self

    def _get_user_token(self) -> Optional[str]:
        """
        Get user token from query param (preferred for remote/ephemeral servers) or local file.
        
        Returns:
            User token if found, None otherwise
        """
        token_param = None
        try:
            token_param = self.get_query_argument("token", default=None)
        except Exception:
            token_param = None

        if token_param and token_param.startswith("eyJ") and token_param.count(".") == 2:
            print("[PROXY] ✅ Found user token in WebSocket query param")
            return token_param

        token = get_current_user_token_string()
        if token:
            print("[PROXY] ✅ Found user token in local file")
            return token

        print("[PROXY] ❌ No user token found")
        return None

    def _is_remote_connection_closed(self) -> bool:
        """Check if the remote WebSocket connection is closed."""
        if self.remote_websocket is None:
            return True
        
        try:
            # Check if the connection is closed
            # For websockets library, use the state property
            from websockets.protocol import State
            return self.remote_websocket.state != State.OPEN
        except Exception as e:
            print(f"[PROXY] Error checking connection state: {e}")
            # If we can't determine the state, assume it's open to avoid reconnecting unnecessarily
            return False

    def check_origin(self, origin: str) -> bool:
        # NOTE: relax CORS – adjust for production
        return True

    async def open(self):
        """Handle WebSocket connection opening from frontend."""
        # Get user token from local file
        user_token = self._get_user_token()
        
        if not user_token:
            print("[PROXY] ❌ No authentication token available")
            await self._safe_write_message({
                "type": "system",
                "msg": "error", 
                "error": "Authentication required. Please log in to use this service."
            })
            return
        
        # Store token for remote backend connection
        self.user_token = user_token
        
        # Tell the frontend we are ready
        await self._safe_write_message({
            "type": "system", 
            "msg": "ready", 
            "connection_id": self.connection_id
        })
        
        # Establish connection to remote backend
        await self._connect_to_remote_backend()

    async def _connect_to_remote_backend(self):
        """Establish WebSocket connection to remote backend server."""
        try:
            async with self._remote_connection_lock:
                if self.remote_websocket is None or self._is_remote_connection_closed():
                    # Add user token to URL for authentication
                    connection_url = self.remote_url
                    params = []

                    if hasattr(self, 'user_token') and self.user_token:
                        params.append(f"token={self.user_token}")
                        print(f"[PROXY] Connecting to remote backend with user authentication")
                    else:
                        print(f"[PROXY] Connecting to remote backend without authentication")
                    
                    # Add client version
                    params.append(f"client_version={client_version}")

                    if params:
                        separator = "&" if "?" in connection_url else "?"
                        connection_url = f"{connection_url}{separator}{'&'.join(params)}"
                    
                    redacted_url = re.sub(r"(token=)[^&]+", r"\1<redacted>", connection_url)
                    print(f"[PROXY] Remote URL: {redacted_url}")
                    
                    # Only create SSL context for wss:// connections
                    ssl_context = None
                    if connection_url.startswith("wss://"):
                        try:
                            ssl_context = ssl.create_default_context(cafile=certifi.where())
                            print(f"[PROXY] Using certifi certificate bundle for WebSocket SSL verification")
                        except Exception as e:
                            print(f"[PROXY] Failed to create SSL context with certifi: {e}")
                            # Fallback to default SSL context
                            ssl_context = ssl.create_default_context()
                    
                    # Connect with timeout to fail fast on network errors
                    try:
                        if connection_url.startswith("wss://"):
                            print(f"[PROXY] Connecting to secure WebSocket (wss://) with SSL context")
                            self.remote_websocket = await asyncio.wait_for(
                                websockets.connect(connection_url, ssl=ssl_context),
                                timeout=5.0  # 5 second timeout
                            )
                        else:
                            # Plain ws:// connection - no SSL context needed
                            print(f"[PROXY] Connecting to plain WebSocket (ws://) without SSL")
                            self.remote_websocket = await asyncio.wait_for(
                                websockets.connect(connection_url),
                                timeout=5.0  # 5 second timeout
                            )
                    except asyncio.TimeoutError:
                        raise Exception("Connection timeout - remote backend is not responding")
                    
                    # Reset the disconnection notified flag on successful connection
                    self._remote_disconnection_notified = False
                    
                    # Start listening for messages from remote backend
                    asyncio.create_task(self._listen_to_remote_backend())
                    
                    # Start ping task to monitor connection health
                    asyncio.create_task(self._ping_remote_backend())
                    
                    print(f"[PROXY] Connected to remote backend successfully")
        except Exception as e:
            print(f"[PROXY] Failed to connect to remote backend: {e}")
            # Clear the websocket reference
            self.remote_websocket = None

    async def _listen_to_remote_backend(self):
        """Listen for messages from remote backend and forward to frontend."""
        try:
            async for message in self.remote_websocket:
                try:
                    data = json.loads(message)
                    await self._handle_remote_backend_message(data)
                except json.JSONDecodeError as e:
                    print(f"[PROXY] Invalid JSON from remote backend: {e}")
                except Exception as e:
                    print(f"[PROXY] Error handling remote backend message: {e}")
        except websockets.exceptions.ConnectionClosed:
            print("[PROXY] Remote backend connection closed")
            # Only notify if we haven't already
            if not self._remote_disconnection_notified:
                self._remote_disconnection_notified = True
                # Notify frontend that remote connection is closed
                await self._safe_write_message({
                    "type": "system",
                    "msg": "remote_disconnected",
                    "error": "Connection to remote backend was closed"
                })
            # Clear the remote websocket reference
            self.remote_websocket = None
        except Exception as e:
            print(f"[PROXY] Error listening to remote backend: {e}")
            # Only notify if we haven't already
            if not self._remote_disconnection_notified:
                self._remote_disconnection_notified = True
                # Notify frontend of the error
                await self._safe_write_message({
                    "type": "system",
                    "msg": "remote_error",
                    "error": f"Error in remote backend connection: {str(e)}"
                })
            # Clear the remote websocket reference
            self.remote_websocket = None

    async def _handle_remote_backend_message(self, data):
        """Handle messages from remote backend."""
        msg_type = data.get("type")
        
        # Reduce log verbosity for streaming messages
        if msg_type not in ["assistant_chunk", "reasoning_chunk"]:
            print(f"[PROXY] Received message from remote backend: {msg_type}")
        
        if msg_type in ["assistant_chunk", "reasoning_chunk", "assistant_complete", "system", "tool_call", "tool_call_args_update", "tool_call_output"]:
            # Forward AI responses directly to frontend (includes reasoning chunks for reasoning models)
            await self._safe_write_message(data)
            
        elif msg_type == "tool_call_request":
            # Handle tool call request from remote backend
            print(f"[PROXY] Handling tool call request: {data.get('tool_name')}")
            await self._handle_tool_call_request(data)
            
        elif msg_type == "shell_execute":
            # Handle shell execute as local tool execution (not frontend request)
            print(f"[PROXY] Handling shell execute as local tool")
            await self._handle_shell_execute_locally(data)
            
        elif msg_type == "get_image_base64":
            # Handle image base64 request from remote backend
            print(f"[PROXY] Handling get_image_base64 request")
            await self._handle_get_image_base64_request(data)
            
        elif msg_type in ["cell_execute", "rerun_all_cells", "edit_cell", "insert_markdown_cell", 
                         "shell_permission_request", "rerun_all_cells_permission_request"]:
            # Handle frontend request messages from remote backend
            await self._safe_write_message(data)
            
        else:
            # Forward other messages to frontend
            print(f"[PROXY] Forwarding unknown message type {msg_type} to frontend")
            print(f"[PROXY] Full message data: {data}")
            await self._safe_write_message(data)

    async def _handle_shell_execute_locally(self, data):
        """Handle shell execute request from remote backend by executing locally on proxy server."""
        try:
            command = data.get("command", "")
            request_id = data.get("request_id")
            
            print(f"[PROXY] Executing shell command locally: {command}")
            
            # Execute shell command using proxy's tool executor
            result = await self.tool_executor.shell_execute(command)
            
            # Send result back to remote backend
            await self._send_to_remote_backend({
                "type": "shell_execute_result",
                "request_id": request_id,
                "result": result
            })
            
        except Exception as e:
            print(f"[PROXY] Error executing shell command: {e}")
            # Send error back to remote backend
            await self._send_to_remote_backend({
                "type": "shell_execute_result",
                "request_id": data.get("request_id"),
                "result": f"Error executing shell command: {e}"
            })

    async def _check_agent_mode_timeout(self, request_id: str, tool_name: str):
        """Check if we're in agent mode by timing out on cell_execute requests."""
        await asyncio.sleep(10)  # Wait 10 seconds
        
        # If the request_id is still tracked, it means no response came back
        # This indicates agent mode where frontend doesn't properly handle cell_execute
        if hasattr(self, '_pending_frontend_requests') and request_id in self._pending_frontend_requests:
            print(f"[PROXY] Detected agent mode - frontend didn't respond to {tool_name} in 10 seconds")
            
            # Send error response
            error_result = "Error: cell_execute requires a connected frontend with a Jupyter kernel. In agent mode, please use shell_execute for command-line operations instead."
            
            await self._send_to_remote_backend({
                "type": "tool_call_result",
                "request_id": request_id,
                "tool_name": tool_name,
                "result": error_result
            })
            
            # Clean up the pending request
            self._pending_frontend_requests.discard(request_id)

    async def _handle_tool_call_request(self, data):
        """Handle tool call request from remote backend by executing locally."""
        try:
            tool_name = data.get("tool_name")
            tool_args = data.get("tool_args", {})
            request_id = data.get("request_id")
            
            print(f"[PROXY] Handling tool call request: {tool_name} with args: {tool_args}")
            tool_meta = get_tool_meta(tool_name)
            if not tool_meta:
                await self._send_to_remote_backend({
                    "type": "tool_call_result",
                    "request_id": request_id,
                    "tool_name": tool_name,
                    "result": f"Error: Unknown tool '{tool_name}'"
                })
                return

            # Permission-gated tools can be routed through an executor even if their natural
            # location is frontend. This keeps permission concerns separate from transport.
            if tool_meta.requires_permission and tool_meta.permission_executor:
                print(f"[PROXY] Executing permission-gated tool via executor: {tool_name}")
                result = await self._execute_local_tool(
                    tool_name,
                    tool_args,
                    request_id,
                    tool_meta,
                    executor_override=tool_meta.permission_executor
                )
                await self._send_to_remote_backend({
                    "type": "tool_call_result",
                    "request_id": request_id,
                    "tool_name": tool_name,
                    "result": result
                })
                return

            if tool_meta.location == "frontend":
                print(f"[PROXY] Forwarding frontend-interactive tool {tool_name} to frontend with request_id: {request_id}")
                frontend_message = {
                    "type": tool_meta.message_type or tool_name,
                    "request_id": request_id,
                    "connection_id": self.connection_id,
                    **tool_args
                }
                print(f"[PROXY] Frontend message: {frontend_message}")

                success = await self._safe_write_message(frontend_message)
                if success:
                    print(f"[PROXY] Frontend message sent. Waiting for response...")
                    if tool_meta.timeout_on_pending:
                        self._pending_frontend_requests.add(request_id)
                        asyncio.create_task(self._check_agent_mode_timeout(request_id, tool_name))
                else:
                    error_result = tool_meta.frontend_error or f"Error: {tool_name} requires a connected frontend with a Jupyter notebook."
                    await self._send_to_remote_backend({
                        "type": "tool_call_result",
                        "request_id": request_id,
                        "tool_name": tool_name,
                        "result": error_result
                    })

            elif tool_meta.location == "proxy":
                print(f"[PROXY] Executing local tool: {tool_name}")
                result = await self._execute_local_tool(tool_name, tool_args, request_id, tool_meta)
                await self._send_to_remote_backend({
                    "type": "tool_call_result",
                    "request_id": request_id,
                    "tool_name": tool_name,
                    "result": result
                })
            else:
                error_result = f"Error: {tool_name} should be handled by the remote backend"
                await self._send_to_remote_backend({
                    "type": "tool_call_result",
                    "request_id": request_id,
                    "tool_name": tool_name,
                    "result": error_result
                })
            
        except Exception as e:
            print(f"[PROXY] Error handling tool call request: {e}")
            # Send error back to remote backend
            await self._send_to_remote_backend({
                "type": "tool_call_result",
                "request_id": data.get("request_id"),
                "tool_name": data.get("tool_name"),
                "result": f"Error executing tool: {e}"
            })

    @staticmethod
    def _filter_tool_args(executor, tool_args: dict) -> dict:
        """Filter provided args to those accepted by the executor, warn on drops."""
        import inspect

        try:
            sig = inspect.signature(executor)
        except (TypeError, ValueError):
            return tool_args

        filtered = {}
        for name in sig.parameters.keys():
            if name in tool_args:
                filtered[name] = tool_args[name]

        # Warn if arguments were dropped unexpectedly
        dropped = set(tool_args.keys()) - set(filtered.keys())
        if dropped:
            print(f"[PROXY] Warning: Dropped unsupported args for {getattr(executor, '__name__', 'executor')}: {sorted(dropped)}")
        return filtered

    @staticmethod
    def _apply_arg_aliases(tool_name: str, tool_args: dict) -> dict:
        """
        Apply known alias mappings (e.g., dir -> dir_path for list_dir).
        Keeps original keys so upstream logic remains backward compatible.
        """
        aliases = {
            "list_dir": {"dir": "dir_path"},
        }
        mapped = dict(tool_args) if tool_args else {}
        alias_map = aliases.get(tool_name, {})
        for src, dest in alias_map.items():
            if src in mapped and dest not in mapped:
                mapped[dest] = mapped[src]
        return mapped

    async def _execute_local_tool(self, tool_name: str, tool_args: dict, request_id: str = None, tool_meta=None, executor_override: str | None = None) -> str:
        """Execute a proxy-local tool using the WebSocket tool executor."""
        if tool_meta is None:
            tool_meta = get_tool_meta(tool_name)

        if not tool_meta:
            return f"Unknown tool: {tool_name}"
        # Permission-gated tools may specify an override executor even if their
        # declared location is frontend. Allow that path.
        if executor_override is None and tool_meta.location != "proxy":
            return f"Unknown tool: {tool_name}"

        executor_name = executor_override or tool_meta.executor
        executor = getattr(self.tool_executor, executor_name, None) if executor_name else None
        if not executor:
            return f"Unknown tool: {tool_name}"

        normalized_args = self._apply_arg_aliases(tool_name, tool_args)
        filtered_args = self._filter_tool_args(executor, normalized_args)
        return await executor(**filtered_args)

    async def _send_to_remote_backend(self, data):
        """Send message to remote backend."""
        try:
            if self.remote_websocket and not self._is_remote_connection_closed():
                await self.remote_websocket.send(json.dumps(data))
            else:
                await self._connect_to_remote_backend()
                if self.remote_websocket and not self._is_remote_connection_closed():
                    await self.remote_websocket.send(json.dumps(data))
                else:
                    # Connection failed, notify frontend immediately
                    raise Exception("Failed to establish connection to remote backend")
        except Exception as e:
            print(f"[PROXY] Error sending to remote backend: {e}")
            import traceback
            traceback.print_exc()
            
            # Clear the connection on any error
            self.remote_websocket = None
            
            # Notify frontend of the error immediately
            error_message = str(e)
            if "nodename nor servname provided" in error_message or "getaddrinfo" in error_message:
                error_message = "Failed to connect to remote backend: Network connection error. Please check your internet connection."
            elif "Connection refused" in error_message:
                error_message = "Failed to connect to remote backend: Service unavailable. Please try again later."
            elif "timeout" in error_message.lower():
                error_message = "Failed to connect to remote backend: Connection timeout. Please check your network connection."
            else:
                error_message = f"Failed to connect to remote backend: {error_message}"
            
            await self._safe_write_message({
                "type": "error",
                "error": error_message,
                "request_id": data.get("request_id")
            })

    async def _safe_write_message(self, data):
        """Safely write a message to the frontend WebSocket with error handling."""
        if self._is_closed:
            return False
        
        try:
            await self.write_message(json.dumps(data))
            return True
        except tornado.websocket.WebSocketClosedError:
            self._is_closed = True
            return False
        except Exception as e:
            print(f"Error writing to frontend WebSocket: {str(e)}")
            return False

    async def on_message(self, raw: str):
        """
        Handle incoming WebSocket messages from frontend.
        Route appropriately between local tools and remote backend.
        """
        try:
            msg = json.loads(raw)
            msg_type = msg.get("type")

            if msg_type == "user":
                # Forward user messages to remote backend for AI processing
                await self._forward_to_remote_backend(msg)

            elif msg_type == "cancel":
                # Forward cancellation to remote backend
                await self._forward_to_remote_backend(msg)
                
            elif msg_type in ["cell_result", "shell_permission_response", "rerun_all_cells_result",
                             "edit_cell_result", "edit_markdown_cell_result", "insert_markdown_cell_result", "rerun_all_cells_permission_response",
                             "open_tab_result", "insert_cell_result", "run_cell_result", "delete_cell_result", "run_long_terminal_result"]:
                # Handle local tool results
                await self._handle_local_tool_result(msg)
                
            elif msg_type == "ping_remote":
                # Simple ping to check if remote is connected
                if self.remote_websocket is None or self._is_remote_connection_closed():
                    # Attempt to establish the remote connection before reporting status
                    await self._connect_to_remote_backend()
                is_connected = self.remote_websocket is not None and not self._is_remote_connection_closed()
                await self._safe_write_message({
                    "type": "pong_remote",
                    "connected": is_connected
                })
                
            elif msg_type == "connection_test":
                # Handle connection test messages from frontend - don't forward to remote backend
                # This is just a health check, so we can ignore it
                pass
                
            else:
                # Forward other message types to remote backend
                await self._forward_to_remote_backend(msg)

        except Exception as e:
            print(f"Error in on_message: {e}")
            import traceback
            traceback.print_exc()

    async def _forward_to_remote_backend(self, msg):
        """Forward message to remote backend."""
        # Add connection ID for routing
        msg["connection_id"] = self.connection_id
        
        # Ensure connection to remote backend
        if not self.remote_websocket or self._is_remote_connection_closed():
            await self._connect_to_remote_backend()
        
        await self._send_to_remote_backend(msg)

    async def _handle_local_tool_result(self, msg):
        """Handle results from local tool execution (from frontend)."""
        msg_type = msg.get("type")
        conn_id = msg.get("connection_id", self.connection_id)
        print(f"[Proxy] hander message type {msg_type}")
        
        # Locate the correct handler
        handler = handler_registry.get(conn_id, self)
        
        if msg_type == "cell_result":
            result = msg.get("result", "No result provided")
            request_id = msg.get("request_id")
            
            if request_id:
                # This is from a remote backend tool call, forward it back
                print(f"[PROXY] Forwarding cell_result to remote backend with request_id: {request_id}")
                
                # Clean up pending request tracking
                if hasattr(self, '_pending_frontend_requests'):
                    self._pending_frontend_requests.discard(request_id)
                
                # Process the result to check for image data
                if '"image/png"' in result:
                    print(f"[PROXY] Detected image/png data in cell_result")
                    modified_result = await handler.image_processor.replace_base64_with_urls(result)
                    result = modified_result
                
                await self._send_to_remote_backend({
                    "type": "tool_call_result",
                    "request_id": request_id,
                    "tool_name": "cell_execute",
                    "result": result
                })
            else:
                # Process the result to check for image data (local execution)
                await self._process_cell_result(handler, result)
            
        elif msg_type == "edit_cell_result":
            result = msg.get("result", "No result provided")
            request_id = msg.get("request_id")
            
            # Process the result to check for image data
            if '"image/png"' in result:
                modified_result = await handler.image_processor.replace_base64_with_urls(result)
                result = modified_result
            
            # Always forward the result back to remote backend with request_id
            if request_id:
                await self._send_to_remote_backend({
                    "type": "tool_call_result",
                    "request_id": request_id,
                    "tool_name": "edit_cell",
                    "result": result
                })
            else:
                # Fallback: treat as local tool execution result
                if handler.waiter and not handler.waiter.done():
                    handler.waiter.set_result(result)
            
        elif msg_type == "edit_markdown_cell_result":
            result = msg.get("result", "No result provided")
            request_id = msg.get("request_id")

            if '"image/png"' in result:
                modified_result = await handler.image_processor.replace_base64_with_urls(result)
                result = modified_result

            if request_id:
                await self._send_to_remote_backend({
                    "type": "tool_call_result",
                    "request_id": request_id,
                    "tool_name": "edit_markdown_cell",
                    "result": result
                })
            else:
                if handler.waiter and not handler.waiter.done():
                    handler.waiter.set_result(result)
                else:
                    print(f"[PROXY] Handler waiter not available for edit_markdown_cell result")
            
        elif msg_type == "shell_permission_response":
            allowed = msg.get("allowed", False) 
            request_id = msg.get("request_id")
            print(f"[PROXY] Received shell permission response: allowed={allowed}, request_id={request_id}")
            
            # Set the permission response to the waiter
            if handler.waiter and not handler.waiter.done():
                handler.waiter.set_result({"allowed": allowed, "request_id": request_id})
            else:
                print(f"[PROXY] Cannot set shell permission response - waiter not available")
                
        elif msg_type == "rerun_all_cells_result":
            result = msg.get("result", "No result provided")
            request_id = msg.get("request_id")
            
            # If this result is from a remote backend tool call, forward it back
            if request_id:
                print(f"[PROXY] Forwarding rerun_all_cells_result to remote backend")
                await self._send_to_remote_backend({
                    "type": "tool_call_result",
                    "request_id": request_id,
                    "tool_name": "rerun_all_cells",
                    "result": result
                })
            else:
                # Set the result directly to the waiter (for local calls)
                if handler.waiter and not handler.waiter.done():
                    handler.waiter.set_result(result)
                else:
                    print(f"[PROXY] Handler waiter not available for {msg_type}")
                
        elif msg_type == "insert_markdown_cell_result":
            success = msg.get("success", False)
            request_id = msg.get("request_id")
            
            if success:
                result = msg.get("message", "Markdown cell inserted successfully")
            else:
                error = msg.get("error", "Unknown error occurred")
                result = f"Error inserting markdown cell: {error}"
            
            # If this result is from a remote backend tool call, forward it back
            if request_id:
                print(f"[PROXY] Forwarding insert_markdown_cell_result to remote backend")
                await self._send_to_remote_backend({
                    "type": "tool_call_result",
                    "request_id": request_id,
                    "tool_name": "insert_markdown_cell",
                    "result": result
                })
            else:
                # Set the result directly to the waiter (for local calls)
                if handler.waiter and not handler.waiter.done():
                    handler.waiter.set_result(result)
                else:
                    print(f"[PROXY] Handler waiter not available for insert markdown cell result")
                
        elif msg_type == "rerun_all_cells_permission_response":
            allowed = msg.get("allowed", False)
            request_id = msg.get("request_id")
            print(f"[PROXY] Received rerun permission response: allowed={allowed}, request_id={request_id}")
            
            # Set the permission response to the waiter
            if handler.waiter and not handler.waiter.done():
                handler.waiter.set_result({"allowed": allowed, "request_id": request_id})
            else:
                print(f"[PROXY] Cannot set rerun permission response - waiter not available")
            
        elif msg_type == "open_tab_result":
            success = msg.get("success", False)
            request_id = msg.get("request_id")
            if success:
                result = msg.get("result", "file is opened in tab")
            else:
                result = msg.get("error", "Unknown error occurred")
            if request_id:
                print(f"[PROXY] Forwarding open_tab to remote backend")
                await self._send_to_remote_backend({
                    "type": "tool_call_result",
                    "request_id": request_id,
                    "tool_name": "open_tab",
                    "result": result
                })
            if handler.waiter and not handler.waiter.done():
                handler.waiter.set_result(result)
            else:
                print(f"[PROXY] Handler waiter not available for open tab result")
                
        elif msg_type == "insert_cell_result":
            result = msg.get("result", "No result provided")
            request_id = msg.get("request_id")
            
            if request_id:
                print(f"[PROXY] Forwarding insert_cell_result to remote backend")
                await self._send_to_remote_backend({
                    "type": "tool_call_result",
                    "request_id": request_id,
                    "tool_name": "insert_cell",
                    "result": result
                })
            else:
                if handler.waiter and not handler.waiter.done():
                    handler.waiter.set_result(result)
                else:
                    print(f"[PROXY] Handler waiter not available for insert_cell result")
                    
        elif msg_type == "run_cell_result":
            result = msg.get("result", "No result provided")
            request_id = msg.get("request_id")
            
            # Process the result to check for image data
            if '"image/png"' in result:
                print(f"[PROXY] Detected image/png data in run_cell_result")
                modified_result = await handler.image_processor.replace_base64_with_urls(result)
                result = modified_result
            
            if request_id:
                print(f"[PROXY] Forwarding run_cell_result to remote backend")
                await self._send_to_remote_backend({
                    "type": "tool_call_result",
                    "request_id": request_id,
                    "tool_name": "run_cell",
                    "result": result
                })
            else:
                if handler.waiter and not handler.waiter.done():
                    handler.waiter.set_result(result)
                else:
                    print(f"[PROXY] Handler waiter not available for run_cell result")
                    
        elif msg_type == "delete_cell_result":
            result = msg.get("result", "No result provided")
            request_id = msg.get("request_id")
            
            if request_id:
                print(f"[PROXY] Forwarding delete_cell_result to remote backend")
                await self._send_to_remote_backend({
                    "type": "tool_call_result",
                    "request_id": request_id,
                    "tool_name": "delete_cell",
                    "result": result
                })
            else:
                if handler.waiter and not handler.waiter.done():
                    handler.waiter.set_result(result)
                else:
                    print(f"[PROXY] Handler waiter not available for delete_cell result")

        elif msg_type == "run_long_terminal_result":
            success = msg.get("success", False)
            request_id = msg.get("request_id")
            if success:
                result = msg.get("result", "Terminal created")
            else:
                result = msg.get("error", "Unknown error occurred")
            if request_id:
                print(f"[PROXY] Forwarding run_long_terminal_result to remote backend")
                await self._send_to_remote_backend({
                    "type": "tool_call_result",
                    "request_id": request_id,
                    "tool_name": "run_long_terminal",
                    "result": result
                })
            else:
                if handler.waiter and not handler.waiter.done():
                    handler.waiter.set_result(result)
                else:
                    print(f"[PROXY] Handler waiter not available for run_long_terminal result")



    def _is_local_image_service_url(self, image_url: str) -> bool:
        """Check if the image URL is pointing to the local Jupyter server's image service."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(image_url)
            
            # Check if it's our image service path
            if "/d5m-ai/image-service/" not in parsed.path:
                return False
            
            # Check if it's localhost or local IP
            hostname = parsed.hostname
            if not hostname:
                return False
                
            # Consider these as local hosts
            local_hosts = {
                'localhost',
                '127.0.0.1',
                '::1',
                '0.0.0.0'
            }
            
            # Check if hostname is explicitly local
            if hostname.lower() in local_hosts:
                return True
            
            # Additional check: if port matches common Jupyter ports and hostname looks local
            port = parsed.port
            jupyter_ports = {8888, 8889, 8890, 8891}  # Common Jupyter ports
            
            if port in jupyter_ports and (hostname.startswith('127.') or hostname.startswith('10.') or hostname.startswith('192.168.')):
                return True
                
            return False
            
        except Exception as e:
            print(f"[PROXY] Error checking if URL is local: {e}")
            return False

    async def _process_cell_result(self, handler, result):
        """Process cell results and handle image data conversion for display."""
        try:
            print(f"[PROXY] Processing cell result of length: {len(result) if result else 0}")
            
            # Check if result contains image data that needs to be converted to URLs
            if '"image/png"' in result:
                print(f"[PROXY] Detected image/png data in cell result")
                # Replace base64 data with URLs in the result
                modified_result = await handler.image_processor.replace_base64_with_urls(result)
                
                # Set the modified result to unblock the function call
                if handler.waiter and not handler.waiter.done():
                    handler.waiter.set_result(modified_result)
                else:
                    print(f"[PROXY] Handler waiter not available or already done")
            else:
                # No image, just set the result directly
                if handler.waiter and not handler.waiter.done():
                    handler.waiter.set_result(result)
                else:
                    print(f"[PROXY] Handler waiter not available or already done")
                    
        except Exception as e:
            print(f"[PROXY] Error processing cell result: {e}")
            import traceback
            traceback.print_exc()
            # Fail safely by returning the original result
            if handler.waiter and not handler.waiter.done():
                handler.waiter.set_result(result)

    async def _handle_get_image_base64_request(self, data):
        """Handle get_image_base64 request from remote backend."""
        try:
            image_url = data.get("image_url")
            request_id = data.get("request_id")
            
            print(f"[PROXY] Processing get_image_base64 request for URL: {image_url[:100]}...")
            
            if not image_url or not request_id:
                # Send error response
                await self._send_to_remote_backend({
                    "type": "image_base64_result",
                    "request_id": request_id,
                    "success": False,
                    "error": "Missing image_url or request_id"
                })
                return
            
            # Try to fetch the image using normal HTTP first
            try:
                import base64
                import httpx
                
                # Normal path: try HTTP request first
                headers = {
                    'User-Agent': 'httpx/proxy-client',
                }
                async with httpx.AsyncClient() as client:
                    response = await client.get(image_url, headers=headers, follow_redirects=True)
                    response.raise_for_status()
                    image_data = response.content
                    print(f"[PROXY] Successfully retrieved image via HTTP, size: {len(image_data)} bytes")
                
                # Convert to base64
                image_base64 = base64.b64encode(image_data).decode('utf-8')
                
                print(f"[PROXY] Successfully retrieved image, size: {len(image_data)} bytes")
                
                # Send success response
                await self._send_to_remote_backend({
                    "type": "image_base64_result",
                    "request_id": request_id,
                    "success": True,
                    "base64_data": image_base64
                })
                
            except Exception as fetch_error:
                print(f"[PROXY] HTTP request failed: {fetch_error}")
                
                # Fallback: try direct file access for localhost URLs only
                try:
                    from urllib.parse import urlparse
                    import os
                    
                    if self._is_local_image_service_url(image_url):
                        print(f"[PROXY] Attempting fallback to direct file access for localhost URL")
                        
                        parsed_url = urlparse(image_url)
                        filename = parsed_url.path.split("/d5m-ai/image-service/")[-1]
                        
                        from ..image.handler import IMAGE_STORAGE_DIR
                        image_path = os.path.join(IMAGE_STORAGE_DIR, filename)
                        
                        if os.path.exists(image_path) and os.path.isfile(image_path):
                            with open(image_path, "rb") as f:
                                image_data = f.read()
                            
                            image_base64 = base64.b64encode(image_data).decode('utf-8')
                            print(f"[PROXY] Fallback successful: read image from filesystem, size: {len(image_data)} bytes")
                            
                            # Send success response
                            await self._send_to_remote_backend({
                                "type": "image_base64_result",
                                "request_id": request_id,
                                "success": True,
                                "base64_data": image_base64
                            })
                            return
                        else:
                            print(f"[PROXY] Fallback failed: image file not found at {image_path}")
                    
                    # If not localhost or fallback failed, send original error
                    raise fetch_error
                        
                except Exception as fallback_error:
                    print(f"[PROXY] Fallback also failed: {fallback_error}")
                    # Fall through to send original HTTP error
                
                # Send error response with original HTTP error
                await self._send_to_remote_backend({
                    "type": "image_base64_result",
                    "request_id": request_id,
                    "success": False,
                    "error": f"Failed to fetch image: {str(fetch_error)}"
                })
                
        except Exception as e:
            print(f"[PROXY] Error handling get_image_base64 request: {e}")
            import traceback
            traceback.print_exc()
            
            # Send error response
            await self._send_to_remote_backend({
                "type": "image_base64_result",
                "request_id": data.get("request_id"),
                "success": False,
                "error": f"Internal error: {str(e)}"
            })

    def on_close(self):
        """Handle WebSocket connection closing."""
        # Set closed flag
        self._is_closed = True
        
        # Close remote backend connection
        if self.remote_websocket and not self._is_remote_connection_closed():
            asyncio.create_task(self.remote_websocket.close())
        
        # Deregister and clean up
        handler_registry.pop(self.connection_id, None)
        if self.waiter and not self.waiter.done():
            self.waiter.cancel()
        self.waiter = None
        
        # Clean up image processor
        self.image_processor.cleanup_images()

    async def _ping_remote_backend(self):
        """Periodically ping the remote backend to detect disconnections."""
        try:
            while self.remote_websocket and not self._is_remote_connection_closed():
                try:
                    # Send ping and wait for pong
                    pong_waiter = await self.remote_websocket.ping()
                    await asyncio.wait_for(pong_waiter, timeout=5)  # Reduced to 5 seconds
                    await asyncio.sleep(10)  # Ping every 10 seconds
                except (asyncio.TimeoutError, websockets.exceptions.ConnectionClosed) as e:
                    print(f"[PROXY] Remote backend ping failed: {e}")
                    # Close and clear the connection
                    if self.remote_websocket:
                        await self.remote_websocket.close()
                    self.remote_websocket = None
                    break
                except Exception as e:
                    print(f"[PROXY] Error in ping task: {e}")
                    break
        except Exception as e:
            print(f"[PROXY] Ping task error: {e}") 
