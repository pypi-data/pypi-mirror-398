"""
Quick Fix proxy handler module.

Provides a proxy API that forwards quick fix requests to the remote backend.
"""

from .quick_fix_handler import QuickFixApplyHandler

__all__ = ["QuickFixApplyHandler"]
