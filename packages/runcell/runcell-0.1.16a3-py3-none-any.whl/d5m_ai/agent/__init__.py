"""
D5M AI Agent Module

This module provides AI agent functionality for JupyterLab environments using
the proxy handler architecture. The proxy handler forwards requests to the 
remote backend server for AI processing.
"""

# Primary proxy handler (used by extension)
from .proxy_handler import AIJLAgentProxyHandler

# Internal infrastructure (used by proxy handler and direct handler)
from .config import handler_registry, IMAGE_DIR, IMAGE_BASE_URL
from .image_processor import ImageProcessor
from .websocket_tool_executor import WebSocketToolExecutor

# Tool execution components
from .tools.local.shell import ShellExecutor, PermissionHandler

__all__ = [
    # Primary proxy handler
    'AIJLAgentProxyHandler',
    
    # Configuration
    'handler_registry',
    'IMAGE_DIR', 
    'IMAGE_BASE_URL',
    
    # Infrastructure modules
    'ImageProcessor',
    'WebSocketToolExecutor',

    # Shell execution
    'ShellExecutor',
    'PermissionHandler'
]
