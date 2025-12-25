from __future__ import annotations

import json
import pickle
from typing import Any

from .interfaces import Serializer


class JsonSerializer(Serializer):
    """Strict JSON (bytes in/out). Values must be JSON-serializable."""

    def dumps(self, value: Any) -> bytes:
        return json.dumps(value, separators=(",", ":")).encode("utf-8")

    def loads(self, data: bytes) -> Any:
        return json.loads(data.decode("utf-8"))


# class PickleSerializer(Serializer):
#     """
#     Binary pickle (bytes in/out).

#     WARNING: Do NOT use with untrusted data.
#     Only enable this explicitly in trusted environments.
#     """

#     def dumps(self, value: Any) -> bytes:
#         return pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)

#     def loads(self, data: bytes) -> Any:
#         return pickle.loads(data)
