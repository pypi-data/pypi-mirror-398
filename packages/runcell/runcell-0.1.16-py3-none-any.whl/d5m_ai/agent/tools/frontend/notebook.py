"""
Notebook operation tools - rerun_all_cells, open_tab.

These tools require frontend/JupyterLab interaction via WebSocket.
"""

from .helpers import send_and_wait, request_permission_and_execute


async def rerun_all_cells(handler) -> str:
    """
    Rerun all cells in the current notebook via WebSocket.
    
    This operation requires user permission since it can overwrite existing outputs.
    
    Args:
        handler: The WebSocket handler instance.
    
    Returns:
        Result of the rerun operation, or cancellation/error message.
    """
    return await request_permission_and_execute(
        handler,
        permission_message_type="rerun_all_cells_permission_request",
        permission_message="Rerun all cells will execute all cells from top to bottom and may overwrite existing outputs. Do you want to proceed?",
        execute_message_type="rerun_all_cells",
        execute_payload={},
        permission_timeout=120.0,
        execute_timeout=120.0,
        cancelled_message="Rerun all cells cancelled by user. This operation can overwrite existing cell outputs.",
        permission_timeout_message="Rerun all cells timed out waiting for user permission.",
    )


async def open_tab(handler, file_path: str) -> str:
    """
    Open a file in a JupyterLab tab via WebSocket.
    
    Args:
        handler: The WebSocket handler instance.
        file_path: Path to the file to open.
    
    Returns:
        Result of the open operation.
    """
    return await send_and_wait(
        handler,
        message_type="open_tab",
        payload={"file_path": file_path},
        timeout=15.0,
        error_message="Error: No result received from open tab (timeout)",
    )

async def run_long_terminal(handler, command: str, error_detection_window_ms: int | None = 3000) -> str:
    return await send_and_wait(
        handler,
        message_type="run_long_terminal",
        payload={"command": command, "error_detection_window_ms": error_detection_window_ms},
        timeout=15.0,
        error_message="Start a new terminal in jupyter failed(timeout)"
    )
