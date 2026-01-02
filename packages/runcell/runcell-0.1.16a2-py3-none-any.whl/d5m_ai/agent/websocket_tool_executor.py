"""
Tool executor that delegates to specialized tool modules.

This module provides the WebSocketToolExecutor class that bridges the tool registry
with actual tool implementations organized by location (local vs frontend).
"""

import asyncio
import uuid
from typing import Optional

from .tools.local import file_ops, search
from .tools.local.shell import ShellExecutor, PermissionHandler
from .tools.frontend import cell_ops, notebook


class WebSocketToolExecutor:
    """
    Tool executor implementation that bridges to WebSocket handler.
    
    This class delegates to specialized tool modules:
    - Local tools (file_ops, search, shell): Execute on proxy server
    - Frontend tools (cell_ops, notebook): Require browser interaction
    """
    
    def __init__(self, handler):
        self.handler = handler
        # Create shell executor with permission handler.
        self.shell_executor = ShellExecutor(WebSocketPermissionHandler(handler))
    
    # =========================================================================
    # Local tools - execute on proxy server
    # =========================================================================
    
    async def read_file(self, file_path: str, start_row_index: int = 0, end_row_index: int = 200) -> str:
        """Read content from a file with optional row range."""
        return await file_ops.read_file(file_path, start_row_index, end_row_index)
    
    async def write_file(self, file_path: str, content: str) -> str:
        """Write content to a file, creating or overwriting it."""
        return await file_ops.write_file(file_path, content)
    
    async def edit(
        self,
        file_path: str,
        old_string: str,
        new_string: str,
        replace_all: bool = False,
    ) -> str:
        """Make exact string replacements in a file."""
        return await file_ops.edit(
            file_path=file_path,
            old_string=old_string,
            new_string=new_string,
            replace_all=replace_all,
        )
    
    async def apply_patch(self, patch_text: str, cwd: str | None = None) -> str:
        """Apply unified diff patch text."""
        return await file_ops.apply_patch(patch_text=patch_text, cwd=cwd)
    
    async def create_notebook(self, file_path: str) -> str:
        """Create an empty Jupyter notebook (.ipynb) file."""
        return await file_ops.create_notebook(file_path)
    
    async def list_dir(self, dir_path: str = ".") -> str:
        """List directory contents."""
        return await search.list_dir(dir_path)
    
    async def glob(
        self,
        pattern: str,
        path: str = ".",
    ) -> str:
        """Find files by glob pattern, sorted by modification time."""
        return await search.glob(pattern=pattern, path=path)
    
    async def grep(
        self,
        pattern: str,
        path: str = ".",
        i: bool = False,
        A: Optional[int] = None,
        B: Optional[int] = None,
        C: Optional[int] = None,
        output_mode: str = "content",
        glob: Optional[str] = None,
        type: Optional[str] = None,
        head_limit: Optional[int] = None,
        multiline: bool = False,
    ) -> str:
        """Search for patterns in files."""
        return await search.grep(
            pattern=pattern,
            path=path,
            i=i,
            A=A,
            B=B,
            C=C,
            output_mode=output_mode,
            glob=glob,
            file_type=type,
            head_limit=head_limit,
            multiline=multiline,
        )
    
    async def shell_execute(self, command: str) -> str:
        """Execute shell command via shell executor."""
        return await self.shell_executor.execute_command(command)
    
    # =========================================================================
    # Frontend tools - require browser/JupyterLab interaction
    # =========================================================================
    async def run_long_terminal(self, command: str, error_detection_window_ms: int | None = 3000, request_id: Optional[str] = None) -> str:
        return await notebook.run_long_terminal(self.handler, command, error_detection_window_ms)
    
    async def cell_execute(
        self,
        code: str,
        file_path: Optional[str] = None,
        insert_position: Optional[int] = None,
    ) -> str:
        """Execute code in a cell via WebSocket."""
        return await cell_ops.cell_execute(self.handler, code, file_path=file_path, insert_position=insert_position)
    
    async def edit_cell(
        self,
        cell_index: int,
        code: str,
        file_path: str,
        rerun: bool = False,
        request_id: Optional[str] = None,
    ) -> str:
        """Edit a cell via WebSocket."""
        return await cell_ops.edit_cell(self.handler, cell_index, code, file_path, rerun)

    async def edit_markdown_cell(
        self,
        file_path: str,
        cell_index: int,
        content: str,
        render: bool = True,
        request_id: Optional[str] = None,
    ) -> str:
        """Edit a markdown cell via WebSocket."""
        return await cell_ops.edit_markdown_cell(self.handler, file_path, cell_index, content, render)

    async def insert_markdown_cell(
        self,
        content: str,
        file_path: str,
        insert_position: Optional[int] = None,
        request_id: Optional[str] = None,
    ) -> str:
        """Insert a markdown cell via WebSocket."""
        return await cell_ops.insert_markdown_cell(self.handler, content, file_path, insert_position)
    
    async def rerun_all_cells(self, request_id: Optional[str] = None) -> str:
        """Rerun all cells via WebSocket with permission check."""
        return await notebook.rerun_all_cells(self.handler)
    
    async def open_tab(self, file_path: str, request_id: Optional[str] = None) -> str:
        """Open a file in a JupyterLab tab via WebSocket."""
        return await notebook.open_tab(self.handler, file_path)
    
    async def insert_cell(
        self,
        code: str,
        file_path: str,
        insert_position: Optional[int] = None,
        request_id: Optional[str] = None,
    ) -> str:
        """Insert a code cell without executing via WebSocket."""
        return await cell_ops.insert_cell(self.handler, code, file_path, insert_position)
    
    async def run_cell(
        self,
        file_path: str,
        cell_index: Optional[int] = None,
        request_id: Optional[str] = None,
    ) -> str:
        """Run a cell by index via WebSocket."""
        return await cell_ops.run_cell(self.handler, file_path, cell_index)
    
    async def delete_cell(
        self,
        file_path: str,
        cell_index: Optional[int] = None,
        request_id: Optional[str] = None,
    ) -> str:
        """Delete a cell by index via WebSocket."""
        return await cell_ops.delete_cell(self.handler, file_path, cell_index)

    # =========================================================================
    # Remote tools - should be handled by remote backend, not local executor
    # =========================================================================

    async def interpret_image(self, image_url: str) -> str:
        """Interpret an image using a vision-capable LLM."""
        return "Error: interpret_image tool should be handled by the remote backend, not the local executor"


