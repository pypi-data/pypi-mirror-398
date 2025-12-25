from __future__ import annotations

from typing import Any, Optional, TYPE_CHECKING

from f40_toolkit.cache.interfaces import CacheBackend, Serializer
from f40_toolkit.cache.errors import CacheConfigurationError

if TYPE_CHECKING:  # for type checkers only
    import redis  # type: ignore[import]


class RedisCacheBackend(CacheBackend):
    """
    Simple Redis-backed cache.

    - Keys are namespaced with a prefix.
    - Values are serialized via a Serializer.
    """

    def __init__(
        self,
        client: "redis.Redis",
        *,
        prefix: str = "f40:",
        default_timeout: int = 300,
        serializer: Serializer,
        test_connection: bool = True,
    ) -> None:
        self._r = client
        self._prefix = prefix if prefix.endswith(":") else prefix + ":"
        self.default_timeout = default_timeout
        self.serializer = serializer

        if test_connection:
            self._test_connection()

    # ---- connection test / ping ----
    def _test_connection(self) -> None:
        """
        Internal connectivity/config check.

        Called from __init__ (by default) so misconfig (e.g. wrong DB index)
        blows up early as a CacheConfigurationError instead of surfacing later.
        """
        try:
            from redis.exceptions import RedisError, ResponseError  # type: ignore[import]
        except Exception:  # pragma: no cover - very defensive
            # If redis isn't available here, something is very wrong anyway.
            RedisError = Exception  # type: ignore[assignment]

            class ResponseError(Exception):  # type: ignore[no-redef]
                pass

        try:
            self._r.ping()
        except ResponseError as e:  # type: ignore[name-defined]
            msg = str(e)
            if "DB index is out of range" in msg or "invalid DB index" in msg:
                raise CacheConfigurationError(
                    "Redis backend misconfigured: invalid DB index.\n"
                    "Your connection is selecting a database index that this "
                    "Redis instance does not support (many managed/clustered "
                    "caches only support database 0).\n"
                    "Fix your configuration by using DB 0, e.g.:\n"
                    "  - rediss://:<KEY>@host:6380/0\n"
                    "  - or set cache.redis.db = 0"
                ) from e
            raise CacheConfigurationError(
                f"Redis backend ping failed with ResponseError: {msg}"
            ) from e
        except RedisError as e:  # type: ignore[name-defined]
            raise CacheConfigurationError(f"Redis backend ping failed: {e}") from e

    def ping(self) -> bool:
        """
        Optional public ping you can reuse from healthchecks if you want.
        Raises CacheConfigurationError on config issues.
        """
        self._test_connection()
        return True

    # ---- helpers ----
    def _k(self, key: str) -> str:
        return f"{self._prefix}{key}"

    # ---- backend API ----
    def get(self, key: str) -> Any:
        raw = self._r.get(self._k(key))
        if raw is None:
            raise KeyError(key)
        return self.serializer.loads(raw)

    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> None:
        ttl = self.default_timeout if timeout is None else timeout
        payload = self.serializer.dumps(value)  # bytes

        if ttl is None or ttl <= 0:
            self._r.set(self._k(key), payload)
        else:
            self._r.setex(self._k(key), ttl, payload)

    def invalidate(self, key: str) -> None:
        self._r.delete(self._k(key))

    def clear(self) -> None:
        """
        Remove all keys with the configured prefix.

        Note: uses SCAN to avoid blocking Redis. Be careful with very large
        keyspaces, but for typical cache-sized usage this is fine.
        """
        pattern = self._k("*")
        cursor: int = 0
        while True:
            cursor, keys = self._r.scan(cursor=cursor, match=pattern, count=100)
            if keys:
                self._r.delete(*keys)
            if cursor == 0:
                break
