"""
Registry for ask-mode proxy tools.

ARCHITECTURE NOTE - Ask Mode Tool Execution:
============================================
Ask mode has a 3-layer architecture:

    Browser Frontend  -->  Proxy (JupyterLab extension)  -->  Remote Backend (d5m_ai_server)
         |                        |                                   |
    (displays UI)         (executes local tools)            (AI completion + web_search)

Tool execution flow:
1. Frontend sends chat request to Proxy (chat_proxy_handler.py)
2. Proxy forwards to Remote Backend for AI completion
3. When AI calls a tool, Remote Backend returns 'pending_tool' event
4. Proxy intercepts 'pending_tool', executes tool LOCALLY on user's machine
5. Proxy sends tool results back to Remote Backend to continue conversation
6. Frontend receives streamed response (tool outputs + AI continuation)

Why tools run on the PROXY (not browser frontend):
- read_file, list_dir, grep, glob: Need access to user's local filesystem
- edit, apply_patch: Need to modify files on user's machine (currently disabled)
- web_search: Runs on Remote Backend (not here) because it needs API keys

IMPORTANT: The browser frontend correctly ignores 'pending_tool' events in chat.ts.
This is NOT a bug - the Proxy handles tool execution, not the frontend.
The comment "Proxy handles tool execution" in chat.ts is accurate.
"""

from __future__ import annotations

import json
from typing import Any, Awaitable, Callable, Dict, Optional, Tuple

from .read_file import execute_read_file_tool
from .list_dir import execute_list_dir_tool
from .grep import execute_grep_tool
# TEMPORARILY DISABLED: edit and apply_patch tools - may re-enable in future
# from .edit import execute_edit_tool
# from .apply_patch import execute_apply_patch_tool
from .glob_search import execute_glob_tool


ToolExecutor = Callable[[Dict[str, Any]], Awaitable[Any]]
PostProcessor = Callable[[Any], Tuple[str, Any]]


def _default_postprocess(result: Any) -> Tuple[str, Any]:
    return str(result), result


def _list_dir_postprocess(result: Any) -> Tuple[str, Any]:
    """Return JSON string for LLM, structured list for SSE."""
    try:
        return json.dumps(result), result
    except Exception:
        return str(result), result


def _grep_postprocess(result: Any) -> Tuple[str, Any]:
    """
    Grep already returns JSON string; keep it for LLM, try to parse for SSE.
    """
    llm_output = result if isinstance(result, str) else str(result)
    try:
        sse_output = json.loads(llm_output)
    except Exception:
        sse_output = llm_output
    return llm_output, sse_output


def _glob_postprocess(result: Any) -> Tuple[str, Any]:
    """
    Return JSON string for LLM and structured list for SSE.
    """
    if isinstance(result, list):
        try:
            return json.dumps(result), result
        except Exception:
            pass
    return str(result), result


ASK_TOOL_REGISTRY: Dict[str, Tuple[ToolExecutor, PostProcessor]] = {
    "read_file": (execute_read_file_tool, _default_postprocess),
    "list_dir": (execute_list_dir_tool, _list_dir_postprocess),
    "grep": (execute_grep_tool, _grep_postprocess),
    # TEMPORARILY DISABLED: edit and apply_patch tools - may re-enable in future
    # "edit": (execute_edit_tool, _default_postprocess),
    # "apply_patch": (execute_apply_patch_tool, _default_postprocess),
    "glob": (execute_glob_tool, _glob_postprocess),
}


async def run_ask_tool(tool_name: str, args: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Execute a registered ask-mode tool.

    Returns:
        dict with llm_output (str) and sse_output (Any) or None if unsupported.
    """
    entry = ASK_TOOL_REGISTRY.get(tool_name)
    if not entry:
        return None

    executor, postprocess = entry
    raw_result = await executor(args)
    llm_output, sse_output = postprocess(raw_result)

    return {
        "llm_output": llm_output,
        "sse_output": sse_output,
    }
