import json
import os
import ssl
import certifi
from typing import Optional
from jupyter_server.base.handlers import APIHandler
import tornado
import aiohttp

# Import token handler for user authentication
from d5m_ai.auth.token_handler import get_current_user_token_string
from .._version import __version__ as client_version

# Remote server configuration
D5M_REMOTE_HOST = os.getenv("D5M_REMOTE_HOST", "service.runcell.dev")

# Construct the full URL
if D5M_REMOTE_HOST.startswith("localhost"):
    REMOTE_BACKEND_URL = f"http://{D5M_REMOTE_HOST}"
else:
    REMOTE_BACKEND_URL = f"https://{D5M_REMOTE_HOST}"

class AnthropicCompletionHandler(APIHandler):
    """
    Handler for Anthropic AI code completion requests.
    """

    def _get_user_token(self) -> Optional[str]:
        """
        Get user token using existing token handler utility.
        This reuses the same authentication infrastructure as other handlers.
        """
        return get_current_user_token_string()

    @tornado.web.authenticated
    async def post(self):
        """Handle POST requests to the Anthropic completion endpoint"""
        try:
            print("AnthropicCompletionHandler")
            
            # Get user token using token handler utility
            user_token = self._get_user_token()
            if not user_token:
                self.set_status(401)
                self.finish(json.dumps({
                    "success": False,
                    "error": "No authentication token provided. Please log in.",
                    "status": "auth_required"
                }))
                return

            # Parse the request
            input_data = self.get_json_body()
            code = input_data.get("code", "")
            language = input_data.get("language", "python")

            # Prepare payload for remote server
            payload = {
                "code": code,
                "language": language,
                "client_version": client_version
            }

            # Forward request to remote server
            try:
                remote_url = f"{REMOTE_BACKEND_URL}/completion"
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {user_token}"
                }
                
                print(f"[ANTHROPIC-COMPLETION-PROXY] Forwarding authenticated request to: {remote_url}")
                
                # Create SSL context with proper certificate verification
                try:
                    ssl_context = ssl.create_default_context(cafile=certifi.where())
                    print(f"[ANTHROPIC-COMPLETION-PROXY] Using certifi certificate bundle for SSL verification")
                except Exception as e:
                    print(f"[ANTHROPIC-COMPLETION-PROXY] Failed to create SSL context with certifi: {e}")
                    # Fallback to default SSL context
                    ssl_context = ssl.create_default_context()
                
                # Create connector with SSL context
                connector = aiohttp.TCPConnector(ssl=ssl_context)
                
                async with aiohttp.ClientSession(connector=connector) as session:
                    async with session.post(remote_url, json=payload, headers=headers) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            
                            # Try to parse error as JSON for better error handling
                            try:
                                error_data = json.loads(error_text)
                                error_status = error_data.get("status", "error")
                                error_message = error_data.get("error", error_text)
                                
                                # Handle specific error types
                                if response.status == 401:
                                    self.set_status(401)
                                    self.finish(json.dumps({
                                        "success": False,
                                        "error": "Authentication failed. Please log in again.",
                                        "status": "auth_error"
                                    }))
                                elif response.status == 402:
                                    self.set_status(402)
                                    self.finish(json.dumps({
                                        "success": False,
                                        "error": error_message,
                                        "status": "insufficient_credits"
                                    }))
                                else:
                                    self.set_status(response.status)
                                    self.finish(json.dumps({
                                        "success": False,
                                        "error": error_message,
                                        "status": error_status
                                    }))
                            except json.JSONDecodeError:
                                # Fallback for non-JSON error responses
                                self.set_status(response.status)
                                self.finish(json.dumps({
                                    "success": False,
                                    "error": f"Remote server error: {error_text}"
                                }))
                            return
                        
                        response_data = await response.json()
                        self.set_header("Content-Type", "application/json")
                        self.finish(json.dumps(response_data))
                        print("[ANTHROPIC-COMPLETION-PROXY] Response forwarded successfully")

            except aiohttp.ClientError as e:
                print(f"[ANTHROPIC-COMPLETION-PROXY] Network error: {e}")
                self.set_status(500)
                self.finish(json.dumps({"error": f"Failed to connect to remote server: {str(e)}"}))
            except Exception as e:
                print(f"[ANTHROPIC-COMPLETION-PROXY] Unexpected error: {e}")
                self.set_status(500)
                self.finish(json.dumps({"error": f"Proxy error: {str(e)}"}))

        except Exception as e:
            print(f"[ANTHROPIC-COMPLETION-PROXY] Handler error: {e}")
            self.set_status(500)
            self.finish(json.dumps({"error": str(e)}))

