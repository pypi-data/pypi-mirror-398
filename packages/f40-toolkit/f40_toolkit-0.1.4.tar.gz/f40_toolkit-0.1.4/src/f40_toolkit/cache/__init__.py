from __future__ import annotations

from .errors import (
    CacheError,
    CacheConfigurationError,
    CachePrefixError,
    InvalidCacheValue,
)
from .interfaces import CacheBackend, Serializer
from .serializers import JsonSerializer#, PickleSerializer
from .manager import CacheManager
from .factory import create_cache_from_config
from .utils import build_cache_prefix_from_config
from .keys import KeyBuilder, default_builder
from .observability import check_cache_health
from .backends.file_backend import FileCacheBackend
from .backends.memory_backend import MemoryCacheBackend
from .backends.redis_backend import RedisCacheBackend

__all__ = [
    # errors
    "CacheError",
    "CacheConfigurationError",
    "CachePrefixError",
    "InvalidCacheValue",
    # core interfaces / manager
    "CacheBackend",
    "Serializer",
    "CacheManager",
    # serializers
    "JsonSerializer",
    # "PickleSerializer",
    # factory & utils
    "create_cache_from_config",
    "build_cache_prefix_from_config",
    # key building
    "KeyBuilder",
    "default_builder",
    # backends
    "FileCacheBackend",
    "MemoryCacheBackend",
    "RedisCacheBackend",
    # observability
    "check_cache_health",
]
