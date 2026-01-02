import os
import json
import fnmatch
from pathlib import Path
from typing import List, Dict, Any, Optional
from jupyter_server.base.handlers import APIHandler
import tornado.web


class MentionFileHandler(APIHandler):
    """Handler for getting files and folders for mention functionality."""

    @tornado.web.authenticated
    async def get(self):
        """Get files and folders under current directory."""
        try:
            # Get query parameters
            match_string = self.get_argument('match', default='', strip=True)
            current_dir = self.get_argument('dir', default='.', strip=True)
            recursive = self.get_argument('recursive', default='true', strip=True).lower() == 'true'
            max_depth = int(self.get_argument('max_depth', default='3', strip=True))
            
            # Resolve the directory path
            if not os.path.isabs(current_dir):
                current_dir = os.path.abspath(current_dir)
            
            if not os.path.exists(current_dir) or not os.path.isdir(current_dir):
                self.set_status(400)
                self.finish(json.dumps({
                    "success": False,
                    "error": f"Directory does not exist: {current_dir}"
                }))
                return
            
            # Get gitignore patterns
            gitignore_patterns = self._load_gitignore_patterns(current_dir)
            
            # Get file list
            if recursive:
                file_list = self._get_file_list_recursive(current_dir, match_string, gitignore_patterns, max_depth)
            else:
                file_list = self._get_file_list(current_dir, match_string, gitignore_patterns)
            
            self.finish(json.dumps({
                "success": True,
                "files": file_list,
                "directory": current_dir,
                "recursive": recursive
            }))
            
        except Exception as e:
            self.set_status(500)
            self.finish(json.dumps({
                "success": False,
                "error": str(e)
            }))

    def _load_gitignore_patterns(self, directory: str) -> List[str]:
        """Load gitignore patterns from .gitignore file."""
        patterns = []
        gitignore_path = os.path.join(directory, '.gitignore')
        
        if os.path.exists(gitignore_path):
            try:
                with open(gitignore_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        # Skip empty lines and comments
                        if line and not line.startswith('#'):
                            patterns.append(line)
            except Exception as e:
                print(f"Warning: Could not read .gitignore file: {e}")
        
        # Add common patterns to ignore
        default_patterns = [
            '__pycache__',
            '*.pyc',
            '.git',
            '.DS_Store',
            'node_modules',
            '.ipynb_checkpoints',
            '.venv',
            'venv',
            '.env',
            '*.log',
            '.pytest_cache',
            '__pycache__/',
            '.git/',
            'node_modules/',
            '.ipynb_checkpoints/'
        ]
        patterns.extend(default_patterns)
        
        return patterns

    def _is_ignored(self, path: str, patterns: List[str], base_dir: str = None) -> bool:
        """Check if a path should be ignored based on gitignore patterns."""
        path_obj = Path(path)
        
        # Get relative path from base directory if provided
        if base_dir:
            try:
                rel_path = os.path.relpath(path, base_dir)
            except ValueError:
                rel_path = str(path_obj)
        else:
            rel_path = str(path_obj)
        
        for pattern in patterns:
            # Handle directory patterns (ending with /)
            if pattern.endswith('/'):
                pattern = pattern[:-1]
                if path_obj.is_dir():
                    # Check against directory name
                    if fnmatch.fnmatch(path_obj.name, pattern):
                        return True
                    # Check against relative path
                    if fnmatch.fnmatch(rel_path, pattern):
                        return True
            else:
                # Check against filename
                if fnmatch.fnmatch(path_obj.name, pattern):
                    return True
                # Check against relative path
                if fnmatch.fnmatch(rel_path, pattern):
                    return True
                # Check if any parent directory matches the pattern
                for parent in path_obj.parents:
                    if fnmatch.fnmatch(parent.name, pattern):
                        return True
        
        return False

    def _get_file_extension(self, filename: str) -> Optional[str]:
        """Get file extension without the dot."""
        if '.' in filename:
            return filename.split('.')[-1].lower()
        return None

    def _get_file_list_recursive(self, directory: str, match_string: str, gitignore_patterns: List[str], max_depth: int = 3) -> List[Dict[str, Any]]:
        """Get list of files and folders matching the criteria recursively."""
        file_list = []
        
        def _walk_directory(current_dir: str, current_depth: int = 0):
            if current_depth > max_depth:
                return
                
            try:
                for item in os.listdir(current_dir):
                    item_path = os.path.join(current_dir, item)
                    
                    # Skip if ignored by gitignore
                    if self._is_ignored(item_path, gitignore_patterns, directory):
                        continue
                    
                    # Determine type
                    is_dir = os.path.isdir(item_path)
                    
                    # For match filtering, check if the item name matches
                    matches_search = True
                    if match_string:
                        matches_search = match_string.lower() in item.lower()
                    
                    # Add to results if it matches the search
                    if matches_search:
                        file_type = 'folder' if is_dir else 'file'
                        
                        # Get extension for files
                        extension = None if is_dir else self._get_file_extension(item)
                        
                        # Get relative path from base directory
                        rel_path = os.path.relpath(item_path, directory)
                        
                        file_info = {
                            'type': file_type,
                            'name': item,
                            'path': os.path.abspath(item_path),
                            'relative_path': rel_path,
                            'depth': current_depth
                        }
                        
                        if extension:
                            file_info['extension'] = extension
                        
                        file_list.append(file_info)
                    
                    # Recursively search subdirectories
                    if is_dir and current_depth < max_depth:
                        _walk_directory(item_path, current_depth + 1)
            
            except PermissionError:
                # Skip directories we don't have permission to read
                pass
            except Exception as e:
                print(f"Warning: Error reading directory {current_dir}: {e}")
        
        _walk_directory(directory)
        
        # Sort: by depth first (shallower first), then folders before files, then alphabetically
        file_list.sort(key=lambda x: (x['depth'], x['type'] == 'file', x['relative_path'].lower()))
        
        # Limit results to prevent overwhelming the UI
        max_results = 100
        if len(file_list) > max_results:
            file_list = file_list[:max_results]
        
        return file_list

    def _get_file_list(self, directory: str, match_string: str, gitignore_patterns: List[str]) -> List[Dict[str, Any]]:
        """Get list of files and folders matching the criteria (non-recursive)."""
        file_list = []
        
        try:
            for item in os.listdir(directory):
                item_path = os.path.join(directory, item)
                
                # Skip if ignored by gitignore
                if self._is_ignored(item_path, gitignore_patterns, directory):
                    continue
                
                # Skip if match_string is provided and doesn't match
                if match_string and match_string.lower() not in item.lower():
                    continue
                
                # Determine type
                is_dir = os.path.isdir(item_path)
                file_type = 'folder' if is_dir else 'file'
                
                # Get extension for files
                extension = None if is_dir else self._get_file_extension(item)
                
                file_info = {
                    'type': file_type,
                    'name': item,
                    'path': os.path.abspath(item_path),
                    'relative_path': item,
                    'depth': 0
                }
                
                if extension:
                    file_info['extension'] = extension
                
                file_list.append(file_info)
        
        except PermissionError:
            # Skip directories we don't have permission to read
            pass
        except Exception as e:
            print(f"Warning: Error reading directory {directory}: {e}")
        
        # Sort: folders first, then files, both alphabetically
        file_list.sort(key=lambda x: (x['type'] == 'file', x['name'].lower()))
        
        return file_list
