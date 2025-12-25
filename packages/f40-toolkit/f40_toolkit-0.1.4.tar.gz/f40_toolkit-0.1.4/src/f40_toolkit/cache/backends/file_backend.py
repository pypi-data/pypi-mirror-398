from __future__ import annotations

import io
import os
import threading
import time
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

import logging

from f40_toolkit.common.fs import read_json_safe, atomic_write_json
from f40_toolkit.cache.interfaces import CacheBackend, Serializer
from f40_toolkit.cache.serializers import JsonSerializer

try:
    # Integrate with f40 logging if available
    from f40_toolkit.logging import get_logger  # type: ignore

    main_logger = get_logger("cache.file", channel="default")
except Exception:  # pragma: no cover - fallback
    main_logger = logging.getLogger("f40.cache.file")


class FileCacheBackend(CacheBackend):
    """
    Simple file-based cache:

    - index.json holds metadata (expiries)
    - cache.blob holds hex-encoded serialized values keyed by cache key
    - Writes are atomic via os.replace to survive crashes.
    - Thread-safe via RLock.

    Multi-process friendly *enough* for dev / low-contention usage, but not
    intended for high-concurrency multi-process production workloads.
    """

    def __init__(
        self,
        cache_dir: str | os.PathLike[str],
        default_timeout: int = 300,
        serializer: Optional[Serializer] = None,
    ):
        self.cache_dir = str(Path(cache_dir).resolve())
        self.default_timeout = default_timeout
        self.serializer = serializer or JsonSerializer()

        self._idx_path = str(Path(self.cache_dir) / "index.json")
        self._blob_path = str(Path(self.cache_dir) / "cache.blob")
        self._lock = threading.RLock()

        os.makedirs(self.cache_dir, exist_ok=True)
        if not os.path.exists(self._idx_path):
            atomic_write_json(self._idx_path, {})
        if not os.path.exists(self._blob_path):
            atomic_write_json(self._blob_path, {})

        main_logger.info(
            "FileCacheBackend initialized cache_dir=%s idx=%s blob=%s",
            self.cache_dir,
            self._idx_path,
            self._blob_path,
        )

    # ---- helpers ----
    @staticmethod
    def _now() -> float:
        return time.time()

    # ---- backend API ----
    def get(self, key: str) -> Any:
        with self._lock:
            idx: Dict[str, Any] = read_json_safe(self._idx_path)
            meta = idx.get(key)
            if not meta:
                raise KeyError(key)

            exp = meta.get("exp")  # None => no expiry
            if exp is not None and self._now() > float(exp):
                self.invalidate(key)
                raise KeyError(key)

            blob: Dict[str, Any] = read_json_safe(self._blob_path)
            raw = blob.get(key)
            if raw is None:
                self.invalidate(key)
                raise KeyError(key)

            try:
                data = bytes.fromhex(raw)
            except Exception as e:
                main_logger.warning(
                    "FileCacheBackend: invalid hex payload for key=%s: %s", key, e
                )
                self.invalidate(key)
                raise KeyError(key)

            return self.serializer.loads(data)

    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> None:
        with self._lock:
            idx: Dict[str, Any] = read_json_safe(self._idx_path)
            blob: Dict[str, Any] = read_json_safe(self._blob_path)

            ttl = self.default_timeout if timeout is None else timeout
            exp = None if (ttl is None or ttl <= 0) else self._now() + ttl

            data = self.serializer.dumps(value).hex()
            idx[key] = {"exp": exp}
            blob[key] = data

            atomic_write_json(self._blob_path, blob)
            atomic_write_json(self._idx_path, idx)

    def invalidate(self, key: str) -> None:
        with self._lock:
            idx: Dict[str, Any] = read_json_safe(self._idx_path)
            blob: Dict[str, Any] = read_json_safe(self._blob_path)

            idx.pop(key, None)
            blob.pop(key, None)

            atomic_write_json(self._blob_path, blob)
            atomic_write_json(self._idx_path, idx)

    def clear(self) -> None:
        with self._lock:
            atomic_write_json(self._blob_path, {})
            atomic_write_json(self._idx_path, {})
