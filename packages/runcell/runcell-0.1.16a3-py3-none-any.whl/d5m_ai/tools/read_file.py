"""
Standalone Read File Tool

A lightweight file reading implementation that provides controlled access to file contents.
Supports reading full files or specific line ranges with proper error handling.
"""

import os
import logging
from typing import Dict, Any, Optional


async def execute_read_file_tool(args: Dict[str, Any]) -> str:
    """
    Execute the read_file tool to read file contents.
    
    Args:
        args: Dictionary containing:
            - file_path: Path to the file to read (required)
            - start_row_index: Starting line index (default: 0)
            - end_row_index: Ending line index (default: 200)
    
    Returns:
        Formatted string with file contents or error message
    """
    file_path = args.get('file_path')
    start_row_index = int(args.get('start_row_index', 0) or 0)
    end_row_index = int(args.get('end_row_index', 200) or 200)

    if not file_path:
        return "Error: 'file_path' is required for read_file tool"

    try:
        if not os.path.exists(file_path):
            return f"Error: File '{file_path}' does not exist"

        if not os.path.isfile(file_path):
            return f"Error: '{file_path}' is not a file"

        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        if not lines:
            return f"File: {file_path}\nFile is empty."

        # Normalize indices
        if start_row_index < 0:
            start_row_index = 0
        if end_row_index < start_row_index:
            end_row_index = start_row_index
        if end_row_index >= len(lines):
            end_row_index = len(lines) - 1 if lines else 0

        selected_lines = lines[start_row_index:end_row_index + 1]
        content = ''.join(selected_lines)

        return (
            f"File: {file_path}\n"
            f"Rows {start_row_index}-{end_row_index}:\n"
            f"{content}"
        )
    except UnicodeDecodeError:
        logging.error(f"[READ-FILE] Unicode decode error for file: {file_path}")
        return f"Error reading file '{file_path}': File contains non-UTF-8 characters or is binary"
    except PermissionError:
        logging.error(f"[READ-FILE] Permission denied for file: {file_path}")
        return f"Error reading file '{file_path}': Permission denied"
    except Exception as e:
        logging.error(f"[READ-FILE] Error executing read_file tool: {e}")
        return f"Error reading file '{file_path}': {str(e)}"

