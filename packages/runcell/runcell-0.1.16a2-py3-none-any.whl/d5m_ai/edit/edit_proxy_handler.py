"""
Edit Proxy Handler for Remote Backend Architecture

This handler acts as a proxy between the frontend WebSocket and a remote backend server.
Architecture: frontend --- (websocket) --- jupyter backend (proxy) --- (websocket) --- remote server

The jupyter backend now serves as:
- WebSocket proxy for edit/LLM communication with remote server
- Local tool host for shell execution, cell execution, etc.
- Message router between frontend and remote backend
"""

import asyncio
import json
import os
import ssl
import certifi
import uuid
import websockets
from tornado.websocket import WebSocketHandler
from typing import Optional
import tornado

from .connection_manager import ConnectionManager
from .image_processor import ImageProcessor
from .shell_executor import ShellExecutor
from ..utils import build_remote_backend_url
from ..auth.token_handler import get_current_user_token_string


class EditWebSocketToolExecutor:
    """
    Tool executor for edit module that handles local tools via WebSocket communication.
    Handles cell execution, shell commands, file operations, etc.
    """
    
    def __init__(self, handler):
        self.handler = handler
        self.shell_executor = ShellExecutor()
        self.image_processor = ImageProcessor(handler.server_url)
    
    async def cell_execute(self, code: str) -> str:
        """Execute a code cell and return the result."""
        print(f"[EDIT-PROXY] Executing cell with code: {code[:100]}...")
        
        # Generate request ID and send cell execution request
        request_id = str(uuid.uuid4())
        await self.handler._safe_write_message({
            "type": "cell_execute",
            "code": code,
            "request_id": request_id,
            "connection_id": self.handler.connection_id,
        })
        
        # Wait for result
        self.handler.waiter = asyncio.get_running_loop().create_future()
        try:
            result = await asyncio.wait_for(self.handler.waiter, timeout=90.0)
            print(f"[EDIT-PROXY] Cell execution result: {result[:100]}...")
            return result
        except asyncio.TimeoutError:
            return "Error: Cell execution timed out"
        finally:
            self.handler.waiter = None
    
    async def shell_execute(self, command: str) -> str:
        """Execute a shell command and return the result."""
        print(f"[EDIT-PROXY] Executing shell command: {command}")
        
        # Use shell executor to handle permission and execution
        result = await self.shell_executor.execute_command(self.handler, command)
        print(f"[EDIT-PROXY] Shell execution result: {result[:100]}...")
        return result
    
    async def edit_cell(self, cell_index: int, code: str, rerun: bool = False) -> str:
        """Edit a cell and optionally rerun it."""
        print(f"[EDIT-PROXY] Editing cell {cell_index}, rerun={rerun}")
        
        # Generate request ID and send edit cell request
        request_id = str(uuid.uuid4())
        await self.handler._safe_write_message({
            "type": "edit_cell",
            "cell_index": cell_index,
            "code": code,
            "rerun": rerun,
            "request_id": request_id,
            "connection_id": self.handler.connection_id,
        })
        
        # Wait for result
        self.handler.waiter = asyncio.get_running_loop().create_future()
        try:
            result = await asyncio.wait_for(self.handler.waiter, timeout=90.0)
            print(f"[EDIT-PROXY] Edit cell result: {result[:100]}...")
            return result
        except asyncio.TimeoutError:
            return "Error: Edit cell operation timed out"
        finally:
            self.handler.waiter = None
    
    async def rerun_all_cells(self) -> str:
        """Rerun all cells in the notebook."""
        print(f"[EDIT-PROXY] Rerunning all cells")
        
        # Generate request ID and send rerun all cells request
        request_id = str(uuid.uuid4())
        await self.handler._safe_write_message({
            "type": "rerun_all_cells",
            "request_id": request_id,
            "connection_id": self.handler.connection_id,
        })
        
        # Wait for result
        self.handler.waiter = asyncio.get_running_loop().create_future()
        try:
            result = await asyncio.wait_for(self.handler.waiter, timeout=90.0)
            print(f"[EDIT-PROXY] Rerun all cells result: {result[:100]}...")
            return result
        except asyncio.TimeoutError:
            return "Error: Rerun all cells operation timed out"
        finally:
            self.handler.waiter = None
    
    async def insert_markdown_cell(self, cell_index: int, content: str) -> str:
        """Insert a markdown cell at the specified index."""
        print(f"[EDIT-PROXY] Inserting markdown cell at index {cell_index}")
        
        # Generate request ID and send insert markdown cell request
        request_id = str(uuid.uuid4())
        await self.handler._safe_write_message({
            "type": "insert_markdown_cell",
            "cell_index": cell_index,
            "content": content,
            "request_id": request_id,
            "connection_id": self.handler.connection_id,
        })
        
        # Wait for result
        self.handler.waiter = asyncio.get_running_loop().create_future()
        try:
            result = await asyncio.wait_for(self.handler.waiter, timeout=90.0)
            print(f"[EDIT-PROXY] Insert markdown cell result: {result[:100]}...")
            return result
        except asyncio.TimeoutError:
            return "Error: Insert markdown cell operation timed out"
        finally:
            self.handler.waiter = None
    
    async def read_file(self, file_path: str, start_row_index: int = 0, end_row_index: int = 200) -> str:
        """Read a file and return its contents."""
        print(f"[EDIT-PROXY] Reading file: {file_path}")
        
        try:
            # Implement file reading locally (no need for WebSocket for this)
            import os
            import traceback
            
            if not os.path.exists(file_path):
                return f"Error: File '{file_path}' does not exist"
            
            if not os.path.isfile(file_path):
                return f"Error: '{file_path}' is not a file"
            
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Apply row indexing
            if start_row_index < 0:
                start_row_index = 0
            if end_row_index >= len(lines):
                end_row_index = len(lines) - 1
            
            selected_lines = lines[start_row_index:end_row_index + 1]
            content = ''.join(selected_lines)
            
            result = f"File: {file_path}\nRows {start_row_index}-{end_row_index}:\n{content}"
            print(f"[EDIT-PROXY] File read result: {result[:100]}...")
            return result
            
        except Exception as e:
            error_msg = f"Error reading file '{file_path}': {str(e)}"
            print(f"[EDIT-PROXY] {error_msg}")
            return error_msg
    
    async def web_search(self, query: str) -> str:
        """Perform web search (handled by remote server)."""
        print(f"[EDIT-PROXY] Web search should be handled by remote server, not locally")
        return "Error: Web search should be handled by the remote server. This appears to be a configuration issue."


