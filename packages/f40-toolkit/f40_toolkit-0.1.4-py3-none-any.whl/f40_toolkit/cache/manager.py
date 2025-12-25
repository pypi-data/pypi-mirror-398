from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from .interfaces import CacheBackend
from .errors import CacheConfigurationError, InvalidCacheValue

try:
    from .observability import log_get, log_set, log_del
except Exception:  # pragma: no cover

    def log_get(key: str, hit: bool) -> None: ...
    def log_set(key: str, ttl: Optional[int]) -> None: ...
    def log_del(key: str) -> None: ...


class CacheManager:
    """
    Thin facade over a backend. Adds:
      - default timeout
      - get_or_set helper
      - observability logging (GET/SET/DEL)

    All cache misses from .get() raise InvalidCacheValue.
    """

    def __init__(self, backend: CacheBackend, default_timeout: int = 300):
        if backend is None:
            raise CacheConfigurationError(
                "CacheManager initialized with backend=None. "
                "Check your cache configuration and create_cache_from_config()."
            )
        self.backend = backend
        self.default_timeout = default_timeout

    def get(self, key: str) -> Any:
        try:
            value = self.backend.get(key)
            log_get(key, hit=True)
            return value
        except KeyError as e:
            log_get(key, hit=False)
            raise InvalidCacheValue(str(e))

    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> None:
        ttl = self.default_timeout if timeout is None else timeout
        log_set(key, ttl)
        self.backend.set(key, value, ttl)

    def invalidate(self, key: str) -> None:
        log_del(key)
        self.backend.invalidate(key)

    def clear(self) -> None:
        self.backend.clear()

    def get_or_set(
        self,
        key: str,
        func: Callable[..., Any],
        f_args: Optional[List[Any]] = None,
        f_kwa: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,
        default: Any = None,
        use_default_instead_of_compute: bool = False,
    ) -> Any:
        f_args = f_args or []
        f_kwa = f_kwa or {}
        try:
            return self.get(key)
        except InvalidCacheValue:
            if use_default_instead_of_compute and default is not None:
                return default
            result = func(*f_args, **f_kwa)
            self.set(key, result, timeout)
            return result
