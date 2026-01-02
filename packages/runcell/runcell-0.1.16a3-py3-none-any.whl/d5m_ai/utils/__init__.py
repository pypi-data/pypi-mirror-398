"""
D5M AI Utilities Module

Common utilities shared across D5M AI components.
"""

import os


def get_remote_backend_url(service_type: str, use_ssl: bool = None) -> str:
    """
    Construct remote backend URL for different services from a single hostname.
    
    Args:
        service_type: One of 'agent', 'edit', 'chat'
        use_ssl: Whether to use SSL/TLS. If None, auto-detects based on hostname
        
    Returns:
        Complete URL for the specified service
    """
    # Get hostname from environment, default to localhost for development
    host = os.environ.get("D5M_REMOTE_HOST", "service.runcell.dev")
    
    # Auto-detect SSL based on hostname patterns
    if use_ssl is None:
        use_ssl = not (host.startswith("localhost") or host.startswith("127.0.0.1") or ":" in host.split(".")[0])
    
    # Determine protocol and construct base URL
    if service_type == "chat":
        protocol = "https" if use_ssl else "http"
        base_url = f"{protocol}://{host}"
        return f"{base_url}/chat"
    else:
        protocol = "wss" if use_ssl else "ws"
        base_url = f"{protocol}://{host}"
        return f"{base_url}/{service_type}"



def build_remote_backend_url(service_type: str) -> str:
    """    
    This function provides a migration path from multiple service-specific 
    environment variables to a single D5M_REMOTE_HOST variable.
    
    Args:
        service_type: One of 'agent', 'edit', 'chat'
        
    Returns:
        Complete URL for the specified service
    """
    
    return get_remote_backend_url(service_type) 