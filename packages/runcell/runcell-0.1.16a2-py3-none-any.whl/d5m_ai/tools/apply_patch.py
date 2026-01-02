"""
Apply patch tool.

Applies unified diff/patch text to the local filesystem.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import shutil
from typing import Dict, Any, Optional


def _run_patch_command(patch_text: str, cwd: Optional[str] = None) -> str:
    if not patch_text or not patch_text.strip():
        return "Error: patch_text is required"

    patch_bin = shutil.which("patch")
    if not patch_bin:
        return "Error: 'patch' command not found on system"

    workdir = cwd or os.getcwd()

    # Write patch to a temp file to avoid shell quoting issues
    with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".patch") as tmp:
        tmp.write(patch_text)
        tmp_path = tmp.name

    # Try combinations: git-style then raw paths, with increasing fuzz
    attempts = [
        (1, 0),
        (1, 1),
        (1, 2),
        (0, 0),
        (0, 1),
        (0, 2),
    ]
    last_error: str | None = None
    chosen: Optional[tuple[int, int]] = None

    for strip, fuzz in attempts:
        try:
            dry_run = subprocess.run(
                [
                    patch_bin,
                    f"-p{strip}",
                    "-i",
                    tmp_path,
                    "-s",
                    "--dry-run",
                    "--no-backup-if-mismatch",
                    f"--fuzz={fuzz}",
                ],
                cwd=workdir,
                capture_output=True,
                text=True,
                timeout=30,
            )
        except subprocess.TimeoutExpired:
            last_error = "Error: patch command timed out during dry-run"
            continue
        except Exception as exc:
            last_error = f"Error: failed to run patch dry-run: {exc}"
            continue

        if dry_run.returncode == 0:
            chosen = (strip, fuzz)
            break

        stderr = dry_run.stderr.strip()
        stdout = dry_run.stdout.strip()
        details = stderr or stdout or f"exit code {dry_run.returncode}"
        last_error = f"Dry-run failed with -p{strip} --fuzz={fuzz}: {details}"

    if chosen is None:
        if os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
        return last_error or "Error applying patch: no matching strip level"

    chosen_strip, chosen_fuzz = chosen

    # Apply for real with the chosen strip level
    try:
        proc = subprocess.run(
            [
                patch_bin,
                f"-p{chosen_strip}",
                "-i",
                tmp_path,
                "-s",
                "--no-backup-if-mismatch",
                f"--fuzz={chosen_fuzz}",
            ],
            cwd=workdir,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        result = "Error: patch command timed out during apply"
    except Exception as exc:
        result = f"Error: failed to run patch: {exc}"
    else:
        if proc.returncode == 0:
            result = "Success: patch applied"
        else:
            stderr = proc.stderr.strip()
            stdout = proc.stdout.strip()
            details = stderr or stdout or f"exit code {proc.returncode}"
            result = f"Error applying patch with -p{chosen_strip} --fuzz={chosen_fuzz}: {details}"

    # Clean up temp file
    if os.path.exists(tmp_path):
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    return result


async def execute_apply_patch_tool(args: Dict[str, Any]) -> str:
    """
    Apply a unified diff patch to files.

    Args:
        args: Dict containing:
            - patch_text: required patch content
            - cwd: optional working directory for relative paths
    """
    patch_text = args.get("patch_text") or args.get("patch") or ""
    cwd = args.get("cwd")
    return _run_patch_command(patch_text, cwd)


async def apply_patch(patch_text: str, cwd: str | None = None) -> str:
    """Convenience wrapper for agent/proxy executors."""
    return _run_patch_command(patch_text, cwd)
