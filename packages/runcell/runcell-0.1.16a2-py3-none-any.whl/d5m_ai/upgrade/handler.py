import asyncio
import json
import logging
import os
import subprocess
import sys
from importlib import metadata
from typing import Any, Dict, Optional

import tornado.web
from jupyter_server.base.handlers import APIHandler


PACKAGE_NAME = "runcell"
UPGRADE_TIMEOUT_SECONDS = 300  # 5 minutes timeout for pip install

logger = logging.getLogger(__name__)


def _detect_environment() -> Dict[str, Any]:
    """Collect information about the Python environment running Jupyter."""
    prefix = sys.prefix
    python_executable = sys.executable

    pip_path: Optional[str] = None
    for candidate in (
        os.path.join(os.path.dirname(python_executable), "pip"),
        os.path.join(os.path.dirname(python_executable), "pip3"),
    ):
        if os.path.exists(candidate):
            pip_path = candidate
            break

    pip_command = pip_path or f"{python_executable} -m pip"

    try:
        current_version = metadata.version(PACKAGE_NAME)
    except metadata.PackageNotFoundError:
        current_version = "unknown"

    site_packages: Optional[str] = None
    try:
        import site

        site_packages = next(iter(site.getsitepackages() or []), None)
    except Exception:
        site_packages = None

    install_writable = False
    for path in filter(None, (site_packages, prefix, os.path.dirname(python_executable))):
        if os.access(path, os.W_OK):
            install_writable = True
            break

    is_conda = os.path.exists(os.path.join(prefix, "conda-meta"))
    is_venv = hasattr(sys, "real_prefix") or (hasattr(sys, "base_prefix") and sys.base_prefix != prefix)

    def _is_homebrew_path(path: str) -> bool:
        lower_path = path.lower()
        return "/homebrew/" in lower_path or "/opt/homebrew/" in lower_path

    is_homebrew = _is_homebrew_path(python_executable) or _is_homebrew_path(sys.prefix)

    return {
        "python_executable": python_executable,
        "python_version": sys.version,
        "prefix": prefix,
        "pip_command": pip_command,
        "current_version": current_version,
        "is_conda": is_conda,
        "is_venv": is_venv,
        "is_homebrew": is_homebrew,
        "site_packages": site_packages,
        "install_writable": install_writable,
    }


class UpgradeEnvironmentHandler(APIHandler):
    """Return environment details for safe upgrades."""

    @tornado.web.authenticated
    async def get(self):
        try:
            env_info = _detect_environment()
            self.finish(json.dumps({"success": True, "environment": env_info}))
        except Exception as exc:  # pragma: no cover - defensive
            self.set_status(500)
            self.finish(json.dumps({"success": False, "error": str(exc)}))


class UpgradeHandler(APIHandler):
    """Run pip upgrade using the Python environment powering Jupyter."""

    @tornado.web.authenticated
    async def post(self):
        body = self.get_json_body() or {}
        package_name = body.get("package_name", PACKAGE_NAME)
        dry_run = bool(body.get("dry_run")) or os.environ.get("D5M_UPGRADE_DRY_RUN") == "1"
        allow_pre = bool(body.get("pre", False))
        env_info = _detect_environment()

        if env_info.get("is_homebrew"):
            self.finish(
                json.dumps(
                    {
                        "success": False,
                        "error": "Jupyter appears to be running from a Homebrew environment. Please upgrade using Homebrew.",
                        "environment": env_info,
                        "needs_brew": True,
                        "dry_run": dry_run,
                    }
                )
            )
            return

        command = [sys.executable, "-m", "pip", "install", "--upgrade", "--no-cache-dir"]
        if allow_pre:
            command.append("--pre")
        command.append(package_name)

        if dry_run:
            self.finish(
                json.dumps(
                    {
                        "success": True,
                        "returncode": 0,
                        "stdout": "[dry-run] Would run: " + " ".join(command),
                        "stderr": "",
                        "command": " ".join(command),
                        "environment": env_info,
                        "dry_run": True,
                    }
                )
            )
            return

        try:
            # Use subprocess.run in a thread pool for better Windows compatibility
            # asyncio.create_subprocess_exec can have issues on Windows
            loop = asyncio.get_event_loop()
            
            # On Windows, avoid creating a console window
            # CREATE_NO_WINDOW = 0x08000000
            extra_kwargs = {}
            if sys.platform == "win32":
                extra_kwargs["creationflags"] = 0x08000000  # CREATE_NO_WINDOW
            
            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    command,
                    capture_output=True,
                    timeout=UPGRADE_TIMEOUT_SECONDS,
                    **extra_kwargs,
                )
            )

            stdout = result.stdout.decode("utf-8", errors="replace")
            stderr = result.stderr.decode("utf-8", errors="replace")

            self.finish(
                json.dumps(
                    {
                        "success": result.returncode == 0,
                        "returncode": result.returncode,
                        "stdout": stdout,
                        "stderr": stderr,
                        "command": " ".join(command),
                        "environment": env_info,
                        "dry_run": False,
                    }
                )
            )
        except subprocess.TimeoutExpired as exc:
            logger.error(f"Upgrade command timed out after {UPGRADE_TIMEOUT_SECONDS}s: {command}")
            self.set_status(500)
            self.finish(
                json.dumps(
                    {
                        "success": False,
                        "error": f"Upgrade timed out after {UPGRADE_TIMEOUT_SECONDS} seconds. The pip install may still be running in the background.",
                        "command": " ".join(command),
                        "environment": env_info,
                        "dry_run": False,
                    }
                )
            )
        except Exception as exc:  # pragma: no cover - defensive
            # Capture detailed error info for debugging
            error_type = type(exc).__name__
            error_msg = str(exc) or repr(exc)
            full_error = f"{error_type}: {error_msg}" if error_msg else error_type
            logger.error(f"Upgrade failed with {error_type}: {error_msg}", exc_info=True)
            
            self.set_status(500)
            self.finish(
                json.dumps(
                    {
                        "success": False,
                        "error": full_error,
                        "command": " ".join(command),
                        "environment": env_info,
                        "dry_run": False,
                    }
                )
            )
