"""
Empty display proxy handler.

Forwards empty state display requests to the SaaS backend to avoid CORS issues.
"""

import asyncio
import aiohttp
import certifi
import json
import logging
import os
import ssl
from typing import Optional
from urllib.parse import urlparse

from jupyter_server.base.handlers import APIHandler
from tornado import web

from ..auth.token_handler import get_current_user_token_string

logging.basicConfig(level=logging.INFO)

DEFAULT_SAAS_URL = "https://www.runcell.dev"
ALLOWED_HOST_SUFFIXES = (".runcell.dev",)
ALLOWED_HOSTS = {"runcell.dev", "www.runcell.dev", "localhost", "127.0.0.1"}


def _is_allowed_host(hostname: str) -> bool:
    if not hostname:
        return False
    hostname = hostname.lower()
    if hostname in ALLOWED_HOSTS:
        return True
    return any(hostname.endswith(suffix) for suffix in ALLOWED_HOST_SUFFIXES)


class EmptyDisplayProxyHandler(APIHandler):
    """Proxy handler for empty display requests."""

    def _create_ssl_context(self):
        try:
            certifi_ca_bundle = certifi.where()
            return ssl.create_default_context(cafile=certifi_ca_bundle)
        except Exception as error:
            logging.warning(f"[EMPTY-DISPLAY-PROXY] Failed to use certifi CA bundle: {error}")
            return ssl.create_default_context()

    def _resolve_saas_url(self, saas_url: Optional[str]) -> str:
        candidate = saas_url or os.environ.get("D5M_SAAS_URL") or DEFAULT_SAAS_URL
        candidate = candidate.strip()

        parsed = urlparse(candidate)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("Invalid SaaS URL")

        if not _is_allowed_host(parsed.hostname or ""):
            raise ValueError("SaaS URL host not allowed")

        return f"{parsed.scheme}://{parsed.netloc}".rstrip("/")

    def _extract_token(self) -> Optional[str]:
        local_token = get_current_user_token_string()
        if local_token:
            return local_token

        auth_header = self.request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return auth_header[7:]

        return None

    @web.authenticated
    async def post(self):
        try:
            try:
                body = json.loads(self.request.body or b"{}")
            except json.JSONDecodeError:
                self.set_status(400)
                self.finish(json.dumps({"error": "Invalid JSON in request body"}))
                return

            ping_status = body.get("ping_status") or {}
            payload = {
                "runcell_version": body.get("runcell_version", ""),
                "ping_status": {
                    "local": bool(ping_status.get("local")),
                    "remote": bool(ping_status.get("remote"))
                }
            }

            if "logged_in" in body:
                payload["logged_in"] = bool(body.get("logged_in"))
            if "user_id" in body:
                payload["user_id"] = body.get("user_id")

            try:
                saas_url = self._resolve_saas_url(body.get("saas_url"))
            except ValueError as error:
                self.set_status(400)
                self.finish(json.dumps({"error": str(error)}))
                return

            user_token = self._extract_token()
            headers = {"Content-Type": "application/json"}
            if user_token:
                headers["Authorization"] = f"Bearer {user_token}"

            ssl_context = self._create_ssl_context()
            timeout = aiohttp.ClientTimeout(total=10)

            async with aiohttp.ClientSession(timeout=timeout) as session:
                url = f"{saas_url}/api/plugin-auth/empty_display"
                logging.info(f"[EMPTY-DISPLAY-PROXY] Forwarding request to: {url}")
                async with session.post(url, json=payload, headers=headers, ssl=ssl_context) as response:
                    response_text = await response.text()
                    if response.status == 200:
                        try:
                            response_data = json.loads(response_text)
                            self.finish(json.dumps(response_data))
                        except json.JSONDecodeError:
                            logging.error("[EMPTY-DISPLAY-PROXY] Invalid JSON response")
                            self.set_status(502)
                            self.finish(json.dumps({"error": "Invalid response from server"}))
                    else:
                        logging.error(f"[EMPTY-DISPLAY-PROXY] Remote error {response.status}: {response_text}")
                        self.set_status(response.status)
                        self.finish(response_text)

        except asyncio.TimeoutError:
            logging.error("[EMPTY-DISPLAY-PROXY] Request timeout")
            self.set_status(408)
            self.finish(json.dumps({"error": "Request timeout"}))
        except Exception as error:
            logging.error(f"[EMPTY-DISPLAY-PROXY] Unexpected error: {error}")
            self.set_status(500)
            self.finish(json.dumps({"error": f"Internal server error: {error}"}))
