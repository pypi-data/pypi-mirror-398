"""
Title generation module.

This module provides title generation functionality using the proxy handler architecture.
The proxy handler forwards requests to the remote backend server for AI processing.
"""

from .title_handler import TitleGenerationHandler

__all__ = ['TitleGenerationHandler']