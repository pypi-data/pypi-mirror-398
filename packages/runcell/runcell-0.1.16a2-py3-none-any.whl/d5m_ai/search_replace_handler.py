import json
import os
import re
import subprocess
from typing import Any, Dict, Iterable, List, Optional, Tuple

from jupyter_server.base.handlers import APIHandler
import tornado.web

from .tools.grep import execute_grep_tool
from .tools.edit import edit_file_text


DEFAULT_MATCH_LIMIT = 200
MAX_MATCH_LIMIT = 1000
DEFAULT_EXCLUDE_DIRS = [
    "node_modules",
    ".ipynb_checkpoints",
    "jupyterlab-env",
    "build",
    "lib",
    "dist",
    "__pycache__",
    ".git",
]
DEFAULT_EXCLUDE_GLOBS: List[str] = []


def _get_root_dir(handler: APIHandler) -> str:
    root_dir = getattr(handler.contents_manager, "root_dir", None)
    if not root_dir:
        root_dir = (
            handler.settings.get("server_root_dir")
            or handler.settings.get("root_dir")
            or os.getcwd()
        )
    return os.path.abspath(root_dir)


def _get_repo_root(root_dir: str) -> Optional[str]:
    if os.path.isdir(os.path.join(root_dir, ".git")):
        return root_dir

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=root_dir,
            capture_output=True,
            text=True,
            check=False
        )
    except Exception:
        return None

    if result.returncode != 0:
        return None

    output = (result.stdout or "").strip()
    return output or None


def _resolve_target_dir(root_dir: str, path_arg: str) -> str:
    if not path_arg or path_arg in (".", "/"):
        target_dir = root_dir
    else:
        cleaned = path_arg.lstrip("/").lstrip("\\")
        target_dir = os.path.abspath(os.path.join(root_dir, cleaned))

    root_dir = os.path.abspath(root_dir)
    if os.path.commonpath([root_dir, target_dir]) != root_dir:
        raise ValueError("Path is outside server root.")
    return target_dir


def _to_display_path(file_path: str, root_dir: str) -> str:
    if not file_path:
        return file_path
    try:
        rel_path = os.path.relpath(file_path, root_dir)
    except ValueError:
        return file_path
    if rel_path.startswith(".."):
        return file_path
    return rel_path.replace(os.sep, "/")


def _split_list_input(value: Any) -> List[str]:
    if not value:
        return []

    if isinstance(value, str):
        raw_items = re.split(r"[,\n]", value)
    elif isinstance(value, Iterable):
        raw_items = []
        for item in value:
            if isinstance(item, str):
                raw_items.extend(re.split(r"[,\n]", item))
            else:
                raw_items.append(str(item))
    else:
        raw_items = [str(value)]

    cleaned = []
    for item in raw_items:
        stripped = item.strip().strip('"').strip("'")
        if stripped:
            cleaned.append(stripped)
    return cleaned


def _extract_simple_dir(pattern: str) -> Optional[str]:
    candidate = pattern.strip().lstrip("/").rstrip("/")
    if not candidate:
        return None
    if candidate.startswith("**/") and candidate.endswith("/**"):
        candidate = candidate[3:-3]
    if any(char in candidate for char in ("*", "?", "[", "]", "/", "\\")):
        return None
    return candidate or None


def _classify_excludes(patterns: Iterable[str]) -> Tuple[List[str], List[str]]:
    exclude_dirs: List[str] = []
    exclude_globs: List[str] = []

    for raw in patterns:
        pattern = raw.strip()
        if not pattern or pattern.startswith("#"):
            continue
        if pattern.startswith("!"):
            continue

        pattern = pattern.lstrip("/")
        simple_dir = _extract_simple_dir(pattern)
        if simple_dir:
            exclude_dirs.append(simple_dir)
            exclude_globs.append(simple_dir)
            continue

        if pattern.endswith("/"):
            exclude_dirs.append(pattern.rstrip("/"))
            continue

        exclude_globs.append(pattern)

    def dedupe(items: List[str]) -> List[str]:
        seen: set[str] = set()
        output: List[str] = []
        for item in items:
            if item not in seen:
                seen.add(item)
                output.append(item)
        return output

    return dedupe(exclude_dirs), dedupe(exclude_globs)


def _load_gitignore_patterns(root_dir: str) -> List[str]:
    gitignore_path = os.path.join(root_dir, ".gitignore")
    if not os.path.isfile(gitignore_path):
        return []

    try:
        with open(gitignore_path, "r", encoding="utf-8") as handle:
            lines = handle.readlines()
    except Exception:
        return []

    patterns = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        patterns.append(stripped)
    return patterns


def _parse_bool(value: Any, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"0", "false", "no", "off"}:
            return False
        if lowered in {"1", "true", "yes", "on"}:
            return True
    return bool(value)


def _parse_grep_response(result: str) -> Tuple[str, List[Dict[str, Any]], bool]:
    try:
        data = json.loads(result)
    except json.JSONDecodeError:
        return "Failed to parse search response.", [], False

    if data.get("result_type") == "error":
        return data.get("summary") or "Search failed.", [], False

    matches = data.get("matches") or []
    return data.get("summary") or "", matches, bool(data.get("truncated"))


def _parse_files_response(result: str) -> Tuple[str, List[str]]:
    try:
        data = json.loads(result)
    except json.JSONDecodeError:
        return "Failed to parse search response.", []

    if data.get("result_type") == "error":
        return data.get("summary") or "Search failed.", []

    files = data.get("files") or []
    return data.get("summary") or "", files


