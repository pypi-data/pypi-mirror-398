"""
File operation tools - read_file, write_file, edit.

These tools execute locally on the proxy server without frontend interaction.
"""

import os
from typing import Tuple

from d5m_ai.tools import edit_file_text, apply_patch as apply_patch_tool


async def read_file(file_path: str, start_row_index: int = 0, end_row_index: int = 200) -> str:
    """
    Read content from a file with optional row range specification.
    
    Args:
        file_path: Path to the file to read.
        start_row_index: Starting line index (0-based, inclusive).
        end_row_index: Ending line index (0-based, inclusive). Use -1 for end of file.
    
    Returns:
        File content with metadata header, or error message.
    """
    try:
        if not file_path:
            return "Error: file_path is required"
            
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
                
            total_lines = len(lines)
            
            # Handle negative end_row_index (read to end of file).
            if end_row_index == -1:
                end_row_index = total_lines - 1
                
            # Validate row indices.
            start_row_index = max(0, start_row_index)
            end_row_index = min(end_row_index, total_lines - 1)
            
            if start_row_index > end_row_index:
                return f"Error: start_row_index ({start_row_index}) is greater than end_row_index ({end_row_index})"
            elif start_row_index >= total_lines:
                return f"Error: start_row_index ({start_row_index}) is beyond file length ({total_lines} lines)"
            else:
                # Extract the specified range of lines.
                selected_lines = lines[start_row_index:end_row_index + 1]
                content = ''.join(selected_lines)
                
                # Add metadata about the file and range.
                metadata = f"File: {file_path}\n"
                metadata += f"Total lines: {total_lines}\n"
                metadata += f"Showing lines {start_row_index + 1}-{min(end_row_index + 1, total_lines)} (1-indexed)\n"
                metadata += "=" * 50 + "\n"
                
                return metadata + content
                
        except FileNotFoundError:
            return f"Error: File '{file_path}' not found"
        except PermissionError:
            return f"Error: Permission denied reading file '{file_path}'"
        except UnicodeDecodeError:
            return f"Error: File '{file_path}' contains binary data or unsupported encoding"
        except Exception as read_error:
            return f"Error reading file '{file_path}': {str(read_error)}"
            
    except Exception as e:
        return f"Error in read_file tool: {str(e)}"


async def write_file(file_path: str, content: str) -> str:
    """
    Write content to a file, creating it if it doesn't exist or overwriting if it does.
    
    Args:
        file_path: Path to the file to write.
        content: Content to write to the file.
    
    Returns:
        Success message with file info, or error message.
    """
    try:
        if not file_path:
            return "Error: file_path is required"
        
        if content is None:
            return "Error: content is required"
        
        # Ensure parent directory exists.
        parent_dir = os.path.dirname(file_path)
        if parent_dir and not os.path.exists(parent_dir):
            try:
                os.makedirs(parent_dir, exist_ok=True)
            except Exception as dir_error:
                return f"Error: Failed to create parent directory '{parent_dir}': {str(dir_error)}"
        
        # Write content to file (create or overwrite).
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(content)
            
            # Return success message with file info.
            file_size = len(content)
            lines_count = len(content.splitlines())
            file_existed = os.path.exists(file_path)
            action = "Updated" if file_existed else "Created"
            
            return f"{action} file: {file_path}\nLines written: {lines_count}\nBytes written: {file_size}"
            
        except PermissionError:
            return f"Error: Permission denied writing to file '{file_path}'"
        except IsADirectoryError:
            return f"Error: '{file_path}' is a directory, not a file"
        except Exception as write_error:
            return f"Error writing to file '{file_path}': {str(write_error)}"
            
    except Exception as e:
        return f"Error in write_file tool: {str(e)}"


async def edit(
    file_path: str,
    old_string: str,
    new_string: str,
    replace_all: bool = False,
) -> str:
    """
    Make exact string replacements in a file.
    """
    try:
        return await edit_file_text(
            file_path=file_path,
            old_string=old_string,
            new_string=new_string,
            replace_all=replace_all,
        )
    except Exception as e:
        return f"Error in edit tool: {str(e)}"


async def apply_patch(patch_text: str, cwd: str | None = None) -> str:
    """
    Apply unified diff patch text to files.
    """
    try:
        return await apply_patch_tool(patch_text=patch_text, cwd=cwd)
    except Exception as e:
        return f"Error in apply_patch tool: {str(e)}"


async def create_notebook(file_path: str) -> str:
    """
    Create an empty Jupyter notebook (.ipynb) file at the specified path.
    
    Args:
        file_path: Path where the notebook should be created. Should end with .ipynb
    
    Returns:
        Success message with file info, or error message.
    """
    import json
    
    try:
        if not file_path:
            return "Error: file_path is required"
        
        # Ensure the file has .ipynb extension.
        if not file_path.endswith('.ipynb'):
            file_path = file_path + '.ipynb'
        
        # Check if file already exists.
        if os.path.exists(file_path):
            return f"Error: Notebook '{file_path}' already exists. Use a different path or delete the existing file first."
        
        # Ensure parent directory exists.
        parent_dir = os.path.dirname(file_path)
        if parent_dir and not os.path.exists(parent_dir):
            try:
                os.makedirs(parent_dir, exist_ok=True)
            except Exception as dir_error:
                return f"Error: Failed to create parent directory '{parent_dir}': {str(dir_error)}"
        
        # Create empty notebook structure with minimal metadata.
        # Jupyter will populate kernelspec and language_info when the notebook
        # is opened and a kernel is attached, so we only include required fields.
        empty_notebook = {
            "cells": [],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 5
        }
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(empty_notebook, f, indent=1)
            
            return f"Created notebook: {file_path}\nThe notebook is empty and ready for use."
            
        except PermissionError:
            return f"Error: Permission denied creating notebook '{file_path}'"
        except IsADirectoryError:
            return f"Error: '{file_path}' is a directory, not a file"
        except Exception as write_error:
            return f"Error creating notebook '{file_path}': {str(write_error)}"
            
    except Exception as e:
        return f"Error in create_notebook tool: {str(e)}"
