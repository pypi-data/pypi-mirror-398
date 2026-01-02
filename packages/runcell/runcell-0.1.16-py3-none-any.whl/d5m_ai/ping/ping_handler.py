import asyncio
import aiohttp
import ssl
import certifi
import os
from jupyter_server.base.handlers import APIHandler
from tornado import web
import json

from ..utils import build_remote_backend_url

class PingProxyHandler(APIHandler):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Get remote backend URL using unified URL builder
        self.remote_backend_url = build_remote_backend_url("chat").replace("/chat", "")
        
    def _create_ssl_context(self):
        """
        Create SSL context with proper certificate verification and fallback handling.
        This handles cases where certifi bundle might not be accessible in packaged environments.
        """
        try:
            # Try to use certifi's certificate bundle first
            certifi_ca_bundle = certifi.where()
            if os.path.exists(certifi_ca_bundle):
                return ssl.create_default_context(cafile=certifi_ca_bundle)
            else:
                # If certifi bundle doesn't exist, log and fall back
                self.log.warning(f"Certifi CA bundle not found at {certifi_ca_bundle}, using default SSL context")
        except Exception as e:
            # If certifi fails entirely, log and fall back
            self.log.warning(f"Failed to use certifi CA bundle: {e}, using default SSL context")
        
        # Fallback to default SSL context
        try:
            # Try to create default context without specifying cafile
            return ssl.create_default_context()
        except Exception as e:
            self.log.error(f"Failed to create default SSL context: {e}")
            # Last resort: create unverified context (not recommended but better than complete failure)
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            self.log.warning("Using unverified SSL context as last resort - this is not secure")
            return context

    @web.authenticated
    async def get(self):
        """
        Proxy ping request to the remote service to avoid CORS issues
        """
        try:
            # Create SSL context with proper certificate verification and fallback handling
            ssl_context = self._create_ssl_context()
            timeout = aiohttp.ClientTimeout(total=5)  # 5 second timeout
            
            # Create connector with SSL context
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
                ping_url = f"{self.remote_backend_url}/ping"
                async with session.head(ping_url) as response:
                    if response.status == 200:
                        self.finish(json.dumps({"status": "success", "message": "Service is online"}))
                    else:
                        self.finish(json.dumps({"status": "error", "message": f"Service returned {response.status}"}))
        except asyncio.TimeoutError:
            self.set_status(408)  # Request Timeout
            self.finish(json.dumps({"status": "error", "message": "Request timeout"}))
        except Exception as e:
            self.set_status(500)
            self.finish(json.dumps({"status": "error", "message": f"Connection failed: {str(e)}"}))


class PingLocalHandler(APIHandler):
    @web.authenticated
    async def get(self):
        """
        Local health check for the Jupyter backend.
        """
        self.finish(json.dumps({"status": "success", "message": "Jupyter backend is online"}))