class AIEditChatProxyHandler(WebSocketHandler):
    """
    WebSocket proxy handler that bridges frontend to remote backend server for edit functionality.
    
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
        self.waiting_for_remote_backend_response: bool = False

        # Frontend WebSocket connection state
        self._is_closed = False
        self.waiter: asyncio.Future | None = None
        self._active_tasks = set()
        
        # Remote backend connection
        self.remote_websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.remote_url = build_remote_backend_url("edit")
        self._remote_connection_lock = asyncio.Lock()
        
        # Flag to prevent duplicate disconnection notifications
        self._remote_disconnection_notified = False
        
        # Server base URL for API calls
        self.server_url = os.environ.get("SERVER_URL", "http://localhost:8888")
        
        # Token-based authentication (replaces access key system)
        print("[EDIT-PROXY] Token authentication enabled - will forward tokens to remote backend")
        
        # Initialize local components (for tool execution)
        self.image_processor = ImageProcessor(self.server_url)
        self.tool_executor = EditWebSocketToolExecutor(self)
        
        # Register this handler with connection manager
        ConnectionManager.register_handler(self)

    def _get_user_token(self) -> Optional[str]:
        """
        Get user token from local file (saved during OAuth flow).
        
        Returns:
            User token if found, None otherwise
        """
        token = get_current_user_token_string()
        if token:
            print(f"[EDIT-PROXY] ✅ Found user token")
        else:
            print("[EDIT-PROXY] ❌ No user token found")
        return token

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
            print(f"[EDIT-PROXY] Error checking connection state: {e}")
            # If we can't determine the state, assume it's open to avoid reconnecting unnecessarily
            return False

    def check_origin(self, origin: str) -> bool:
        # NOTE: relax CORS – adjust for production
        return True

    async def open(self):
        """Handle WebSocket connection opening from frontend.

        NOTE: Edit mode is deprecated. This handler now only returns an upgrade message
        and closes the connection. Old clients that still try to use edit mode will
        receive this message asking them to upgrade.
        """
        # Edit mode is deprecated - send upgrade message and close
        print("[EDIT-PROXY] ⚠️ Edit mode is deprecated. Sending upgrade message to client.")
        await self._safe_write_message({
            "type": "error",
            "error": "Edit mode has been deprecated. Please upgrade your extension to the latest version to use Agent mode instead."
        })
        self.close()
        return

    async def _connect_to_remote_backend(self):
        """Establish WebSocket connection to remote backend server."""
        try:
            async with self._remote_connection_lock:
                if self.remote_websocket is None or self._is_remote_connection_closed():
                    # Add user token to URL for authentication
                    connection_url = self.remote_url
                    if hasattr(self, 'user_token') and self.user_token:
                        separator = "&" if "?" in connection_url else "?"
                        connection_url = f"{connection_url}{separator}token={self.user_token}"
                        print(f"[EDIT-PROXY] Connecting to remote backend with user authentication: {self.remote_url}")
                    else:
                        print(f"[EDIT-PROXY] Connecting to remote backend without authentication: {self.remote_url}")
                    
                    # Only create SSL context for wss:// connections
                    ssl_context = None
                    if connection_url.startswith("wss://"):
                        try:
                            ssl_context = ssl.create_default_context(cafile=certifi.where())
                            print(f"[EDIT-PROXY] Using certifi certificate bundle for WebSocket SSL verification")
                        except Exception as e:
                            print(f"[EDIT-PROXY] Failed to create SSL context with certifi: {e}")
                            # Fallback to default SSL context
                            ssl_context = ssl.create_default_context()
                    
                    # Connect with timeout to fail fast on network errors
                    try:
                        if connection_url.startswith("wss://"):
                            print(f"[EDIT-PROXY] Connecting to secure WebSocket (wss://) with SSL context")
                            self.remote_websocket = await asyncio.wait_for(
                                websockets.connect(connection_url, ssl=ssl_context),
                                timeout=5.0  # 5 second timeout
                            )
                        else:
                            # Plain ws:// connection - no SSL context needed
                            print(f"[EDIT-PROXY] Connecting to plain WebSocket (ws://) without SSL")
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
                    
                    print(f"[EDIT-PROXY] Connected to remote backend successfully")
        except Exception as e:
            print(f"[EDIT-PROXY] Failed to connect to remote backend: {e}")
            # Clear the websocket reference (match agent mode - no error message to frontend)
            self.remote_websocket = None

    async def _listen_to_remote_backend(self):
        """Listen for messages from remote backend and forward to frontend."""
        try:
            async for message in self.remote_websocket:
                try:
                    data = json.loads(message)
                    await self._handle_remote_backend_message(data)
                except json.JSONDecodeError as e:
                    print(f"[EDIT-PROXY] Invalid JSON from remote backend: {e}")
                except Exception as e:
                    print(f"[EDIT-PROXY] Error handling remote backend message: {e}")
        except websockets.exceptions.ConnectionClosed:
            print("[EDIT-PROXY] Remote backend connection closed")
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
            print(f"[EDIT-PROXY] Error listening to remote backend: {e}")
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
            print(f"[EDIT-PROXY] Received message from remote backend: {msg_type}")
        
        if msg_type in ["assistant_chunk", "reasoning_chunk", "assistant_complete", "system", "tool_call", "tool_call_output"]:
            # Forward AI responses directly to frontend (includes reasoning chunks for reasoning models)
            await self._safe_write_message(data)
            
        elif msg_type == "tool_call_request":
            # Handle tool call request from remote backend
            print(f"[EDIT-PROXY] Handling tool call request: {data.get('tool_name')}")
            await self._handle_tool_call_request(data)
            
        elif msg_type == "shell_execute":
            # Handle shell execute as local tool execution (not frontend request)
            print(f"[EDIT-PROXY] Handling shell execute as local tool")
            await self._handle_shell_execute_locally(data)
            
        elif msg_type == "get_image_base64":
            # Handle image base64 request from remote backend
            print(f"[EDIT-PROXY] Handling get_image_base64 request")
            await self._handle_get_image_base64_request(data)
            
        elif msg_type in ["cell_execute", "edit_cell", "insert_markdown_cell", "rerun_all_cells"]:
            # Handle frontend request messages from remote backend
            await self._handle_frontend_request_from_remote(data)
            
        else:
            # Forward other messages to frontend
            print(f"[EDIT-PROXY] Forwarding unknown message type {msg_type} to frontend")
            await self._safe_write_message(data)

    async def _handle_shell_execute_locally(self, data):
        """Handle shell execute request from remote backend by executing locally on proxy server."""
        try:
            command = data.get("command", "")
            request_id = data.get("request_id")
            
            print(f"[EDIT-PROXY] Executing shell command locally: {command}")
            
            # Execute shell command using proxy's tool executor
            result = await self.tool_executor.shell_execute(command)
            
            # Send result back to remote backend
            await self._send_to_remote_backend({
                "type": "shell_execute_result",
                "request_id": request_id,
                "result": result
            })
            
        except Exception as e:
            print(f"[EDIT-PROXY] Error executing shell command: {e}")
            # Send error back to remote backend
            await self._send_to_remote_backend({
                "type": "shell_execute_result",
                "request_id": data.get("request_id"),
                "result": f"Error executing shell command: {e}"
            })

    async def _handle_tool_call_request(self, data):
        """Handle tool call request from remote backend by executing locally."""
        try:
            tool_name = data.get("tool_name")
            tool_args = data.get("tool_args", {})
            request_id = data.get("request_id")
            
            print(f"[EDIT-PROXY] Executing local tool: {tool_name} with args: {tool_args}")
            
            # Execute the tool locally
            result = await self._execute_local_tool(tool_name, tool_args)
            
            # Send result back to remote backend
            await self._send_to_remote_backend({
                "type": "tool_call_result",
                "request_id": request_id,
                "tool_name": tool_name,
                "result": result
            })
            
        except Exception as e:
            print(f"[EDIT-PROXY] Error handling tool call request: {e}")
            # Send error back to remote backend
            await self._send_to_remote_backend({
                "type": "tool_call_result",
                "request_id": data.get("request_id"),
                "tool_name": data.get("tool_name"),
                "result": f"Error executing tool: {e}"
            })

    async def _handle_frontend_request_from_remote(self, data):
        """Handle frontend request messages from remote backend."""
        try:
            msg_type = data.get("type")
            request_id = data.get("request_id")
            
            print(f"[EDIT-PROXY] Processing frontend request {msg_type} with request_id: {request_id}")
            
            # Forward the message to frontend
            await self._safe_write_message(data)
            
            # Set up waiter to capture the response
            self.waiter = asyncio.get_running_loop().create_future()
            self.current_request_id = request_id
            self.waiting_for_remote_backend_response = True
            
            print(f"[EDIT-PROXY] Waiting for response to request_id: {request_id}")
            
            # Wait for the response (with timeout)
            try:
                result = await asyncio.wait_for(self.waiter, timeout=90.0)
                print(f"[EDIT-PROXY] Received response for request_id {request_id}: {result[:100]}...")
                
                # Send the result back to remote backend
                await self._send_to_remote_backend({
                    "type": f"{msg_type}_result",
                    "request_id": request_id,
                    "result": result
                })
                
            except asyncio.TimeoutError:
                error_msg = f"Timeout waiting for {msg_type} response"
                print(f"[EDIT-PROXY] {error_msg}")
                await self._send_to_remote_backend({
                    "type": f"{msg_type}_result", 
                    "request_id": request_id,
                    "result": error_msg
                })
            finally:
                self.waiter = None
                self.current_request_id = None
                self.waiting_for_remote_backend_response = False
                
        except Exception as e:
            print(f"[EDIT-PROXY] Error handling frontend request: {e}")
            import traceback
            traceback.print_exc()

    async def _execute_local_tool(self, tool_name: str, tool_args: dict) -> str:
        """Execute a tool locally using the WebSocket tool executor."""
        if tool_name == "cell_execute":
            return await self.tool_executor.cell_execute(tool_args.get("code", ""))
            
        elif tool_name == "shell_execute":
            return await self.tool_executor.shell_execute(tool_args.get("command", ""))
            
        elif tool_name == "edit_cell":
            return await self.tool_executor.edit_cell(
                tool_args.get("cell_index", 0),
                tool_args.get("code", ""),
                tool_args.get("rerun", False)
            )
            
        elif tool_name == "rerun_all_cells":
            return await self.tool_executor.rerun_all_cells()
            
        elif tool_name == "insert_markdown_cell": 
            return await self.tool_executor.insert_markdown_cell(
                tool_args.get("cell_index", 0),
                tool_args.get("content", "")
            )
            
        elif tool_name == "read_file":
            return await self.tool_executor.read_file(
                tool_args.get("file_path", ""),
                tool_args.get("start_row_index", 0),
                tool_args.get("end_row_index", 200)
            )
            
        elif tool_name == "web_search":
            return "Error: Web search should be handled by remote server, not as a local tool"
            
        else:
            return f"Error: Unknown tool '{tool_name}'"

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
            print(f"[EDIT-PROXY] Error sending to remote backend: {e}")
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
            
            # Send completion signal so frontend knows the chat is finished and saves it
            await self._safe_write_message({
                "type": "assistant_complete"
            })

    async def _safe_write_message(self, data):
        """Safely write a message to the WebSocket with error handling."""
        if self._is_closed:
            return False
        
        try:
            await self.write_message(json.dumps(data))
            return True
        except tornado.websocket.WebSocketClosedError:
            self._is_closed = True
            return False
        except Exception as e:
            print(f"[EDIT-PROXY] Error writing to WebSocket: {str(e)}")
            return False

    async def on_message(self, raw: str):
        """Handle incoming WebSocket messages from frontend."""
        try:
            msg = json.loads(raw)
            msg_type = msg.get("type")
            print(f"[EDIT-PROXY] Received message from frontend: {msg_type}")

            if msg_type == "user":
                # Forward user message to remote backend
                await self._forward_to_remote_backend(msg)
                
            elif msg_type in ["cell_result", "edit_cell_result", "rerun_all_cells_result", 
                            "insert_markdown_cell_result", "shell_execute_result", "shell_permission_response", 
                            "rerun_all_cells_permission_response"]:
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
                
            else:
                print(f"[EDIT-PROXY] Unknown message type from frontend: {msg_type}")
                
        except Exception as e:
            print(f"[EDIT-PROXY] Error in on_message: {str(e)}")
            import traceback
            traceback.print_exc()

    async def _forward_to_remote_backend(self, msg):
        """Forward a message to the remote backend."""
        # Add connection_id to the message for correlation
        msg["connection_id"] = self.connection_id
        await self._send_to_remote_backend(msg)

    async def _handle_local_tool_result(self, msg):
        """Handle results from local tool execution."""
        msg_type = msg.get("type")
        conn_id = msg.get("connection_id", self.connection_id)
        request_id = msg.get("request_id")
        
        # Find the handler with this connection ID
        handler = ConnectionManager.get_handler(conn_id) or self
        
        # Check if this is a response to a pending frontend request from remote backend
        # This should only apply when we're explicitly waiting for a remote backend response
        if (hasattr(handler, 'waiting_for_remote_backend_response') and 
            handler.waiting_for_remote_backend_response and
            handler.current_request_id and handler.current_request_id == request_id and
            handler.waiter and not handler.waiter.done()):
            print(f"[EDIT-PROXY] Processing response for pending frontend request from remote backend: {request_id}")
            
            if msg_type == "cell_result":
                result = msg.get("result", "No result provided")
                # Process the result to check for image data and resolve waiter
                await self._process_cell_result(handler, result)
                return  # Early return to avoid duplicate processing
                
            elif msg_type in ["edit_cell_result", "rerun_all_cells_result", "insert_markdown_cell_result"]:
                # For other result types, process and resolve waiter directly
                if msg_type == "insert_markdown_cell_result":
                    success = msg.get("success", False)
                    if success:
                        result = msg.get("message", "Markdown cell inserted successfully")
                    else:
                        error = msg.get("error", "Unknown error occurred")
                        result = f"Error inserting markdown cell: {error}"
                else:
                    result = msg.get("result", "No result provided")
                
                handler.waiter.set_result(result)
                return  # Early return to avoid duplicate processing
        
        # If not a pending frontend request, handle as before
        if msg_type == "cell_result":
            result = msg.get("result", "No result provided")
            # Process the result to check for image data
            await self._process_cell_result(handler, result)
            
        elif msg_type == "edit_cell_result":
            result = msg.get("result", "No result provided")
            # Set the result directly to the waiter (no image processing needed for this operation)
            if handler.waiter and not handler.waiter.done():
                handler.waiter.set_result(result)
            else:
                print(f"[EDIT-PROXY] Handler waiter not available or already done for edit cell result")
                
        elif msg_type == "rerun_all_cells_result":
            result = msg.get("result", "No result provided")
            # Set the result directly to the waiter (no image processing needed for this operation)
            if handler.waiter and not handler.waiter.done():
                handler.waiter.set_result(result)
            else:
                print(f"[EDIT-PROXY] Handler waiter not available or already done for rerun all cells result")
                
        elif msg_type == "insert_markdown_cell_result":
            success = msg.get("success", False)
            # Prepare result message based on success status
            if success:
                result = msg.get("message", "Markdown cell inserted successfully")
            else:
                error = msg.get("error", "Unknown error occurred")
                result = f"Error inserting markdown cell: {error}"
                
            # Set the result directly to the waiter (no image processing needed for this operation)
            if handler.waiter and not handler.waiter.done():
                handler.waiter.set_result(result)
            else:
                print(f"[EDIT-PROXY] Handler waiter not available or already done for insert markdown cell result")
                
        elif msg_type == "shell_permission_response":
            allowed = msg.get("allowed", False)
            request_id = msg.get("request_id")
            print(f"[EDIT-PROXY][SHELL] Received permission response: allowed={allowed}, request_id={request_id}")
            
            # Set the permission response to the waiter
            if handler.waiter and not handler.waiter.done():
                print(f"[EDIT-PROXY][SHELL] Setting permission response to waiter")
                handler.waiter.set_result({"allowed": allowed, "request_id": request_id})
            else:
                print(f"[EDIT-PROXY][SHELL] Cannot set permission response - waiter not available or already done")
                
        elif msg_type == "rerun_all_cells_permission_response":
            allowed = msg.get("allowed", False)
            request_id = msg.get("request_id")
            print(f"[EDIT-PROXY][RERUN] Received permission response: allowed={allowed}, request_id={request_id}")
            
            # Set the permission response to the waiter
            if handler.waiter and not handler.waiter.done():
                print(f"[EDIT-PROXY][RERUN] Setting permission response to waiter")
                handler.waiter.set_result({"allowed": allowed, "request_id": request_id})
            else:
                print(f"[EDIT-PROXY][RERUN] Cannot set permission response - waiter not available or already done")

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
            print(f"[EDIT-PROXY] Error checking if URL is local: {e}")
            return False

    async def _process_cell_result(self, handler, result):
        """Process cell result to check for image data."""
        await self.image_processor.process_cell_result(handler, result)

    async def _handle_get_image_base64_request(self, data):
        """Handle get_image_base64 request from remote backend."""
        try:
            image_url = data.get("image_url")
            request_id = data.get("request_id")
            
            print(f"[EDIT-PROXY] Processing get_image_base64 request for URL: {image_url[:100]}...")
            
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
                    print(f"[EDIT-PROXY] Successfully retrieved image via HTTP, size: {len(image_data)} bytes")
                
                # Convert to base64
                image_base64 = base64.b64encode(image_data).decode('utf-8')
                
                print(f"[EDIT-PROXY] Successfully retrieved image, size: {len(image_data)} bytes")
                
                # Send success response
                await self._send_to_remote_backend({
                    "type": "image_base64_result",
                    "request_id": request_id,
                    "success": True,
                    "base64_data": image_base64
                })
                
            except Exception as fetch_error:
                print(f"[EDIT-PROXY] HTTP request failed: {fetch_error}")
                
                # Fallback: try direct file access for localhost URLs only
                try:
                    from urllib.parse import urlparse
                    import os
                    
                    if self._is_local_image_service_url(image_url):
                        print(f"[EDIT-PROXY] Attempting fallback to direct file access for localhost URL")
                        
                        parsed_url = urlparse(image_url)
                        filename = parsed_url.path.split("/d5m-ai/image-service/")[-1]
                        
                        from ..image.handler import IMAGE_STORAGE_DIR
                        image_path = os.path.join(IMAGE_STORAGE_DIR, filename)
                        
                        if os.path.exists(image_path) and os.path.isfile(image_path):
                            with open(image_path, "rb") as f:
                                image_data = f.read()
                            
                            image_base64 = base64.b64encode(image_data).decode('utf-8')
                            print(f"[EDIT-PROXY] Fallback successful: read image from filesystem, size: {len(image_data)} bytes")
                            
                            # Send success response
                            await self._send_to_remote_backend({
                                "type": "image_base64_result",
                                "request_id": request_id,
                                "success": True,
                                "base64_data": image_base64
                            })
                            return
                        else:
                            print(f"[EDIT-PROXY] Fallback failed: image file not found at {image_path}")
                    
                    # If not localhost or fallback failed, send original error
                    raise fetch_error
                        
                except Exception as fallback_error:
                    print(f"[EDIT-PROXY] Fallback also failed: {fallback_error}")
                    # Fall through to send original HTTP error
                
                # Send error response with original HTTP error
                await self._send_to_remote_backend({
                    "type": "image_base64_result",
                    "request_id": request_id,
                    "success": False,
                    "error": f"Failed to fetch image: {str(fetch_error)}"
                })
                
        except Exception as e:
            print(f"[EDIT-PROXY] Error handling get_image_base64 request: {e}")
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
        self._is_closed = True
        
        # Cancel all active tasks
        for task in self._active_tasks:
            if not task.done():
                task.cancel()
        
        # Close remote backend connection
        if self.remote_websocket and not self._is_remote_connection_closed():
            asyncio.create_task(self.remote_websocket.close())
        
        # Remove from registry
        ConnectionManager.unregister_handler(self.connection_id)
        
        # Cancel any pending waiters
        if self.waiter and not self.waiter.done():
            self.waiter.cancel()
        self.waiter = None
        
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
                    print(f"[EDIT-PROXY] Remote backend ping failed: {e}")
                    # Close and clear the connection
                    if self.remote_websocket:
                        await self.remote_websocket.close()
                    self.remote_websocket = None
                    break
                except Exception as e:
                    print(f"[EDIT-PROXY] Error in ping task: {e}")
                    break
        except Exception as e:
            print(f"[EDIT-PROXY] Ping task error: {e}") 
