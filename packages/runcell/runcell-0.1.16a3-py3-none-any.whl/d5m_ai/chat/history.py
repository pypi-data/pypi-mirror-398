from jupyter_server.base.handlers import APIHandler
import tornado.web as web
import os
import json
import asyncio
import logging
import re
import secrets
import string
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Set

from ..utils import build_remote_backend_url
from ..auth import get_current_user_token_string
import aiohttp
from ..image.handler import IMAGE_STORAGE_DIR

# Directory setup for history storage
HISTORY_DIR = os.path.join(os.path.expanduser('~'), '.d5m_ai', 'history')
HISTORY_DB_PATH = os.path.join(HISTORY_DIR, 'history_db.json')

MAX_LOCAL_HISTORIES = 100

# Pattern to match image paths regardless of host (localhost, private IP, domain, etc.)
# Only matches the pathname: /d5m-ai/image-service/<filename> or /d5m-ai/images/<filename>
IMAGE_URL_PATTERN = re.compile(r"/d5m-ai/(?:image-service|images)/([\w.\-]+)")
ALPHANUMERIC = string.ascii_lowercase + string.digits

# Create the history directory if it doesn't exist
os.makedirs(HISTORY_DIR, exist_ok=True)

# Initialize the history database if it doesn't exist
if not os.path.exists(HISTORY_DB_PATH):
    with open(HISTORY_DB_PATH, 'w') as f:
        json.dump([], f)


def _iter_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for nested in value.values():
            yield from _iter_strings(nested)
    elif isinstance(value, list):
        for item in value:
            yield from _iter_strings(item)


def _cleanup_images_from_history(history: Dict[str, Any]) -> None:
    messages = history.get("messages", [])
    image_names = set()
    for text in _iter_strings(messages):
        for match in IMAGE_URL_PATTERN.finditer(text):
            image_name = os.path.basename(match.group(1))
            if image_name:
                image_names.add(image_name)

    for image_name in image_names:
        image_path = os.path.join(IMAGE_STORAGE_DIR, image_name)
        if os.path.isfile(image_path):
            try:
                os.remove(image_path)
            except OSError:
                pass


def _delete_history_file_and_assets(history_id: str) -> None:
    if not history_id:
        return

    history_file_path = os.path.join(HISTORY_DIR, f"{history_id}.json")
    history_content: Optional[Dict[str, Any]] = None

    if os.path.exists(history_file_path):
        try:
            with open(history_file_path, 'r') as f:
                history_content = json.load(f)
        except Exception:
            history_content = None

        try:
            os.remove(history_file_path)
        except (FileNotFoundError, OSError):
            pass

    if history_content:
        _cleanup_images_from_history(history_content)


def _parse_updated_at(updated_at: Any) -> datetime:
    if isinstance(updated_at, str):
        try:
            return datetime.fromisoformat(updated_at)
        except ValueError:
            return datetime.min
    return datetime.min


def clear_old_histories(max_histories: int = MAX_LOCAL_HISTORIES) -> None:
    if max_histories <= 0:
        return

    try:
        with open(HISTORY_DB_PATH, 'r') as f:
            histories: List[Dict[str, Any]] = json.load(f)
    except Exception:
        return

    if not isinstance(histories, list):
        return

    sorted_histories = sorted(histories, key=lambda h: _parse_updated_at(h.get("updatedAt")), reverse=True)

    if len(sorted_histories) <= max_histories:
        return

    keep_histories = sorted_histories[:max_histories]
    histories_to_remove = sorted_histories[max_histories:]

    for history in histories_to_remove:
        history_id = history.get("id")
        if history_id:
            _delete_history_file_and_assets(history_id)

    try:
        with open(HISTORY_DB_PATH, 'w') as f:
            json.dump(keep_histories, f)
    except Exception:
        pass


def _generate_history_id(existing_ids: Optional[Set[str]] = None) -> str:
    while True:
        prefix = datetime.now().strftime("%Y%m%d%H%M")
        suffix = ''.join(secrets.choice(ALPHANUMERIC) for _ in range(4))
        history_id = f"{prefix}-{suffix}"

        if existing_ids and history_id in existing_ids:
            continue

        history_file_path = os.path.join(HISTORY_DIR, f"{history_id}.json")
        if not os.path.exists(history_file_path):
            return history_id


def _update_local_remote_id(history_id: Optional[str], remote_id: Optional[str]) -> None:
    if not history_id or not remote_id:
        return

    history_file_path = os.path.join(HISTORY_DIR, f"{history_id}.json")

    history_content: Optional[Dict[str, Any]] = None
    try:
        with open(history_file_path, 'r') as f:
            data = json.load(f)
            if isinstance(data, dict):
                history_content = data
    except Exception:
        history_content = None

    history_changed = False
    if history_content is not None and history_content.get("remoteId") != remote_id:
        history_content["remoteId"] = remote_id
        history_changed = True

    if history_changed:
        try:
            with open(history_file_path, 'w') as f:
                json.dump(history_content, f)
        except Exception:
            pass

    try:
        with open(HISTORY_DB_PATH, 'r') as f:
            histories: List[Dict[str, Any]] = json.load(f)
    except Exception:
        return

    if not isinstance(histories, list):
        return

    db_changed = False
    for entry in histories:
        if isinstance(entry, dict) and entry.get("id") == history_id:
            if entry.get("remoteId") != remote_id:
                entry["remoteId"] = remote_id
                db_changed = True
            break

    if db_changed:
        try:
            with open(HISTORY_DB_PATH, 'w') as f:
                json.dump(histories, f)
        except Exception:
            pass


