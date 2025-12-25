from __future__ import annotations

from typing import Any, Dict, Iterable, Mapping, Sequence, Set

from .dicts import walk_items

REDACT_SUBSTRINGS = (
    "password",
    "secret",
    "token",
    "apikey",
    "api_key",
    "private",
    "certificate",
    "cookie",
    "key",
)


def is_sensitive_key(key: str) -> bool:
    lk = key.lower()
    return any(sub in lk for sub in REDACT_SUBSTRINGS)


def redact_value(value: Any) -> Any:
    if isinstance(value, str):
        return "*****" if value else value
    if isinstance(value, (dict, list, tuple)):
        return "*****"
    return "*****"


def mask_for_log(d: Dict[str, Any]) -> Dict[str, Any]:
    masked = {}
    for k, v in walk_items(d):
        last = k.split(".")[-1]
        masked[k] = redact_value(v) if is_sensitive_key(last) else v

    out: Dict[str, Any] = {}
    for dotted, v in masked.items():
        parts = dotted.split(".") if dotted else []
        if not parts:
            continue
        cur: Any = out
        for i, p in enumerate(parts):
            is_last = i == len(parts) - 1
            if is_last:
                if isinstance(cur, dict):
                    cur[p] = v
            else:
                nxt = cur.get(p) if isinstance(cur, dict) else None
                if not isinstance(nxt, dict):
                    nxt = {}
                    if isinstance(cur, dict):
                        cur[p] = nxt
                cur = nxt
    return out


def _is_sensitive_key(key: str, sensitive: Set[str]) -> bool:
    lk = key.lower()
    return any(sub in lk for sub in sensitive)


def sanitize_config(
    obj: Any,
    *,
    sensitive_substrings: Iterable[str] = REDACT_SUBSTRINGS,
) -> Any:
    """
    Recursively walk a nested structure (dicts/lists) and replace values whose
    *key* name contains a sensitive substring with "***".
    """
    sensitive = set(sensitive_substrings)

    if isinstance(obj, Mapping):
        out = {}
        for k, v in obj.items():
            kl = str(k).lower()
            if _is_sensitive_key(kl, sensitive):
                out[k] = "***"
            else:
                out[k] = sanitize_config(v, sensitive_substrings=sensitive)
        return out

    if isinstance(obj, Sequence) and not isinstance(obj, (str, bytes, bytearray)):
        return [sanitize_config(v, sensitive_substrings=sensitive) for v in obj]

    return obj