def _parse_replace_count(message: str) -> int:
    match = re.search(r"replaced (\d+) occurrence", message or "")
    if not match:
        return 0
    try:
        return int(match.group(1))
    except ValueError:
        return 0


class SearchReplaceHandler(APIHandler):
    @tornado.web.authenticated
    async def post(self):
        payload = self.get_json_body() or {}
        action = (payload.get("action") or "search").strip().lower()
        query = (payload.get("query") or "").strip()
        regex_enabled = bool(payload.get("regex"))
        case_sensitive = bool(payload.get("caseSensitive", True))
        replace_text = payload.get("replace")
        path_arg = (payload.get("path") or "").strip()
        use_default_excludes = _parse_bool(payload.get("useDefaultExcludes"), True)
        user_excludes = _split_list_input(payload.get("exclude"))
        include_patterns = _split_list_input(payload.get("include"))

        if not query:
            self.set_status(400)
            self.finish(json.dumps({
                "success": False,
                "error": "Search query is required."
            }))
            return

        root_dir = _get_root_dir(self)
        try:
            target_dir = _resolve_target_dir(root_dir, path_arg)
        except ValueError:
            self.set_status(400)
            self.finish(json.dumps({
                "success": False,
                "error": "Invalid path. Must be inside the server root."
            }))
            return

        hard_excludes: List[str] = []
        ignore_patterns: List[str] = []
        if use_default_excludes:
            hard_excludes.extend(DEFAULT_EXCLUDE_DIRS)
            hard_excludes.extend(DEFAULT_EXCLUDE_GLOBS)
            ignore_patterns.extend(_load_gitignore_patterns(root_dir))
            repo_root = _get_repo_root(root_dir)
            if repo_root and repo_root != root_dir:
                ignore_patterns.extend(_load_gitignore_patterns(repo_root))

        apply_ignore = use_default_excludes and not include_patterns
        combined_excludes = hard_excludes + user_excludes
        if apply_ignore:
            combined_excludes += ignore_patterns

        exclude_dirs, exclude_globs = _classify_excludes(combined_excludes)
        no_ignore = not apply_ignore

        if action == "replace":
            if regex_enabled or not case_sensitive:
                self.set_status(400)
                self.finish(json.dumps({
                    "success": False,
                    "error": "Regex or case-insensitive replace is not supported yet."
                }))
                return
            if replace_text is None:
                self.set_status(400)
                self.finish(json.dumps({
                    "success": False,
                    "error": "Replace text is required."
                }))
                return

            grep_args = {
                "pattern": re.escape(query),
                "path": target_dir,
                "output_mode": "files_with_matches",
                "no_ignore": no_ignore,
                "glob": include_patterns,
                "exclude_dirs": exclude_dirs,
                "exclude": exclude_globs,
            }
            grep_result = await execute_grep_tool(grep_args)
            summary, files = _parse_files_response(grep_result)
            if not files and summary.startswith("Error"):
                self.set_status(500)
                self.finish(json.dumps({
                    "success": False,
                    "error": summary
                }))
                return

            replaced: List[Dict[str, Any]] = []
            errors: List[Dict[str, str]] = []
            total_replacements = 0

            for file_path in files:
                abs_path = file_path if os.path.isabs(file_path) else os.path.abspath(os.path.join(target_dir, file_path))
                if os.path.commonpath([root_dir, abs_path]) != root_dir:
                    errors.append({
                        "file": _to_display_path(file_path, root_dir),
                        "error": "Path is outside server root."
                    })
                    continue

                result = await edit_file_text(
                    file_path=abs_path,
                    old_string=query,
                    new_string=replace_text,
                    replace_all=True
                )

                if result.startswith("Success"):
                    count = _parse_replace_count(result)
                    total_replacements += count
                    replaced.append({
                        "file": _to_display_path(abs_path, root_dir),
                        "replacements": count
                    })
                else:
                    errors.append({
                        "file": _to_display_path(abs_path, root_dir),
                        "error": result
                    })

            self.finish(json.dumps({
                "success": True,
                "summary": summary or f"Updated {len(replaced)} file(s).",
                "totalFiles": len(files),
                "totalReplacements": total_replacements,
                "replaced": replaced,
                "errors": errors
            }))
            return

        limit_raw = payload.get("limit", DEFAULT_MATCH_LIMIT)
        try:
            limit = max(1, min(int(limit_raw), MAX_MATCH_LIMIT))
        except (TypeError, ValueError):
            limit = DEFAULT_MATCH_LIMIT

        pattern = query if regex_enabled else re.escape(query)
        grep_args = {
            "pattern": pattern,
            "path": target_dir,
            "output_mode": "content",
            "head_limit": limit,
            "no_ignore": no_ignore,
            "glob": include_patterns,
            "exclude_dirs": exclude_dirs,
            "exclude": exclude_globs,
        }
        if not case_sensitive:
            grep_args["i"] = True

        grep_result = await execute_grep_tool(grep_args)
        summary, matches, truncated = _parse_grep_response(grep_result)
        if not matches and summary.startswith("Error"):
            self.set_status(500)
            self.finish(json.dumps({
                "success": False,
                "error": summary
            }))
            return

        normalized_matches = []
        for match in matches:
            if not isinstance(match, dict):
                continue
            file_path = match.get("file", "")
            normalized_matches.append({
                "file": _to_display_path(file_path, root_dir),
                "line_number": match.get("line_number", 0),
                "content": match.get("content", "")
            })

        self.finish(json.dumps({
            "success": True,
            "summary": summary,
            "matches": normalized_matches,
            "truncated": truncated,
            "limit": limit
        }))
