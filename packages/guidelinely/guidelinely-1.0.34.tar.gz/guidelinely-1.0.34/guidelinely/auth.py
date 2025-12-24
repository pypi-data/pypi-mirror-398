"""Authentication helpers for the Guidelinely API.

The main API endpoints (metadata) do not require authentication.
Calculation endpoints optionally accept an API key.
"""

import os
from typing import Optional

__all__ = ["get_api_key", "get_api_base"]

# Default API base URL
DEFAULT_API_BASE = "https://guidelines.1681248.com/api/v1"


def get_api_key(api_key: Optional[str] = None) -> Optional[str]:
    """Get API key from argument or GUIDELINELY_API_KEY environment variable.

    Args:
        api_key: Optional API key string. If not provided, will check environment.

    Returns:
        API key string or None if not available.
    """
    if api_key is not None:
        return api_key

    env_key = os.getenv("GUIDELINELY_API_KEY")
    if env_key:
        return env_key

    return None


def get_api_base(api_base: Optional[str] = None) -> str:
    """Get API base URL from argument or GUIDELINELY_API_BASE environment variable.

    Args:
        api_base: Optional API base URL string. If not provided, will check environment.

    Returns:
        API base URL string (defaults to production URL if not provided).
    """
    if api_base is not None:
        return api_base

    env_base = os.getenv("GUIDELINELY_API_BASE")
    if env_base:
        return env_base

    return DEFAULT_API_BASE
