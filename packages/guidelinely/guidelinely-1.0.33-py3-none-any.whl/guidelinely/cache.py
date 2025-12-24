"""Client-side caching for Guidelinely API calculation endpoints.

Uses diskcache for persistent caching that survives between runs.

The cache directory can be configured via the GUIDELINELY_CACHE_DIR environment
variable. If not set, defaults to ~/.guidelinely_cache.

The cache TTL can be configured via the GUIDELINELY_CACHE_TTL environment
variable (in seconds). If not set, defaults to 7 days.
"""

import os
from pathlib import Path
from typing import Any, Optional, Union, cast

from diskcache import Cache  # type: ignore[import-untyped]

__all__ = ["get_cached", "set_cached", "cache", "CACHE_DIR", "DEFAULT_TTL"]

# Cache directory: configurable via environment variable, defaults to user's home directory
_default_cache_dir = Path.home() / ".guidelinely_cache"
CACHE_DIR = Path(os.getenv("GUIDELINELY_CACHE_DIR", str(_default_cache_dir)))
cache = Cache(directory=str(CACHE_DIR))

# Default TTL: 7 days in seconds, configurable via environment variable
DEFAULT_TTL = int(os.getenv("GUIDELINELY_CACHE_TTL", str(7 * 24 * 3600)))


def get_cached(
    key_data: Union[str, dict[str, Any], tuple[tuple[str, Any], ...]],
) -> Optional[dict[str, Any]]:
    """Retrieve cached response for given request data.

    Args:
        key_data: Cache key (string, dict of request parameters, or normalized tuple)

    Returns:
        Cached response data if found, None otherwise
    """
    result = cache.get(key_data)
    if result is None:
        return None
    return cast(dict[str, Any], result)


def set_cached(
    key_data: Union[str, dict[str, Any], tuple[tuple[str, Any], ...]],
    value: dict[str, Any],
    ttl: int = DEFAULT_TTL,
) -> None:
    """Store response in cache for given request data with TTL.

    Args:
        key_data: Cache key (string, dict of request parameters, or normalized tuple)
        value: Response data to cache
        ttl: Time to live in seconds. Defaults to DEFAULT_TTL (7 days),
            which can be configured via GUIDELINELY_CACHE_TTL environment variable.
    """
    cache.set(key_data, value, expire=ttl)
