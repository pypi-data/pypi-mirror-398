import asyncio
import json
import os
import time
from typing import Dict, Optional

from jupyter_server.base.handlers import APIHandler
import tornado.web


_CACHE_TTL_SECONDS = 2.0
_cache_timestamp = 0.0
_cache_root: Optional[str] = None
_cache_payload: Optional[Dict[str, object]] = None
_cache_lock = asyncio.Lock()


def _status_priority(status: str) -> int:
    if status == "modified":
        return 3
    if status == "added":
        return 2
    if status == "deleted":
        return 1
    return 0


def _merge_status(current: Optional[str], incoming: str) -> str:
    if not current:
        return incoming
    return incoming if _status_priority(incoming) > _status_priority(current) else current


def _map_git_status(code: str) -> Optional[str]:
    if code == "??":
        return "added"
    if "M" in code or "R" in code or "C" in code or "U" in code:
        return "modified"
    if "A" in code:
        return "added"
    if "D" in code:
        return "deleted"
    return None


def _parse_git_status(output: str) -> Dict[str, str]:
    entries = output.split("\0")
    statuses: Dict[str, str] = {}
    index = 0

    while index < len(entries):
        token = entries[index]
        index += 1

        if not token or len(token) < 3:
            continue

        status_code = token[:2]
        path = token[3:]

        if status_code[0] in ("R", "C") or status_code[1] in ("R", "C"):
            if index < len(entries):
                path = entries[index]
                index += 1

        status = _map_git_status(status_code)
        if not status or not path:
            continue

        statuses[path] = _merge_status(statuses.get(path), status)

    return statuses


async def _get_repo_root(root_dir: str) -> Optional[str]:
    try:
        process = await asyncio.create_subprocess_exec(
            "git",
            "rev-parse",
            "--show-toplevel",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=root_dir
        )
    except Exception:
        return None

    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        return None

    output = stdout.decode("utf-8", errors="replace").strip()
    return output or None


def _normalize_rel_path(path: str) -> str:
    return path.replace(os.sep, "/").lstrip("./")


def _adjust_status_paths(
    statuses: Dict[str, str],
    root_dir: str,
    repo_root: str
) -> Dict[str, str]:
    root_dir = os.path.abspath(root_dir)
    repo_root = os.path.abspath(repo_root)

    if root_dir == repo_root:
        return statuses

    try:
        repo_rel_to_root = os.path.relpath(repo_root, root_dir)
    except ValueError:
        return statuses

    repo_rel_to_root = _normalize_rel_path(repo_rel_to_root)
    if repo_rel_to_root and not repo_rel_to_root.startswith(".."):
        adjusted: Dict[str, str] = {}
        for path, status in statuses.items():
            adjusted_path = f"{repo_rel_to_root}/{path}" if path else repo_rel_to_root
            adjusted[adjusted_path] = _merge_status(adjusted.get(adjusted_path), status)
        return adjusted

    server_rel_to_repo = _normalize_rel_path(os.path.relpath(root_dir, repo_root))
    if not server_rel_to_repo or server_rel_to_repo.startswith(".."):
        return statuses

    adjusted: Dict[str, str] = {}
    prefix = f"{server_rel_to_repo}/"
    for path, status in statuses.items():
        if path.startswith(prefix):
            trimmed = path[len(prefix):]
            if trimmed:
                adjusted[trimmed] = _merge_status(adjusted.get(trimmed), status)
    return adjusted


async def _run_git_status(root_dir: str) -> Dict[str, object]:
    try:
        process = await asyncio.create_subprocess_exec(
            "git",
            "status",
            "--porcelain=1",
            "-z",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=root_dir
        )
    except Exception as exc:
        return {
            "success": False,
            "repo": False,
            "statuses": {},
            "error": str(exc)
        }

    stdout, stderr = await process.communicate()
    stderr_text = stderr.decode("utf-8", errors="replace").strip()

    if process.returncode != 0:
        if "not a git repository" in stderr_text.lower():
            return {
                "success": True,
                "repo": False,
                "statuses": {}
            }
        return {
            "success": False,
            "repo": False,
            "statuses": {},
            "error": stderr_text or "Failed to run git status."
        }

    output = stdout.decode("utf-8", errors="replace")
    repo_root = await _get_repo_root(root_dir)
    statuses = _parse_git_status(output)
    if repo_root:
        statuses = _adjust_status_paths(statuses, root_dir, repo_root)
    return {
        "success": True,
        "repo": True,
        "statuses": statuses
    }


async def _get_cached_status(root_dir: str) -> Dict[str, object]:
    global _cache_timestamp, _cache_payload, _cache_root
    now = time.monotonic()

    if _cache_payload and _cache_root == root_dir and (now - _cache_timestamp) < _CACHE_TTL_SECONDS:
        return _cache_payload

    async with _cache_lock:
        now = time.monotonic()
        if _cache_payload and _cache_root == root_dir and (now - _cache_timestamp) < _CACHE_TTL_SECONDS:
            return _cache_payload

        payload = await _run_git_status(root_dir)
        _cache_payload = payload
        _cache_root = root_dir
        _cache_timestamp = time.monotonic()
        return payload


class GitStatusHandler(APIHandler):
    @tornado.web.authenticated
    async def get(self):
        await self._handle()

    @tornado.web.authenticated
    async def post(self):
        await self._handle()

    async def _handle(self):
        root_dir = getattr(self.contents_manager, "root_dir", None)
        if not root_dir:
            root_dir = (
                self.settings.get("server_root_dir")
                or self.settings.get("root_dir")
                or os.getcwd()
            )

        root_dir = os.path.abspath(root_dir)
        payload = await _get_cached_status(root_dir)
        self.finish(json.dumps(payload))
