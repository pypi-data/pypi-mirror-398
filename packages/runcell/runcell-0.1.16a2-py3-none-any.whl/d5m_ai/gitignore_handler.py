import asyncio
import json
import os
from jupyter_server.base.handlers import APIHandler
import tornado.web


async def _get_repo_root(root_dir: str):
    try:
        process = await asyncio.create_subprocess_exec(
            "git",
            "rev-parse",
            "--show-toplevel",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=root_dir,
        )
    except Exception:
        return None

    stdout, _stderr = await process.communicate()
    if process.returncode != 0:
        return None

    output = stdout.decode("utf-8", errors="replace").strip()
    return output or None


def _normalize_rel_path(path: str) -> str:
    return path.replace(os.sep, "/").lstrip("./")


class GitIgnoreHandler(APIHandler):
    @tornado.web.authenticated
    async def get(self):
        root_dir = getattr(self.contents_manager, "root_dir", None)
        if not root_dir:
            root_dir = (
                self.settings.get("server_root_dir")
                or self.settings.get("root_dir")
                or os.getcwd()
            )

        dir_arg = self.get_argument("dir", default="", strip=True)
        if dir_arg in ("", ".", "/"):
            target_dir = root_dir
        else:
            dir_arg = dir_arg.lstrip("/").lstrip("\\")
            target_dir = os.path.abspath(os.path.join(root_dir, dir_arg))

        root_dir = os.path.abspath(root_dir)
        try:
            if os.path.commonpath([root_dir, target_dir]) != root_dir:
                raise ValueError("Path is outside server root.")
        except ValueError:
            self.set_status(400)
            self.finish(json.dumps({
                "success": False,
                "error": "Invalid directory path."
            }))
            return

        gitignore_path = os.path.join(target_dir, ".gitignore")
        root_content = None
        root_prefix = None
        is_root_request = dir_arg in ("", ".", "/")

        if is_root_request:
            repo_root = await _get_repo_root(root_dir)
            if repo_root:
                repo_root = os.path.abspath(repo_root)
                if repo_root != root_dir:
                    try:
                        rel_from_repo = os.path.relpath(root_dir, repo_root)
                    except ValueError:
                        rel_from_repo = None
                    if rel_from_repo and not rel_from_repo.startswith(".."):
                        rel_from_repo = _normalize_rel_path(rel_from_repo)
                        root_gitignore_path = os.path.join(repo_root, ".gitignore")
                        if os.path.isfile(root_gitignore_path):
                            try:
                                with open(root_gitignore_path, "r", encoding="utf-8") as handle:
                                    root_content = handle.read()
                                root_prefix = rel_from_repo or None
                            except Exception:
                                root_content = None
                                root_prefix = None

        if not os.path.isfile(gitignore_path):
            payload = {
                "success": True,
                "found": False
            }
            if root_content:
                payload["root_content"] = root_content
                if root_prefix:
                    payload["root_prefix"] = root_prefix
            self.finish(json.dumps(payload))
            return

        try:
            with open(gitignore_path, "r", encoding="utf-8") as handle:
                content = handle.read()
            payload = {
                "success": True,
                "found": True,
                "content": content,
                "dir": dir_arg
            }
            if root_content:
                payload["root_content"] = root_content
                if root_prefix:
                    payload["root_prefix"] = root_prefix
            self.finish(json.dumps(payload))
        except Exception as exc:
            self.set_status(500)
            self.finish(json.dumps({
                "success": False,
                "error": str(exc)
            }))
