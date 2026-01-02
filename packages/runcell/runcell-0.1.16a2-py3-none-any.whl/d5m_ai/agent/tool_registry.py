"""
Central registry for agent-mode tools.

Each tool is annotated with where it should execute:
- frontend: requires browser/JupyterLab interaction
- proxy: can execute on the proxy server locally
- remote: handled entirely by remote backend (should not reach proxy)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class AgentToolMeta:
    name: str
    location: str  # "frontend", "proxy", or "remote"
    executor: Optional[str] = (
        None  # method name on WebSocketToolExecutor for proxy tools
    )
    message_type: Optional[str] = None  # frontend message type override
    timeout_on_pending: bool = False  # whether to start agent-mode timeout watchdog
    frontend_error: Optional[str] = None  # error message when no frontend is available
    requires_permission: bool = False  # whether to run via permission helper
    permission_executor: Optional[str] = None  # executor to use for permission flow


AGENT_TOOL_REGISTRY: Dict[str, AgentToolMeta] = {
    # Frontend-interactive tools
    "cell_execute": AgentToolMeta(
        name="cell_execute",
        location="frontend",
        message_type="cell_execute",
        timeout_on_pending=True,
        frontend_error="Error: cell_execute requires a connected frontend with a Jupyter kernel. In agent mode, please use shell_execute for command-line operations instead.",
    ),
    "edit_cell": AgentToolMeta(
        name="edit_cell",
        location="frontend",
        message_type="edit_cell",
        frontend_error="Error: edit_cell requires a connected frontend with a Jupyter notebook.",
    ),
    "edit_markdown_cell": AgentToolMeta(
        name="edit_markdown_cell",
        location="frontend",
        message_type="edit_markdown_cell",
        frontend_error="Error: edit_markdown_cell requires a connected frontend with a Jupyter notebook.",
    ),
    "insert_markdown_cell": AgentToolMeta(
        name="insert_markdown_cell",
        location="frontend",
        message_type="insert_markdown_cell",
        frontend_error="Error: insert_markdown_cell requires a connected frontend with a Jupyter notebook.",
    ),
    "rerun_all_cells": AgentToolMeta(
        name="rerun_all_cells",
        location="frontend",
        requires_permission=True,
        permission_executor="rerun_all_cells",
    ),
    "open_tab": AgentToolMeta(
        name="open_tab",
        location="frontend",
        message_type="open_tab",
        frontend_error="Error: open_tab requires a connected frontend with a Jupyter notebook.",
    ),
    "insert_cell": AgentToolMeta(
        name="insert_cell",
        location="frontend",
        message_type="insert_cell",
        frontend_error="Error: insert_cell requires a connected frontend with a Jupyter notebook.",
    ),
    "run_cell": AgentToolMeta(
        name="run_cell",
        location="frontend",
        message_type="run_cell",
        frontend_error="Error: run_cell requires a connected frontend with a Jupyter notebook.",
    ),
    "delete_cell": AgentToolMeta(
        name="delete_cell",
        location="frontend",
        message_type="delete_cell",
        frontend_error="Error: delete_cell requires a connected frontend with a Jupyter notebook.",
    ),
    # Proxy-local tools
    "shell_execute": AgentToolMeta(
        name="shell_execute",
        location="proxy",
        executor="shell_execute",
    ),
    "run_long_terminal": AgentToolMeta(
        name="run_long_terminal",
        location="frontend",
        message_type="run_long_terminal",
        frontend_error="Error: run_long_terminal requires a connected frontend.",
    ),
    "read_file": AgentToolMeta(
        name="read_file",
        location="proxy",
        executor="read_file",
    ),
    "write_file": AgentToolMeta(
        name="write_file",
        location="proxy",
        executor="write_file",
    ),
    "edit": AgentToolMeta(
        name="edit",
        location="proxy",
        executor="edit",
    ),
    # TEMPORARILY DISABLED: apply_patch tool
    # "apply_patch": AgentToolMeta(
    #     name="apply_patch",
    #     location="proxy",
    #     executor="apply_patch",
    # ),
    "glob": AgentToolMeta(
        name="glob",
        location="proxy",
        executor="glob",
    ),
    "list_dir": AgentToolMeta(
        name="list_dir",
        location="proxy",
        executor="list_dir",
    ),
    "grep": AgentToolMeta(
        name="grep",
        location="proxy",
        executor="grep",
    ),
    "create_notebook": AgentToolMeta(
        name="create_notebook",
        location="proxy",
        executor="create_notebook",
    ),
    # Remote-only tools (should not be forwarded to proxy)
    "interpret_image": AgentToolMeta(
        name="interpret_image",
        location="remote",
    ),
    "web_search": AgentToolMeta(
        name="web_search",
        location="remote",
    ),
}


def get_tool_meta(tool_name: str) -> Optional[AgentToolMeta]:
    """Return tool metadata if registered."""
    return AGENT_TOOL_REGISTRY.get(tool_name)
