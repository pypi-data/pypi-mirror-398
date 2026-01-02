"""
Cell operation tools - cell_execute, edit_cell, edit_markdown_cell, insert_markdown_cell.

These tools require frontend/JupyterLab interaction via WebSocket.
"""

from typing import Optional

from .helpers import send_and_wait


async def cell_execute(
    handler,
    code: str,
    file_path: Optional[str] = None,
    insert_position: Optional[int] = None,
) -> str:
    """
    Execute Python code in a notebook cell via WebSocket.
    
    Args:
        handler: The WebSocket handler instance.
        code: Python code to execute.
        file_path: Target notebook path (optional).
        insert_position: Optional position to insert a new cell.
    
    Returns:
        Execution result from the kernel.
    """
    return await send_and_wait(
        handler,
        message_type="cell_execute",
        payload={
            "code": code,
            "file_path": file_path,
            "insert_position": insert_position,
        },
        timeout=90.0,
        error_message="Error: No result received from code execution (timeout)",
    )


async def edit_cell(
    handler,
    cell_index: int,
    code: str,
    file_path: str,
    rerun: bool = False,
) -> str:
    """
    Edit a cell's content via WebSocket.
    
    Args:
        handler: The WebSocket handler instance.
        cell_index: Index of the cell to edit (0-based).
        code: New code content for the cell.
        file_path: Path to the notebook file.
        rerun: Whether to rerun the cell after editing.
    
    Returns:
        Result of the edit operation.
    """
    return await send_and_wait(
        handler,
        message_type="edit_cell",
        payload={
            "cell_index": cell_index,
            "code": code,
            "file_path": file_path,
            "rerun": rerun,
        },
        timeout=90.0,
        error_message="Error: No result received from cell edit (timeout)",
    )


async def edit_markdown_cell(
    handler,
    file_path: str,
    cell_index: int,
    content: str,
    render: bool = True,
) -> str:
    """
    Edit a markdown cell's content via WebSocket.
    
    Args:
        handler: The WebSocket handler instance.
        file_path: Path to the notebook file.
        cell_index: Index of the markdown cell to edit (0-based).
        content: New markdown content for the cell.
        render: Whether to render the markdown after editing.
    
    Returns:
        Result of the edit operation.
    """
    return await send_and_wait(
        handler,
        message_type="edit_markdown_cell",
        payload={
            "file_path": file_path,
            "cell_index": cell_index,
            "content": content,
            "render": render,
        },
        timeout=60.0,
        error_message="Error: No result received from edit markdown cell (timeout)",
    )


async def insert_markdown_cell(
    handler,
    content: str,
    file_path: str,
    insert_position: Optional[int] = None,
) -> str:
    """
    Insert a new markdown cell via WebSocket.
    
    Args:
        handler: The WebSocket handler instance.
        content: Markdown content for the new cell.
        file_path: Path to the notebook file.
        insert_position: Optional position to insert the cell.
    
    Returns:
        Result of the insert operation.
    """
    return await send_and_wait(
        handler,
        message_type="insert_markdown_cell",
        payload={
            "content": content,
            "file_path": file_path,
            "insert_position": insert_position,
        },
        timeout=30.0,
        error_message="Error: No result received from insert markdown cell (timeout)",
    )


async def insert_cell(
    handler,
    code: str,
    file_path: str,
    insert_position: Optional[int] = None,
) -> str:
    """
    Insert a new code cell via WebSocket without executing it.
    
    Args:
        handler: The WebSocket handler instance.
        code: Code content for the new cell.
        file_path: Path to the notebook file.
        insert_position: Optional position to insert the cell.
    
    Returns:
        Result of the insert operation.
    """
    return await send_and_wait(
        handler,
        message_type="insert_cell",
        payload={
            "code": code,
            "file_path": file_path,
            "insert_position": insert_position,
        },
        timeout=30.0,
        error_message="Error: No result received from insert cell (timeout)",
    )


async def run_cell(
    handler,
    file_path: str,
    cell_index: Optional[int] = None,
) -> str:
    """
    Run an existing cell by index via WebSocket.
    
    Args:
        handler: The WebSocket handler instance.
        file_path: Path to the notebook file.
        cell_index: Index of the cell to run.
    
    Returns:
        Execution result from the kernel.
    """
    return await send_and_wait(
        handler,
        message_type="run_cell",
        payload={
            "file_path": file_path,
            "cell_index": cell_index,
        },
        timeout=90.0,
        error_message="Error: No result received from run cell (timeout)",
    )


async def delete_cell(
    handler,
    file_path: str,
    cell_index: Optional[int] = None,
) -> str:
    """
    Delete a cell by index via WebSocket.
    
    Args:
        handler: The WebSocket handler instance.
        file_path: Path to the notebook file.
        cell_index: Index of the cell to delete.
    
    Returns:
        Result of the delete operation.
    """
    return await send_and_wait(
        handler,
        message_type="delete_cell",
        payload={
            "file_path": file_path,
            "cell_index": cell_index,
        },
        timeout=30.0,
        error_message="Error: No result received from delete cell (timeout)",
    )
