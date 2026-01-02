"""
Configuration for D5M AI Edit Module

Environment variables and settings for the edit proxy architecture.
"""

import os

# Development/production mode
D5M_ENV = os.environ.get("D5M_ENV", "production")

# Remote backend configuration is now handled by utils.build_remote_backend_url()
# using the D5M_REMOTE_HOST environment variable 