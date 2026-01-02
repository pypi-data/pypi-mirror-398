"""
Edit module initialization.

This module provides AI edit functionality using the proxy handler architecture.
The proxy handler forwards requests to the remote backend server for AI processing.
"""

from .edit_proxy_handler import AIEditChatProxyHandler as AIEditChatHandler

__all__ = ['AIEditChatHandler'] 