class AIChatHistoryListHandler(APIHandler):
    @web.authenticated
    async def get(self):
        """Get a list of all chat histories"""
        try:
            # Read the history database file
            with open(HISTORY_DB_PATH, 'r') as f:
                histories = json.load(f)
            
            # Sort histories by updatedAt in descending order (newest first)
            # Parse ISO format date strings for proper sorting
            def get_updated_at_datetime(history):
                updated_at = history.get("updatedAt", "")
                try:
                    return datetime.fromisoformat(updated_at)
                except (ValueError, TypeError):
                    # Return a very old date as fallback
                    return datetime.min
                    
            histories.sort(key=get_updated_at_datetime, reverse=True)
            
            # Return the list of histories
            self.finish(json.dumps({"histories": histories, "status": "success"}))
        except Exception as e:
            self.set_status(500)
            self.finish(json.dumps({"error": str(e), "status": "error"}))

class AIChatHistoryHandler(APIHandler):
    @web.authenticated
    async def get(self):
        """Get a specific chat history"""
        try:
            # Get history_id from query parameters
            history_id = self.get_query_argument("history_id", None)
            
            if not history_id:
                self.set_status(400)
                self.finish(json.dumps({"error": "History ID is required", "status": "error"}))
                return
                
            # Build the path to the history file
            history_file_path = os.path.join(HISTORY_DIR, f"{history_id}.json")
            
            # Check if the history file exists
            if not os.path.exists(history_file_path):
                self.set_status(404)
                self.finish(json.dumps({"error": "History not found", "status": "error"}))
                return
            
            # Read the history file
            with open(history_file_path, 'r') as f:
                history = json.load(f)
            
            # Return the history
            self.finish(json.dumps({"history": history, "status": "success"}))
        except Exception as e:
            self.set_status(500)
            self.finish(json.dumps({"error": str(e), "status": "error"}))
    
    @web.authenticated
    async def post(self):
        """Create a new chat history"""
        try:
            # Parse the request body
            body = json.loads(self.request.body.decode("utf-8"))
            
            with open(HISTORY_DB_PATH, 'r') as f:
                histories: List[Dict[str, Any]] = json.load(f)

            if not isinstance(histories, list):
                histories = []

            existing_ids: Set[str] = {h.get("id") for h in histories if isinstance(h, dict) and isinstance(h.get("id"), str)}

            # Get history_id from body or generate a new one
            provided_history_id = body.get("history_id")
            if provided_history_id:
                history_id = provided_history_id
                if provided_history_id in existing_ids:
                    self.set_status(409)
                    self.finish(json.dumps({"error": "History ID already exists", "status": "error"}))
                    return
            else:
                history_id = _generate_history_id(existing_ids)

            # Get the title or use a default
            title = body.get("title", f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

            # Create the history object
            now = datetime.now().isoformat()
            history = {
                "id": history_id,
                "title": title,
                "createdAt": now,
                "updatedAt": now,
                "messages": body.get("messages", [])
            }

            remote_id = body.get("remoteId")
            if remote_id:
                history["remoteId"] = remote_id

            # Save the full history to a file
            history_file_path = os.path.join(HISTORY_DIR, f"{history_id}.json")
            with open(history_file_path, 'w') as f:
                json.dump(history, f)

            # Update the history database
            history_brief = {
                "id": history_id,
                "title": title,
                "createdAt": now,
                "updatedAt": now
            }

            if remote_id:
                history_brief["remoteId"] = remote_id

            histories.append(history_brief)

            with open(HISTORY_DB_PATH, 'w') as f:
                json.dump(histories, f)

            clear_old_histories()
            
            # Return the created history
            self.finish(json.dumps({"history": history, "status": "success"}))

            # Fire-and-forget remote backup (non-blocking, best-effort)
            try:
                asyncio.create_task(self._backup_history_remote(history))
            except Exception as e:
                logging.debug(f"[CHAT-HISTORY] Failed to schedule remote backup: {e}")
        except Exception as e:
            self.set_status(500)
            self.finish(json.dumps({"error": str(e), "status": "error"}))
    
    @web.authenticated
    async def put(self):
        """Update an existing chat history"""
        try:
            # Parse the request body
            body = json.loads(self.request.body.decode("utf-8"))
            history_id = body.get("history_id")
            
            if not history_id:
                self.set_status(400)
                self.finish(json.dumps({"error": "History ID is required", "status": "error"}))
                return
                
            # Build the path to the history file
            history_file_path = os.path.join(HISTORY_DIR, f"{history_id}.json")
            
            # Check if the history file exists
            if not os.path.exists(history_file_path):
                self.set_status(404)
                self.finish(json.dumps({"error": "History not found", "status": "error"}))
                return
            
            # Read the current history
            with open(history_file_path, 'r') as f:
                history = json.load(f)
            
            # Update the history
            title = body.get("title")
            messages = body.get("messages")
            
            now = datetime.now().isoformat()
            history["updatedAt"] = now
            
            if title:
                history["title"] = title
            
            if messages:
                history["messages"] = messages
            
            # Save the updated history
            with open(history_file_path, 'w') as f:
                json.dump(history, f)

            # Update the history database
            with open(HISTORY_DB_PATH, 'r') as f:
                histories: List[Dict[str, Any]] = json.load(f)

            if not isinstance(histories, list):
                histories = []

            for i, h in enumerate(histories):
                if isinstance(h, dict) and h.get("id") == history_id:
                    histories[i]["title"] = history["title"]
                    histories[i]["updatedAt"] = now
                    remote_id = history.get("remoteId")
                    if remote_id:
                        histories[i]["remoteId"] = remote_id
                    elif "remoteId" in histories[i]:
                        histories[i].pop("remoteId", None)
                    break

            with open(HISTORY_DB_PATH, 'w') as f:
                json.dump(histories, f)

            clear_old_histories()
            
            # Return the updated history
            self.finish(json.dumps({"history": history, "status": "success"}))

            # Fire-and-forget remote backup (non-blocking, best-effort)
            try:
                asyncio.create_task(self._backup_history_remote(history))
            except Exception as e:
                logging.debug(f"[CHAT-HISTORY] Failed to schedule remote backup: {e}")
        except Exception as e:
            self.set_status(500)
            self.finish(json.dumps({"error": str(e), "status": "error"}))
    
    @web.authenticated
    async def delete(self):
        """Delete a chat history"""
        try:
            # Parse the request body
            body = json.loads(self.request.body.decode("utf-8"))
            history_id = body.get("history_id")
            
            if not history_id:
                self.set_status(400)
                self.finish(json.dumps({"error": "History ID is required", "status": "error"}))
                return
                
            # Build the path to the history file
            history_file_path = os.path.join(HISTORY_DIR, f"{history_id}.json")

            # Check if the history file exists
            if not os.path.exists(history_file_path):
                self.set_status(404)
                self.finish(json.dumps({"error": "History not found", "status": "error"}))
                return

            # Delete the history file and associated assets
            _delete_history_file_and_assets(history_id)

            # Update the history database
            with open(HISTORY_DB_PATH, 'r') as f:
                histories: List[Dict[str, Any]] = json.load(f)

            if not isinstance(histories, list):
                histories = []

            histories = [h for h in histories if isinstance(h, dict) and h.get("id") != history_id]

            with open(HISTORY_DB_PATH, 'w') as f:
                json.dump(histories, f)
            
            # Return success
            self.finish(json.dumps({"status": "success"}))
        except Exception as e:
            self.set_status(500)
            self.finish(json.dumps({"error": str(e), "status": "error"}))

    async def _backup_history_remote(self, history: Dict[str, Any]):
        """Send chat history to remote backup endpoint without impacting UX."""
        try:
            token = get_current_user_token_string()
            if not token:
                return

            # Build remote chat HTTP base and then join backup path
            chat_base = build_remote_backend_url("chat")  # e.g. https://host/chat
            # Replace trailing '/chat' with our backup path root
            if chat_base.endswith('/chat'):
                base = chat_base.rsplit('/chat', 1)[0]
            else:
                base = chat_base
            url = f"{base}/chat_history/backup"

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            }

            payload = {
                "title": history.get("title"),
                "createdAt": history.get("createdAt"),
                "updatedAt": history.get("updatedAt"),
                "messages": history.get("messages", []),
                "version": 1,
            }

            remote_id = history.get("remoteId")
            if remote_id:
                payload["id"] = remote_id

            local_history_id = history.get("id")

            response_text = ""
            timeout = aiohttp.ClientTimeout(total=3)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=payload, headers=headers) as resp:
                    # Best-effort; don't raise for status
                    response_text = await resp.text()

            new_remote_id: Optional[str] = None
            if remote_id:
                new_remote_id = remote_id

            try:
                response_data = json.loads(response_text) if response_text else {}
            except Exception:
                response_data = {}

            response_remote_id = response_data.get("id")
            if response_remote_id:
                new_remote_id = response_remote_id

            if new_remote_id and new_remote_id != history.get("remoteId"):
                history["remoteId"] = new_remote_id

            if new_remote_id:
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, _update_local_remote_id, local_history_id, new_remote_id)
        except Exception:
            # Completely swallow errors to avoid UX impact
            pass
