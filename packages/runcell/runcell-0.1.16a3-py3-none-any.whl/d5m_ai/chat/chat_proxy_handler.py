"""
Proxy handler for AI chat functionality.

This handler acts as a proxy between the frontend and the remote backend server.
It forwards chat requests to the remote backend and streams responses back to the frontend.

The remote backend handles all AI processing, while this proxy handles:
- User token-based authentication (replaces access key system)
- Request forwarding with user authentication
- Response streaming 
- CORS handling
- Error handling
- Credit-related error messaging
"""

import asyncio
import aiohttp
import logging
import json
import os
import ssl
import certifi
from copy import deepcopy
from typing import Dict, Any, Optional
from jupyter_server.base.handlers import APIHandler
from tornado import web

from ..utils import build_remote_backend_url
from ..auth.token_handler import get_current_user_token_string
from ..tools.registry import run_ask_tool
from .._version import __version__ as client_version

logging.basicConfig(level=logging.INFO)


class AIChatProxyHandler(APIHandler):
    """Proxy handler for AI chat requests that forwards to remote backend."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Get remote backend URL using unified URL builder
        self.remote_backend_url = build_remote_backend_url("chat").replace("/chat", "")
        
        logging.info(f"[CHAT-PROXY] Initialized with remote backend: {self.remote_backend_url}")
        logging.info("[CHAT-PROXY] Token authentication enabled - will forward tokens to remote backend")
    
    async def get_user_token(self) -> Optional[str]:
        """
        Extract user token from local file or request.
        
        Priority order:
        1. Local file token (saved when OAuth succeeds)
        2. Request headers/cookies (fallback for compatibility)
        
        Returns:
            User token if found, None otherwise
        """
        # **PRIORITY 1: Check local file token (saved when OAuth succeeds)**
        local_token = get_current_user_token_string()
        if local_token:
            logging.info(f"[CHAT-PROXY] ✅ Found token in local file (length: {len(local_token)})")
            return local_token
        
        logging.info("[CHAT-PROXY] No token found in local file, checking request headers/cookies...")
        
        # Debug: Log all available headers and cookies for troubleshooting
        logging.info(f"[CHAT-PROXY] DEBUG - Request headers: {dict(self.request.headers)}")
        logging.info(f"[CHAT-PROXY] DEBUG - Available cookies: {list(self.cookies.keys())}")
        
        # Check for plugin auth token specifically
        plugin_token = self.get_cookie("plugin_auth_token_v2")
        if plugin_token:
            logging.info(f"[CHAT-PROXY] DEBUG - Found plugin_auth_token_v2: {plugin_token[:20]}...")
        else:
            logging.info("[CHAT-PROXY] DEBUG - No plugin_auth_token_v2 cookie found")
            
        # Check each Supabase token type
        for cookie_name in self.cookies.keys():
            if cookie_name.startswith("sb-") and "auth-token" in cookie_name:
                cookie_value = self.cookies[cookie_name]
                token_value = cookie_value.value if hasattr(cookie_value, 'value') else str(cookie_value)
                logging.info(f"[CHAT-PROXY] DEBUG - {cookie_name}: {token_value[:20]}...")
        
        # Check Authorization header
        auth_header = self.request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove "Bearer " prefix
            logging.info("[CHAT-PROXY] Found token in Authorization header")
            return token
        
        # Check X-User-Token header
        user_token = self.request.headers.get("X-User-Token", "")
        if user_token:
            logging.info("[CHAT-PROXY] Found token in X-User-Token header")
            return user_token
        
        # Look for actual Supabase auth tokens that are present in the cookies
        supabase_token_patterns = [
            "sb-",  # Supabase tokens start with sb-
            "plugin_auth_token_v2",
            "auth_token", 
            "user_token",
            "jwt_token"
        ]
        
        # **PRIORITY 1: Plugin Auth Token (JWT format expected by localhost:3000)**
        plugin_token = self.get_cookie("plugin_auth_token_v2")
        if plugin_token and plugin_token.startswith("eyJ") and plugin_token.count('.') == 2:
            logging.info(f"[CHAT-PROXY] ✅ Found valid JWT plugin_auth_token_v2 (length: {len(plugin_token)})")
            return plugin_token
        elif plugin_token:
            logging.warning(f"[CHAT-PROXY] ⚠️ plugin_auth_token_v2 exists but doesn't look like JWT: {plugin_token[:20]}...")
        
        # **PRIORITY 2: Other JWT tokens in cookies**
        for cookie_name in ["auth_token", "user_token", "jwt_token"]:
            token_cookie = self.get_cookie(cookie_name)
            if token_cookie and token_cookie.startswith("eyJ") and token_cookie.count('.') == 2:
                logging.info(f"[CHAT-PROXY] ✅ Found JWT token in cookie: {cookie_name} (length: {len(token_cookie)})")
                return token_cookie
            elif token_cookie:
                logging.warning(f"[CHAT-PROXY] ⚠️ {cookie_name} exists but not JWT format: {token_cookie[:20]}...")
        
        # **FALLBACK: Supabase tokens (likely incompatible with localhost:3000)**
        for cookie_name, cookie_value in self.cookies.items():
            if (cookie_name.startswith("sb-") and 
                "auth-token" in cookie_name and 
                "code-verifier" not in cookie_name):
                token_value = cookie_value.value if hasattr(cookie_value, 'value') else str(cookie_value)
                logging.warning(f"[CHAT-PROXY] ⚠️ Using Supabase token as fallback: {cookie_name} - likely incompatible with localhost:3000")
                logging.warning(f"[CHAT-PROXY] Consider setting D5M_TEST_USER_TOKEN environment variable with a valid JWT")
                return token_value
        
        # Check for token in query parameters (fallback, not recommended for production)
        token_param = self.get_argument("token", None)
        if token_param:
            logging.info("[CHAT-PROXY] Found token in query parameters")
            return token_param
        
        # Check request body for token (in case frontend sends it in the body)
        try:
            body_data = json.loads(self.request.body.decode("utf-8"))
            if "user_token" in body_data:
                logging.info("[CHAT-PROXY] Found token in request body")
                return body_data["user_token"]
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass
        
        # Log detailed debugging information
        logging.warning("[CHAT-PROXY] No user token found in request")
        logging.warning(f"[CHAT-PROXY] Available Supabase cookies: {[name for name in self.cookies.keys() if name.startswith('sb-')]}")
        
        return None
    
    def get_test_token_from_env(self) -> Optional[str]:
        """
        Get test token from environment variable for development/testing.
        
        This is a temporary method to facilitate testing without frontend integration.
        Remove this in production.
        
        Returns:
            Test token if available
        """
        test_token = os.environ.get("D5M_TEST_USER_TOKEN")
        if test_token:
            # Validate that test token is a JWT
            if test_token.startswith("eyJ") and test_token.count('.') == 2:
                logging.warning("[CHAT-PROXY] ✅ Using valid JWT test token from D5M_TEST_USER_TOKEN")
                logging.warning("[CHAT-PROXY] This should only be used for testing!")
                return test_token
            else:
                logging.error(f"[CHAT-PROXY] ❌ D5M_TEST_USER_TOKEN is not a valid JWT format: {test_token[:20]}...")
                logging.error("[CHAT-PROXY] JWT should start with 'eyJ' and have exactly 2 dots")
                return None
        return None
    

        
    @web.authenticated
    async def post(self):
        """Handle POST requests by forwarding to remote backend with user authentication."""
        try:
            # Step 1: Get user token (no verification - let remote backend handle that)
            user_token = await self.get_user_token()
            
            # Fallback to test token if no token found (for development/testing)
            if not user_token:
                user_token = self.get_test_token_from_env()
            
            if not user_token:
                self.set_status(401)
                self.finish(json.dumps({
                    "error": "Authentication required. You may not be signed in or there may be an issue with your authentication. Please try signing in again.",
                    "status": "auth_required",
                    "debug_info": {
                        "frontend_integration_needed": True,
                        "suggestions": [
                            "Save the plugin_auth_token_v2 to the server via /api/d5m_ai/auth/token",
                            "Frontend should send token in Authorization header: 'Bearer <token>'",
                            "Frontend should send token in X-User-Token header",
                            "Check if Supabase auth tokens are available in cookies"
                        ]
                    }
                }))
                return
            
            logging.info(f"[CHAT-PROXY] Found user token, forwarding to remote backend")
            
            # Step 2: Parse request body
            body_data = json.loads(self.request.body.decode("utf-8"))
            messages = body_data.get("messages", [])
            code_cells = body_data.get("code_cells", [])
            stream = body_data.get("stream", True)
            model = body_data.get("model", "anthropic/claude-haiku-4-5")
            
            logging.info(f"[CHAT-PROXY] Forwarding chat request: model={model}, stream={stream}")
            
            if not messages:
                self.set_status(400)
                self.finish(json.dumps({"error": "No messages provided"}))
                return

            # Step 3: Forward request to remote backend with user token
            await self._forward_to_remote_backend(body_data, stream, user_token)
            
        except Exception as e:
            logging.error(f"[CHAT-PROXY] Error handling chat request: {e}")
            self.set_status(500)
            self.finish(json.dumps({
                "error": str(e),
                "status": "error"
            }))

    async def _forward_to_remote_backend(self, body_data: Dict[str, Any], stream: bool, user_token: str):
        """Forward request to remote backend and handle response."""
        try:
            remote_url = f"{self.remote_backend_url}/chat"

            # Add starting content_index to body for conversation continuations
            if hasattr(self, '_unified_content_index') and self._unified_content_index > 0:
                body_data['starting_content_index'] = self._unified_content_index
                logging.info(f"[CHAT-PROXY] Continuing conversation with starting_content_index: {self._unified_content_index}")

            # Inject client version
            body_data['client_version'] = client_version

            # Prepare headers with user authentication
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {user_token}'
            }
            logging.debug("[CHAT-PROXY] Adding user token to remote backend request")
            
            # Create SSL context with proper certificate verification
            try:
                ssl_context = ssl.create_default_context(cafile=certifi.where())
                logging.debug("[CHAT-PROXY] Using certifi certificate bundle for SSL verification")
            except Exception as e:
                logging.warning(f"[CHAT-PROXY] Failed to create SSL context with certifi: {e}")
                # Fallback to default SSL context
                ssl_context = ssl.create_default_context()
            
            # Create connector with SSL context
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.post(
                    remote_url,
                    json=body_data,
                    headers=headers
                ) as response:
                    
                    if response.status != 200:
                        # Handle error response
                        error_text = await response.text()
                        logging.error(f"[CHAT-PROXY] Remote backend error {response.status}: {error_text}")
                        
                        # Try to parse error as JSON for better error handling
                        try:
                            error_data = json.loads(error_text)
                            error_status = error_data.get("status", "error")
                            error_message = error_data.get("error", error_text)
                            
                            # Handle specific error types
                            if response.status == 401:
                                # Authentication error
                                self.set_status(401)
                                self.finish(json.dumps({
                                    "error": "Authentication failed. Please log in again.",
                                    "status": "auth_error"
                                }))
                            elif response.status == 402:
                                # Insufficient credits
                                self.set_status(402)
                                self.finish(json.dumps({
                                    "error": error_message,
                                    "status": "insufficient_credits"
                                }))
                            else:
                                # Other errors
                                self.set_status(response.status)
                                self.finish(json.dumps({
                                    "error": error_message,
                                    "status": error_status
                                }))
                        except json.JSONDecodeError:
                            # Fallback for non-JSON error responses
                            self.set_status(response.status)
                            self.finish(json.dumps({
                                "error": f"Remote backend error: {error_text}",
                                "status": "error"
                            }))
                        return
                    
                    if stream:
                        # Handle streaming response
                        # Track unified content index across all streaming calls for this request
                        if not hasattr(self, '_unified_content_index'):
                            self._unified_content_index = 0
                        
                        pending_tool_data = await self._handle_streaming_response(response, self._unified_content_index)
                        if pending_tool_data:
                            # Update the unified content index for the next continuation
                            self._unified_content_index = pending_tool_data.get('max_content_index', self._unified_content_index)
                            await self._handle_pending_tool_call(pending_tool_data, body_data, user_token)
                    else:
                        # Handle non-streaming response
                        response_data = await response.json()
                        self.finish(json.dumps(response_data))

        except aiohttp.ClientConnectorError as e:
            logging.error(f"[CHAT-PROXY] Cannot connect to remote backend at {self.remote_backend_url}: {e}")
            self.set_status(503)
            self.finish(json.dumps({
                "error": f"Cannot connect to chat remote backend. Please ensure the remote backend server is running at {self.remote_backend_url}",
                "status": "error"
            }))
        except Exception as e:
            logging.error(f"[CHAT-PROXY] Error forwarding to remote backend: {e}")
            self.set_status(500)
            self.finish(json.dumps({
                "error": str(e),
                "status": "error"
            }))

    async def _handle_streaming_response(self, response: aiohttp.ClientResponse, unified_content_index: int = 0) -> Optional[Dict[str, Any]]:
        """Handle streaming response from remote backend.

        Args:
            response: The aiohttp response to stream
            unified_content_index: The current unified content index (for tracking message order across continuations)

        Returns a tuple of (pending_tool_payload, last_content_index) if the conversation should continue,
        or (None, last_content_index) when streaming completes.
        """
        try:
            # Set up streaming response headers (exactly like original handler)
            self.set_header("Content-Type", "text/event-stream")
            self.set_header("Cache-Control", "no-cache")
            self.set_header("Connection", "keep-alive")

            logging.info(f"[CHAT-PROXY] Starting to stream response from remote backend (starting content_index: {unified_content_index})")

            buffer = ""
            assistant_text = ""
            max_content_index = unified_content_index

            # Read response content as chunks and forward after processing
            async for chunk in response.content.iter_chunks():
                if not chunk[0]:
                    continue

                chunk_text = chunk[0].decode('utf-8', errors='ignore')
                buffer += chunk_text

                while '\n\n' in buffer:
                    event_text, buffer = buffer.split('\n\n', 1)
                    if not event_text.startswith('data: '):
                        continue

                    payload_text = event_text[6:]

                    try:
                        payload = json.loads(payload_text)
                    except json.JSONDecodeError:
                        logging.error(f"[CHAT-PROXY] Failed to parse SSE payload: {payload_text}")
                        continue

                    status = payload.get('status')
                    payload_type = payload.get('type')

                    # Track the maximum content_index seen
                    if 'content_index' in payload:
                        content_idx = payload['content_index']
                        if content_idx > max_content_index:
                            max_content_index = content_idx

                    if status == 'streaming' and payload.get('chunk'):
                        assistant_text += payload['chunk']
                        # Ensure content_index is present for proper ordering
                        if 'content_index' not in payload:
                            logging.warning("[CHAT-PROXY] Chunk without content_index - this should not happen with updated backend")
                        await self._write_sse_event(payload)
                    elif payload_type in {'reasoning', 'reasoning_done', 'tool_call', 'tool_call_output'}:
                        await self._write_sse_event(payload)
                    elif status == 'pending_tool':
                        payload.setdefault('assistant_text', assistant_text)
                        payload['max_content_index'] = max_content_index
                        logging.info(f"[CHAT-PROXY] Pending tool call detected (max_content_index: {max_content_index})")
                        return payload
                    elif status == 'done':
                        await self._write_sse_event(payload)
                        logging.info("[CHAT-PROXY] Streaming completed")
                        return None
                    else:
                        await self._write_sse_event(payload)

        except Exception as e:
            logging.error(f"[CHAT-PROXY] Error during streaming: {e}")
            # Send error event to frontend
            error_data = json.dumps({'error': str(e), 'status': 'error'})
            self.write(f"data: {error_data}\n\n")
            await self.flush()
        return None

    async def _write_sse_event(self, payload: Dict[str, Any]):
        """Write a single SSE event to the frontend."""
        event_text = json.dumps(payload)
        self.write(f"data: {event_text}\n\n")
        await self.flush()

    async def _handle_pending_tool_call(self, pending_data: Dict[str, Any], body_data: Dict[str, Any], user_token: str):
        """Execute local tools and continue the conversation with the remote backend."""
        tool_calls = pending_data.get('tool_calls', []) or []
        if not tool_calls:
            logging.warning("[CHAT-PROXY] Pending tool payload without tool_calls")
            return

        messages = body_data.get('messages')
        if not isinstance(messages, list):
            logging.error("[CHAT-PROXY] Messages payload missing or invalid, resetting to list")
            messages = []
            body_data['messages'] = messages

        assistant_text = pending_data.get('assistant_text', '') or ''
        thinking_blocks = pending_data.get('thinking_blocks')
        if thinking_blocks:
            thinking_blocks = deepcopy(thinking_blocks)

        assistant_tool_calls = []
        for tool_call in tool_calls:
            function_info = tool_call.get('function', {}) or {}
            assistant_tool_calls.append({
                'id': tool_call.get('id', ''),
                'type': tool_call.get('type', 'function'),
                'function': {
                    'name': function_info.get('name', ''),
                    'arguments': function_info.get('arguments', '') or ''
                }
            })

        assistant_message: Dict[str, Any] = {
            'role': 'assistant',
            'tool_calls': assistant_tool_calls
        }

        if thinking_blocks:
            content_array = list(thinking_blocks)
            if assistant_text:
                content_array.append({
                    'type': 'text',
                    'text': assistant_text
                })
            assistant_message['content'] = content_array
        else:
            assistant_message['content'] = assistant_text if assistant_text else None

        messages.append(assistant_message)

        for idx, tool_call in enumerate(tool_calls):
            function_info = tool_call.get('function', {}) or {}
            tool_name = function_info.get('name', '')
            raw_arguments = function_info.get('arguments', '') or ''

            try:
                parsed_args = json.loads(raw_arguments) if raw_arguments else {}
            except json.JSONDecodeError:
                logging.warning(f"[CHAT-PROXY] Failed to parse tool arguments for {tool_name}: {raw_arguments}")
                parsed_args = {}

            tool_run = await run_ask_tool(tool_name, parsed_args)
            if tool_run is None:
                tool_result = f"Error: Unsupported tool '{tool_name}' in ask mode"
                sse_output = tool_result
            else:
                tool_result = tool_run["llm_output"]
                sse_output = tool_run["sse_output"]

            call_id = tool_call.get('id', f'tool_call_{idx}')

            messages.append({
                'role': 'tool',
                'tool_call_id': call_id,
                'content': tool_result
            })

            # Increment unified content index for tool output
            self._unified_content_index += 1
            
            await self._write_sse_event({
                'type': 'tool_call_output',
                'call_id': call_id,
                'output': sse_output,
                'content_index': self._unified_content_index,
                'status': 'streaming'
            })

        # Continue the conversation with updated messages
        await self._forward_to_remote_backend(body_data, True, user_token)

    async def options(self):
        """Handle CORS preflight requests."""
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.set_header("Access-Control-Allow-Headers", "Content-Type")
        self.set_status(200)


# For backward compatibility, also export as AIChatHandler
AIChatHandler = AIChatProxyHandler 
