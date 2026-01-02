"""
Search tools - list_dir, grep.

These tools execute locally on the proxy server without frontend interaction.
They reuse implementations from the shared ask-mode tools package.
"""

import json
from typing import Any, Dict, Optional

from d5m_ai.tools import execute_list_dir_tool, execute_grep_tool, execute_glob_tool


async def list_dir(dir_path: str = ".") -> str:
    """
    List directory contents.
    
    Args:
        dir_path: Path to the directory to list. Defaults to current directory.
    
    Returns:
        JSON string with directory contents, or error message.
    """
    try:
        result = await execute_list_dir_tool({"dir": dir_path})
        return json.dumps(result)
    except Exception as e:
        return json.dumps([
            {"name": f"Error listing directory '{dir_path}': {str(e)}", "type": "error"}
        ])


async def grep(
    pattern: str,
    path: str = ".",
    i: bool = False,
    A: Optional[int] = None,
    B: Optional[int] = None,
    C: Optional[int] = None,
    output_mode: str = "content",
    glob: Optional[str] = None,
    file_type: Optional[str] = None,
    head_limit: Optional[int] = None,
    multiline: bool = False,
) -> str:
    """
    Search for patterns in files using grep.
    
    Args:
        pattern: Regular expression pattern to search for.
        path: Path to search in. Defaults to current directory.
        i: Case insensitive search.
        A: Number of lines to show after each match.
        B: Number of lines to show before each match.
        C: Number of lines to show before and after each match.
        output_mode: Output format - "content", "files_with_matches", or "count".
        glob: Glob pattern to filter files.
        file_type: File type to search (e.g., "py", "js").
        head_limit: Limit output to first N results.
        multiline: Enable multiline matching.
    
    Returns:
        Search results as string.
    """
    args: Dict[str, Any] = {
        "pattern": pattern,
        "path": path,
        "output_mode": output_mode,
        "multiline": multiline,
    }

    if i:
        args["i"] = True
    if A is not None:
        args["A"] = A
    if B is not None:
        args["B"] = B
    if C is not None:
        args["C"] = C
    if glob:
        args["glob"] = glob
    if file_type:
        args["type"] = file_type
    if head_limit is not None:
        args["head_limit"] = head_limit

    return await execute_grep_tool(args)


async def glob(
    pattern: str,
    path: str = ".",
) -> str:
    """
    Find files matching a glob pattern, sorted by modification time (newest first).
    """
    try:
        result = await execute_glob_tool({"pattern": pattern, "path": path})
        if isinstance(result, list):
            return json.dumps(result)
        return result
    except Exception as e:
        return json.dumps([f"Error executing glob search: {str(e)}"])
