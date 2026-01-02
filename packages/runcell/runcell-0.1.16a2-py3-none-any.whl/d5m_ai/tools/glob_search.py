"""
Standalone Glob Search Tool

Find files by glob pattern, sorted by modification time (newest first).
"""

import glob
import os
from typing import Any, Dict, List, Union


def _safe_get_mtime(path: str) -> float:
    """Return modification time for sorting, or 0 on failure."""
    try:
        return os.path.getmtime(path)
    except OSError:
        return 0.0


async def execute_glob_tool(args: Dict[str, Any]) -> Union[List[str], str]:
    """
    Execute glob search.

    Args:
        args: Dictionary containing:
            - pattern: Glob pattern (required), e.g., "**/*.py"
            - path: Base directory to search (optional, defaults to ".")

    Returns:
        List of matching file paths sorted by modification time (newest first),
        or an error message string.
    """
    pattern = args.get("pattern")
    base_path = args.get("path") or "."

    if not pattern or not isinstance(pattern, str):
        return "Error: 'pattern' is required for glob tool"

    try:
        if not os.path.exists(base_path):
            return f"Error: Path '{base_path}' does not exist"
        if not os.path.isdir(base_path):
            return f"Error: '{base_path}' is not a directory"

        # Build a full pattern rooted at base_path unless an absolute pattern is provided
        search_pattern = pattern if os.path.isabs(pattern) else os.path.join(base_path, pattern)

        # Use recursive glob to support ** patterns
        matches = glob.glob(search_pattern, recursive=True)

        # Filter to files only and sort by mtime (newest first)
        file_matches = [path for path in matches if os.path.isfile(path)]
        file_matches = sorted(set(file_matches), key=_safe_get_mtime, reverse=True)

        return file_matches
    except Exception as e:
        return f"Error executing glob search: {str(e)}"
