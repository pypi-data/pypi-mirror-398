"""
Chat module initialization.

This module provides AI chat functionality using the proxy handler architecture.
The proxy handler forwards requests to the remote backend server for AI processing.
"""

from .chat_proxy_handler import AIChatProxyHandler as AIChatHandler

__all__ = ['AIChatHandler'] 