from __future__ import annotations

from typing import Any
import logging

from .manager import CacheManager

try:
    # If user configures f40_toolkit.logging, this will give us a nicer channel.
    from f40_toolkit.logging import get_logger

    cache_log = get_logger("cache", channel="default")
    health_log = get_logger("cache.health", channel="default")
except Exception:  # pragma: no cover
    cache_log = logging.getLogger("f40.cache")
    health_log = logging.getLogger("f40.cache.health")


def log_get(key: str, hit: bool) -> None:
    cache_log.debug("GET %s hit=%s", key, hit)


def log_set(key: str, ttl: int | None) -> None:
    cache_log.debug("SET %s ttl=%s", key, ttl)


def log_del(key: str) -> None:
    cache_log.debug("DEL %s", key)


def check_cache_health(
    cache: CacheManager, *, key: str = "__health__", timeout: int = 5
) -> bool:
    """
    Simple healthcheck for the cache subsystem.

    Returns True if everything works, False otherwise.
    """
    try:
        sentinel_value = "ok"
        cache.set(key, sentinel_value, timeout)
        value: Any = cache.get(key)
        if value != sentinel_value:
            health_log.warning(
                "Cache healthcheck mismatch: %r != %r", value, sentinel_value
            )
            return False
        try:
            cache.invalidate(key)
        except Exception:
            pass
        return True
    except Exception as e:
        health_log.warning("Cache healthcheck failed: %s", e)
        return False
