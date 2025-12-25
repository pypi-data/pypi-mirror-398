from __future__ import annotations

import threading
import time
from typing import Any, Dict, Optional

from f40_toolkit.cache.interfaces import CacheBackend


class MemoryCacheBackend(CacheBackend):
    """
    In-process cache with TTL. Thread-safe (RLock).
    Values are stored directly (no serialization).

    NOTE: This cache is *not* shared across processes; each process
    keeps its own in-memory store.
    """

    def __init__(self, default_timeout: int = 300):
        self.default_timeout = default_timeout
        self._lock = threading.RLock()
        self._data: Dict[str, tuple[float | None, Any]] = {}

    @staticmethod
    def _now() -> float:
        return time.time()

    def get(self, key: str) -> Any:
        with self._lock:
            exp, val = self._data.get(key, (None, None))
            if val is None:
                raise KeyError(key)
            if exp is not None and self._now() > exp:
                self._data.pop(key, None)
                raise KeyError(key)
            return val

    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> None:
        with self._lock:
            ttl = self.default_timeout if timeout is None else timeout
            exp = None if (ttl is None or ttl <= 0) else self._now() + ttl
            self._data[key] = (exp, value)

    def invalidate(self, key: str) -> None:
        with self._lock:
            self._data.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._data.clear()
