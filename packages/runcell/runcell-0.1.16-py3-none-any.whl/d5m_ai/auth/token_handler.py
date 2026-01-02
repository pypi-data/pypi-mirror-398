"""
Token handler for saving and retrieving user authentication tokens from local files.

This handler manages the OAuth token storage when authentication succeeds,
allowing the proxy server to access user tokens without requiring frontend
to send tokens with every request.
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from jupyter_server.base.handlers import APIHandler
from tornado import web

logging.basicConfig(level=logging.INFO)

# Default token storage directory
TOKEN_STORAGE_DIR = os.path.expanduser("~/.d5m/tokens")


class TokenHandler(APIHandler):
    """Handler for managing user authentication tokens in local files."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.token_dir = Path(TOKEN_STORAGE_DIR)
        self.token_dir.mkdir(parents=True, exist_ok=True)
        logging.info(f"[TOKEN-HANDLER] Token storage directory: {self.token_dir}")

    def check_xsrf_cookie(self):
        """Override XSRF check for this internal authentication endpoint.
        
        This endpoint is used internally by the authenticated frontend to save tokens
        when OAuth succeeds. Since it's already behind Jupyter's authentication and
        used for internal token management, we disable XSRF protection.
        """
        # Do nothing to disable XSRF check
        return

    @web.authenticated
    async def post(self):
        """Save user token to local file when OAuth succeeds."""
        try:
            data = self.get_json_body()
            token = data.get("token")
            user = data.get("user", {})
            
            if not token:
                self.set_status(400)
                self.finish(json.dumps({"error": "No token provided"}))
                return

            if not user.get("id"):
                self.set_status(400)
                self.finish(json.dumps({"error": "No user ID provided"}))
                return

            user_id = user["id"]
            
            # Create token data
            token_data = {
                "token": token,
                "user": user,
                "saved_at": datetime.now(timezone.utc).isoformat(),
                "expires_at": data.get("expires_at")  # If provided
            }
            
            # Save to file named by user ID
            token_file = self.token_dir / f"{user_id}.json"
            
            with open(token_file, 'w') as f:
                json.dump(token_data, f, indent=2)
            
            logging.info(f"[TOKEN-HANDLER] ✅ Token saved for user: {user_id}")
            logging.info(f"[TOKEN-HANDLER] Token file: {token_file}")
            
            # Also save as "current" token for easy access
            current_token_file = self.token_dir / "current.json"
            with open(current_token_file, 'w') as f:
                json.dump(token_data, f, indent=2)
            
            logging.info(f"[TOKEN-HANDLER] ✅ Current token updated")
            
            self.finish(json.dumps({
                "success": True,
                "message": "Token saved successfully",
                "user_id": user_id
            }))
            
        except Exception as e:
            logging.error(f"[TOKEN-HANDLER] Error saving token: {e}")
            self.set_status(500)
            self.finish(json.dumps({"error": str(e)}))

    @web.authenticated  
    async def get(self):
        """Get current user token from local file."""
        try:
            user_id = self.get_argument("user_id", None)
            
            if user_id:
                # Get specific user's token
                token_file = self.token_dir / f"{user_id}.json"
            else:
                # Get current token
                token_file = self.token_dir / "current.json"
            
            if not token_file.exists():
                self.set_status(404)
                self.finish(json.dumps({"error": "No token found"}))
                return
            
            with open(token_file, 'r') as f:
                token_data = json.load(f)
            
            # Don't return the actual token for security, just metadata
            response_data = {
                "user": token_data.get("user"),
                "saved_at": token_data.get("saved_at"),
                "expires_at": token_data.get("expires_at"),
                "has_token": bool(token_data.get("token"))
            }
            
            self.finish(json.dumps(response_data))
            
        except Exception as e:
            logging.error(f"[TOKEN-HANDLER] Error getting token: {e}")
            self.set_status(500)
            self.finish(json.dumps({"error": str(e)}))

    @web.authenticated
    async def delete(self):
        """Delete user token (logout)."""
        try:
            user_id = self.get_argument("user_id", None)
            
            if user_id:
                # Delete specific user's token
                token_file = self.token_dir / f"{user_id}.json"
                if token_file.exists():
                    token_file.unlink()
                    logging.info(f"[TOKEN-HANDLER] Token deleted for user: {user_id}")
            
            # Also clear current token
            current_token_file = self.token_dir / "current.json"
            if current_token_file.exists():
                current_token_file.unlink()
                logging.info(f"[TOKEN-HANDLER] Current token cleared")
            
            self.finish(json.dumps({"success": True, "message": "Token deleted"}))
            
        except Exception as e:
            logging.error(f"[TOKEN-HANDLER] Error deleting token: {e}")
            self.set_status(500)
            self.finish(json.dumps({"error": str(e)}))


def get_current_user_token() -> Optional[Dict[str, Any]]:
    """
    Utility function to get the current user token from local file.
    Used by other handlers that need to access the user token.
    
    Returns:
        Token data dict if found, None otherwise
    """
    try:
        token_dir = Path(TOKEN_STORAGE_DIR)
        current_token_file = token_dir / "current.json"
        
        if not current_token_file.exists():
            logging.debug("[TOKEN-UTIL] No current token file found")
            return None
        
        with open(current_token_file, 'r') as f:
            token_data = json.load(f)
        
        token = token_data.get("token")
        if not token:
            logging.warning("[TOKEN-UTIL] Token file exists but no token found")
            return None
        
        logging.debug(f"[TOKEN-UTIL] ✅ Token loaded for user: {token_data.get('user', {}).get('id', 'unknown')}")
        return token_data
        
    except Exception as e:
        logging.error(f"[TOKEN-UTIL] Error reading token file: {e}")
        return None


def get_current_user_token_string() -> Optional[str]:
    """
    Utility function to get just the token string.
    
    Returns:
        Token string if found, None otherwise
    """
    token_data = get_current_user_token()
    return token_data.get("token") if token_data else None 