class WebSocketPermissionHandler(PermissionHandler):
    """Permission handler that uses WebSocket to request user permissions."""
    
    def __init__(self, handler):
        self.handler = handler
    
    async def request_permission(self, command: str, dangerous_pattern: str) -> bool:
        """Request permission via WebSocket."""
        request_id = str(uuid.uuid4())
        
        # Create a waiter for the permission response.
        permission_waiter = asyncio.get_running_loop().create_future()
        
        # Store the waiter temporarily.
        original_waiter = self.handler.waiter
        self.handler.waiter = permission_waiter
        
        try:
            # Send permission request to frontend.
            await self.handler._safe_write_message({
                "type": "shell_permission_request",
                "command": command,
                "dangerous_pattern": dangerous_pattern,
                "request_id": request_id,
                "connection_id": self.handler.connection_id,
            })
            
            # Wait for user response (with timeout).
            try:
                permission_response = await asyncio.wait_for(permission_waiter, timeout=60.0)
                return permission_response and permission_response.get("allowed") == True
            except asyncio.TimeoutError:
                # Send timeout notification to frontend.
                await self.handler._safe_write_message({
                    "type": "shell_permission_timeout",
                    "request_id": request_id,
                    "command": command,
                    "connection_id": self.handler.connection_id,
                })
                return False
        finally:
            # Restore original waiter.
            self.handler.waiter = original_waiter
