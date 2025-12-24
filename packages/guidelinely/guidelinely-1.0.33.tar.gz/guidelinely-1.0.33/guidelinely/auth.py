"""Authentication helpers for the Guidelinely API.

The main API endpoints (metadata) do not require authentication.
Calculation endpoints optionally accept an API key.
"""

import os
from typing import Optional

__all__ = ["get_api_key"]


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
