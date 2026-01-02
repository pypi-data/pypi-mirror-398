"""
Title generation proxy handler.

This handler acts as a proxy between the frontend and the remote backend server.
It forwards title generation requests to the remote backend.
"""

import asyncio
import aiohttp
import logging
import json
import ssl
import certifi
from typing import Optional
from jupyter_server.base.handlers import APIHandler
from tornado import web

from ..utils import build_remote_backend_url
from ..auth.token_handler import get_current_user_token_string

logging.basicConfig(level=logging.INFO)


class TitleGenerationHandler(APIHandler):
    """Proxy handler for title generation requests that forwards to remote backend."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Get remote backend URL
        self.remote_backend_url = build_remote_backend_url("chat").replace("/chat", "")
        logging.info(f"[TITLE-PROXY] Initialized with remote backend: {self.remote_backend_url}")
    
    def _create_ssl_context(self):
        """Create SSL context with proper certificate verification."""
        try:
            certifi_ca_bundle = certifi.where()
            return ssl.create_default_context(cafile=certifi_ca_bundle)
        except Exception as e:
            logging.warning(f"Failed to use certifi CA bundle: {e}, using default SSL context")
            return ssl.create_default_context()
    
    async def get_user_token(self) -> Optional[str]:
        """Extract user token from local file or request."""
        # Check local file token first
        local_token = get_current_user_token_string()
        if local_token:
            logging.info(f"[TITLE-PROXY] Found token in local file (length: {len(local_token)})")
            return local_token
        
        # Check Authorization header
        auth_header = self.request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            logging.info("[TITLE-PROXY] Found token in Authorization header")
            return token
        
        logging.warning("[TITLE-PROXY] No user token found")
        return None
    
    @web.authenticated
    async def post(self):
        """Handle title generation request."""
        try:
            # Parse request body
            try:
                body = json.loads(self.request.body)
                message = body.get("message", "")
            except json.JSONDecodeError:
                self.set_status(400)
                self.finish(json.dumps({"error": "Invalid JSON in request body"}))
                return
            
            if not message:
                self.set_status(400)
                self.finish(json.dumps({"error": "Message is required"}))
                return
            
            # Get user token
            user_token = await self.get_user_token()
            if not user_token:
                self.set_status(401)
                self.finish(json.dumps({"error": "No authentication token found"}))
                return
            
            # Prepare request to remote backend
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {user_token}"
            }
            
            request_data = {
                "message": message
            }
            
            # Make request to remote backend
            ssl_context = self._create_ssl_context()
            timeout = aiohttp.ClientTimeout(total=30)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                url = f"{self.remote_backend_url}/api/generate_title"
                logging.info(f"[TITLE-PROXY] Forwarding request to: {url}")
                
                async with session.post(
                    url,
                    json=request_data,
                    headers=headers,
                    ssl=ssl_context
                ) as response:
                    response_text = await response.text()
                    
                    if response.status == 200:
                        try:
                            response_data = json.loads(response_text)
                            self.finish(json.dumps(response_data))
                        except json.JSONDecodeError:
                            logging.error(f"[TITLE-PROXY] Invalid JSON response: {response_text}")
                            self.set_status(500)
                            self.finish(json.dumps({"error": "Invalid response from server"}))
                    else:
                        logging.error(f"[TITLE-PROXY] Remote backend error {response.status}: {response_text}")
                        self.set_status(response.status)
                        self.finish(response_text)
                        
        except asyncio.TimeoutError:
            logging.error("[TITLE-PROXY] Request timeout")
            self.set_status(408)
            self.finish(json.dumps({"error": "Request timeout"}))
        except Exception as e:
            logging.error(f"[TITLE-PROXY] Unexpected error: {str(e)}")
            self.set_status(500)
            self.finish(json.dumps({"error": f"Internal server error: {str(e)}"}))