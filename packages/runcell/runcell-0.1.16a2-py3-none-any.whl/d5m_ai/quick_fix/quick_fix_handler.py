"""
Quick Fix proxy handler.

Forwards quick fix requests to the remote backend server.
"""

import asyncio
import aiohttp
import json
import logging
import ssl
import certifi
from typing import Optional
from jupyter_server.base.handlers import APIHandler
from tornado import web

from ..auth.token_handler import get_current_user_token_string
from ..utils import build_remote_backend_url

logging.basicConfig(level=logging.INFO)


class QuickFixApplyHandler(APIHandler):
    """Proxy handler for quick fix apply requests."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.remote_backend_url = build_remote_backend_url("chat").replace("/chat", "")
        logging.info(f"[QUICK-FIX-PROXY] Initialized with remote backend: {self.remote_backend_url}")

    def _create_ssl_context(self):
        try:
            certifi_ca_bundle = certifi.where()
            return ssl.create_default_context(cafile=certifi_ca_bundle)
        except Exception as e:
            logging.warning(f"[QUICK-FIX-PROXY] Failed to use certifi CA bundle: {e}, using default SSL context")
            return ssl.create_default_context()

    async def get_user_token(self) -> Optional[str]:
        local_token = get_current_user_token_string()
        if local_token:
            logging.info(f"[QUICK-FIX-PROXY] Found token in local file (length: {len(local_token)})")
            return local_token

        auth_header = self.request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            logging.info("[QUICK-FIX-PROXY] Found token in Authorization header")
            return token

        logging.warning("[QUICK-FIX-PROXY] No user token found")
        return None

    @web.authenticated
    async def post(self):
        try:
            try:
                body = json.loads(self.request.body)
            except json.JSONDecodeError:
                self.set_status(400)
                self.finish(json.dumps({"error": "Invalid JSON in request body"}))
                return

            prompt = body.get("prompt")
            selection_text = body.get("selectionText")
            match_mode = body.get("matchMode", "first")
            code_cells = body.get("codeCells")
            selection_cell_index = body.get("selectionCellIndex")
            file_content = body.get("fileContent")

            if not prompt or not selection_text:
                self.set_status(400)
                self.finish(json.dumps({"error": "Missing prompt or selection text"}))
                return

            if code_cells is None and file_content is None:
                self.set_status(400)
                self.finish(json.dumps({"error": "Missing codeCells or fileContent"}))
                return

            if code_cells is not None and selection_cell_index is None:
                self.set_status(400)
                self.finish(json.dumps({"error": "Missing selectionCellIndex for notebook request"}))
                return

            user_token = await self.get_user_token()
            if not user_token:
                self.set_status(401)
                self.finish(json.dumps({"error": "No authentication token found"}))
                return

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {user_token}"
            }

            request_data = {
                "prompt": prompt,
                "selectionText": selection_text,
                "matchMode": match_mode,
                "selectionRange": body.get("selectionRange"),
                "selectionCellIndex": selection_cell_index,
                "fileInfo": body.get("fileInfo"),
                "codeCells": code_cells,
                "fileContent": file_content
            }

            ssl_context = self._create_ssl_context()
            timeout = aiohttp.ClientTimeout(total=60)

            async with aiohttp.ClientSession(timeout=timeout) as session:
                url = f"{self.remote_backend_url}/quick_fix_apply"
                logging.info(f"[QUICK-FIX-PROXY] Forwarding request to: {url}")

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
                            logging.error(f"[QUICK-FIX-PROXY] Invalid JSON response: {response_text}")
                            self.set_status(500)
                            self.finish(json.dumps({"error": "Invalid response from server"}))
                    else:
                        logging.error(f"[QUICK-FIX-PROXY] Remote backend error {response.status}: {response_text}")
                        self.set_status(response.status)
                        self.finish(response_text)

        except asyncio.TimeoutError:
            logging.error("[QUICK-FIX-PROXY] Request timeout")
            self.set_status(408)
            self.finish(json.dumps({"error": "Request timeout"}))
        except Exception as e:
            logging.error(f"[QUICK-FIX-PROXY] Unexpected error: {str(e)}")
            self.set_status(500)
            self.finish(json.dumps({"error": f"Internal server error: {str(e)}"}))
