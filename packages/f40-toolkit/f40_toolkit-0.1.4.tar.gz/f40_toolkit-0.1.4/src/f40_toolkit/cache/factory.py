from __future__ import annotations

from typing import Any, Dict, Mapping, Optional
import os
import pathlib

from .errors import CacheConfigurationError, CachePrefixError
from .manager import CacheManager
from .serializers import JsonSerializer  # , PickleSerializer
from .backends.file_backend import FileCacheBackend
from .backends.memory_backend import MemoryCacheBackend
from .backends.redis_backend import RedisCacheBackend
from .utils import build_cache_prefix_from_config


def _resolve_dir(p: Optional[str]) -> str:
    """
    Resolve cache directory from:

      1. explicit path in config (preferred)
      2. env F40_CACHE_DIR
      3. default ".cache"

    "~" and env vars are expanded. If still relative and F40_PROJECT_ROOT is set,
    path is anchored under that; otherwise under CWD.
    """
    raw = p or os.getenv("F40_CACHE_DIR") or ".cache"
    raw = os.path.expanduser(os.path.expandvars(raw))
    base = os.getenv("F40_PROJECT_ROOT")
    if base and not os.path.isabs(raw):
        raw = os.path.join(base, raw)
    return str(pathlib.Path(raw).resolve())


def create_cache_from_config(cfg: Mapping[str, Any]) -> CacheManager:
    """
    Create a CacheManager from a simple config dict.

    Expected shape:

        {
          "cache": {
            "backend": "file" | "memory" | "redis",
            "default_timeout": 300,
            "serializer": "json" | "pickle",
            "path": ".cache",

            "redis": {
              "url": "redis://localhost:6379/0",
              "prefix": "myapp:",
              # or host/port/db/password/etc...
            }
          }
        }
    """
    c: Dict[str, Any] = dict(cfg.get("cache", {}) or {})
    backend = (c.get("backend") or "file").lower()
    default_timeout = int(c.get("default_timeout", 300))
    serializer_name = (c.get("serializer") or "json").lower()

    # ---- serializer selection ----
    if serializer_name == "json":
        serializer = JsonSerializer()
    # elif serializer_name == "pickle":
    #     serializer = PickleSerializer()
    else:
        raise CacheConfigurationError(f"Unsupported serializer: {serializer_name!r}")

    # ---- backend selection ----
    if backend == "file":
        cache_dir = _resolve_dir(c.get("path"))
        b = FileCacheBackend(
            cache_dir=cache_dir,
            default_timeout=default_timeout,
            serializer=serializer,
        )

    elif backend == "memory":
        b = MemoryCacheBackend(default_timeout=default_timeout)

    elif backend == "redis":
        try:
            import redis  # type: ignore
        except Exception as e:
            raise CacheConfigurationError(
                "Redis backend requested but the 'redis' package is not installed.\n"
                "Install it with:\n"
                "  pip install f40-toolkit[cache-redis]\n"
                "or:\n"
                "  pip install redis"
            ) from e

        rcfg: Dict[str, Any] = dict(c.get("redis", {}) or {})

        explicit_prefix = rcfg.pop("prefix", None)
        url = rcfg.pop("url", None)
        client_kwargs = rcfg

        if url:
            try:
                client = redis.Redis.from_url(url, **client_kwargs)
            except Exception as e:
                raise CacheConfigurationError(
                    "Failed to create Redis client from cache.redis.url.\n"
                    f"URL: {url!r}"
                ) from e
        else:
            try:
                client = redis.Redis(**client_kwargs)
            except Exception as e:
                raise CacheConfigurationError(
                    "Failed to create Redis client from 'cache.redis' config.\n"
                    "Provide either 'cache.redis.url' or host/port/db/password/etc."
                ) from e

        if explicit_prefix:
            prefix = explicit_prefix
        else:
            try:
                prefix = build_cache_prefix_from_config(dict(cfg), kind="cache")
            except CachePrefixError as e:
                raise CacheConfigurationError(
                    "Cache prefix could not be computed for Redis backend. "
                    "Either configure env/service/customer in config, or set "
                    "'cache.redis.prefix' explicitly.\n"
                    f"Details: {e}"
                ) from e

        b = RedisCacheBackend(
            client,
            prefix=prefix,
            default_timeout=default_timeout,
            serializer=serializer,
        )

    else:
        raise CacheConfigurationError(f"Unsupported cache backend: {backend!r}")

    return CacheManager(backend=b, default_timeout=default_timeout)
