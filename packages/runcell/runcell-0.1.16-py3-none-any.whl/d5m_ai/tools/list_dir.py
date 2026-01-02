"""
Standalone List Directory Tool

A lightweight directory listing implementation that provides directory contents.
Returns file and folder information with proper error handling.
"""

import os
import logging
from typing import Dict, Any, List


async def execute_list_dir_tool(args: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Execute the list_dir tool to list directory contents.
    
    Args:
        args: Dictionary containing:
            - dir: Path to the directory to list (optional, defaults to current working directory)
    
    Returns:
        List of dictionaries with 'name' and 'type' fields, or error dict
    """
    dir_path = args.get('dir', '.')
    
    # Handle empty string as current directory
    if not dir_path or dir_path.strip() == '':
        dir_path = '.'

    try:
        if not os.path.exists(dir_path):
            logging.error(f"[LIST-DIR] Directory does not exist: {dir_path}")
            return [{"name": f"Error: Directory '{dir_path}' does not exist", "type": "error"}]

        if not os.path.isdir(dir_path):
            logging.error(f"[LIST-DIR] Path is not a directory: {dir_path}")
            return [{"name": f"Error: '{dir_path}' is not a directory", "type": "error"}]

        # List directory contents
        entries = []
        
        try:
            items = os.listdir(dir_path)
        except PermissionError:
            logging.error(f"[LIST-DIR] Permission denied: {dir_path}")
            return [{"name": f"Error: Permission denied for directory '{dir_path}'", "type": "error"}]
        
        # Sort items: directories first, then files, both alphabetically
        dirs = []
        files = []
        
        for item in items:
            item_path = os.path.join(dir_path, item)
            try:
                if os.path.isdir(item_path):
                    dirs.append(item)
                else:
                    files.append(item)
            except (OSError, PermissionError):
                # Skip items we can't access
                continue
        
        # Sort both lists
        dirs.sort()
        files.sort()
        
        # Normalize directory path for display
        display_dir = dir_path if dir_path != '.' else ''
        
        # Build result list with full paths
        for dir_name in dirs:
            full_path = os.path.join(display_dir, dir_name) if display_dir else dir_name
            entries.append({
                "name": full_path,
                "type": "folder"
            })
        
        for file_name in files:
            full_path = os.path.join(display_dir, file_name) if display_dir else file_name
            entries.append({
                "name": full_path,
                "type": "file"
            })
        
        if not entries:
            return [{"name": "Directory is empty", "type": "info"}]
        
        return entries
        
    except Exception as e:
        logging.error(f"[LIST-DIR] Error executing list_dir tool: {e}")
        return [{"name": f"Error listing directory '{dir_path}': {str(e)}", "type": "error"}]

