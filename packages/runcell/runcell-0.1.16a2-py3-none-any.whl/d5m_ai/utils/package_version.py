"""Utilities for retrieving package versions from the running kernel."""

from __future__ import annotations

from importlib import metadata

__all__ = ["get_packages_version"]

def get_packages_version(limit: int = 50) -> str:
    """Return a list of installed packages with their versions.

    Parameters
    ----------
    limit:
        Limit the number of packages returned. Use ``0`` or ``None`` for no
        limit.
    """

    try:
        packages = {dist.metadata["Name"]: dist.version for dist in metadata.distributions()}
        sorted_packages = sorted(packages.items())
        if limit:
            sorted_packages = sorted_packages[:limit]
        version_info = "\n".join(f"{name}: {version}" for name, version in sorted_packages)
        return version_info or "No packages detected"
    except Exception as e:  # pragma: no cover - defensive
        return f"Error getting package versions: {str(e)}"
