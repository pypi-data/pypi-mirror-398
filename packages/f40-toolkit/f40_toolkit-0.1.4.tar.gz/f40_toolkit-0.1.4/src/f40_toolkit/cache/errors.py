from __future__ import annotations


class CacheError(Exception):
    """Base exception for cache-related issues."""


class CacheConfigurationError(CacheError):
    """Misconfiguration of cache backends / options."""


class CachePrefixError(CacheError):
    """Failure to derive a safe cache key prefix from config."""


class InvalidCacheValue(CacheError, KeyError):
    """
    Raised when a cache key is missing or value cannot be used.
    Kept compatible with KeyError semantics where useful.
    """
