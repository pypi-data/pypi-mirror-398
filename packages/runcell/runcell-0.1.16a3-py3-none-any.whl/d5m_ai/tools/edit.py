"""
Exact string replacement tool.

Provides a simple helper to replace exact string matches in a file.
"""

from __future__ import annotations

import os
from typing import Dict, Any


def _replace_text_in_file(file_path: str, old_string: str, new_string: str, replace_all: bool = False) -> str:
    """
    Replace occurrences of old_string with new_string in the given file.
    """
    if not file_path:
        return "Error: file_path is required"

    # Support relative paths by resolving against the current working directory
    resolved_path = file_path if os.path.isabs(file_path) else os.path.abspath(file_path)

    if not old_string:
        return "Error: old_string is required"

    if new_string is None:
        return "Error: new_string is required"

    if not os.path.exists(resolved_path):
        return f"Error: File '{resolved_path}' does not exist"

    if not os.path.isfile(resolved_path):
        return f"Error: '{resolved_path}' is not a file"

    try:
        with open(resolved_path, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        return f"Error: File '{resolved_path}' is not a UTF-8 text file"
    except PermissionError:
        return f"Error: Permission denied reading file '{resolved_path}'"
    except Exception as read_err:
        return f"Error reading file '{resolved_path}': {read_err}"

    occurrences = content.count(old_string)
    if occurrences == 0:
        return f"Error: old_string not found in '{file_path}'"

    replacements = occurrences if replace_all else 1
    updated_content = content.replace(old_string, new_string, replacements)

    try:
        with open(resolved_path, "w", encoding="utf-8") as f:
            f.write(updated_content)
    except PermissionError:
        return f"Error: Permission denied writing to file '{resolved_path}'"
    except Exception as write_err:
        return f"Error writing file '{resolved_path}': {write_err}"

    return f"Success: replaced {replacements} occurrence(s) in '{resolved_path}'"


async def execute_edit_tool(args: Dict[str, Any]) -> str:
    """
    Execute edit tool using provided arguments.
    """
    file_path = args.get("file_path")
    old_string = args.get("old_string")
    new_string = args.get("new_string")
    replace_all_raw = args.get("replace_all", False)
    if isinstance(replace_all_raw, str):
        replace_all = replace_all_raw.lower() in {"1", "true", "yes", "y"}
    else:
        replace_all = bool(replace_all_raw)

    return _replace_text_in_file(
        file_path=file_path,
        old_string=old_string,
        new_string=new_string,
        replace_all=replace_all,
    )


async def edit_file_text(file_path: str, old_string: str, new_string: str, replace_all: bool = False) -> str:
    """
    Convenience wrapper for agent/local executors.
    """
    return _replace_text_in_file(
        file_path=file_path,
        old_string=old_string,
        new_string=new_string,
        replace_all=replace_all,
    )
