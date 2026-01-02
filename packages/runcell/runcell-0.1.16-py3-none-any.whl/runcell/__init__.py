"""
RunCell - A JupyterLab extension for AI-powered coding assistance.

This is a wrapper module that re-exports everything from d5m_ai
to maintain compatibility with the new package name "runcell".
"""

# Import and re-export everything from d5m_ai
from d5m_ai import *
from d5m_ai import (
    __version__,
    _jupyter_server_extension_points,
    _jupyter_labextension_paths, 
    _jupyter_server_extension_paths,
    load_jupyter_server_extension
)

# Maintain the same interface
__all__ = [
    '__version__',
    '_jupyter_server_extension_points',
    '_jupyter_labextension_paths',
    '_jupyter_server_extension_paths', 
    'load_jupyter_server_extension'
] 