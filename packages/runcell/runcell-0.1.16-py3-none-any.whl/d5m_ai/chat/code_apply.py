from jupyter_server.base.handlers import APIHandler
from tornado import web
import json
import os
import ssl
import certifi
import aiohttp
from typing import List, Dict, Any, Optional

from ..auth.token_handler import get_current_user_token_string


# Remote server configuration
D5M_REMOTE_HOST = os.getenv("D5M_REMOTE_HOST", "service.runcell.dev")

# Construct the full URL
if D5M_REMOTE_HOST.startswith("localhost"):
    REMOTE_BACKEND_URL = f"http://{D5M_REMOTE_HOST}"
else:
    REMOTE_BACKEND_URL = f"https://{D5M_REMOTE_HOST}"

def parse_code_cells(code_cells: List[Dict[str, Any]]) -> List[str]:
    """Parse ICodeCell format into indexed strings for the AI model."""
    return [f"[cell index: {cell.get('index', i)}]: {cell.get('content', '')}" for i, cell in enumerate(code_cells)]

def capture_raw_json(text: str) -> str:
    # find the first { and the last }
    start = text.find('{')
    end = text.rfind('}') + 1
    return text[start:end]

class CodeApplyHandler(APIHandler):
    
    def _get_user_token(self) -> Optional[str]:
        """
        Get user token using existing token handler utility.
        This reuses the same authentication infrastructure as other handlers.
        """
        return get_current_user_token_string()
    
    @web.authenticated
    async def post(self):
        try:
            print("[CODE-APPLY-PROXY] Processing code apply request")
            
            # Get user token using token handler utility
            user_token = self._get_user_token()
            if not user_token:
                self.set_status(401)
                self.finish(json.dumps({
                    "error": "No authentication token provided. Please log in.",
                    "status": "auth_required"
                }))
                return
            
            data = json.loads(self.request.body)
            code = data.get('code')
            code_cells = data.get('codeCells')  # Now expects ICodeCell[] format
            recommended_action = data.get('recommendedAction')
            
            if not code or not code_cells:
                self.set_status(400)
                self.finish(json.dumps({"status": "error", "message": "Missing code or codeCells data"}))
                return
            
            # Prepare payload for remote server
            payload = {
                "code": code,
                "codeCells": code_cells,
                "recommendedAction": recommended_action
            }

            # Forward request to remote server
            try:
                remote_url = f"{REMOTE_BACKEND_URL}/code_apply"
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {user_token}"
                }
                
                print(f"[CODE-APPLY-PROXY] Forwarding authenticated request to: {remote_url}")
                
                # Create SSL context with proper certificate verification
                try:
                    ssl_context = ssl.create_default_context(cafile=certifi.where())
                    print(f"[CODE-APPLY-PROXY] Using certifi certificate bundle for SSL verification")
                except Exception as e:
                    print(f"[CODE-APPLY-PROXY] Failed to create SSL context with certifi: {e}")
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
                                        "error": "Authentication failed. Please log in again.",
                                        "status": "auth_error"
                                    }))
                                elif response.status == 402:
                                    self.set_status(402)
                                    self.finish(json.dumps({
                                        "error": error_message,
                                        "status": "insufficient_credits"
                                    }))
                                else:
                                    self.set_status(response.status)
                                    self.finish(json.dumps({
                                        "error": error_message,
                                        "status": error_status
                                    }))
                            except json.JSONDecodeError:
                                # Fallback for non-JSON error responses
                                self.set_status(response.status)
                                self.finish(json.dumps({"error": f"Remote server error: {error_text}"}))
                            return
                        
                        response_data = await response.json()
                        self.set_header("Content-Type", "application/json")
                        self.finish(json.dumps(response_data))
                        print("[CODE-APPLY-PROXY] Response forwarded successfully")

            except aiohttp.ClientError as e:
                print(f"[CODE-APPLY-PROXY] Network error: {e}")
                self.set_status(500)
                self.finish(json.dumps({"error": f"Failed to connect to remote server: {str(e)}"}))
            except Exception as e:
                print(f"[CODE-APPLY-PROXY] Unexpected error: {e}")
                self.set_status(500)
                self.finish(json.dumps({"error": f"Proxy error: {str(e)}"}))
        
        except Exception as e:
            print(f"[CODE-APPLY-PROXY] Handler error: {e}")
            self.set_status(500)
            self.finish(json.dumps({"error": str(e)}))
        
        
        
        