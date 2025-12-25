from __future__ import annotations

import copy
from typing import Any, Iterable, List, Tuple, Union


def deep_merge(base: dict, override: dict) -> dict:
    """
    Deep merge: returns a NEW dict; keys in `override` win.
    Dicts are merged recursively, other types (incl. lists) are replaced.
    """
    result = copy.deepcopy(base)
    for k, v in (override or {}).items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = deep_merge(result[k], v)
        else:
            result[k] = copy.deepcopy(v)
    return result


def set_path(d: Union[dict, list], path: List[str], value: Any) -> None:
    """
    Set nested value. Supports list indexes when component is an int string.
    """
    cur = d
    for i, part in enumerate(path):
        is_last = i == len(path) - 1
        idx: Union[int, None] = None

        if isinstance(cur, list):
            try:
                idx = int(part)
            except ValueError:
                raise KeyError(f"List index expected at {'.'.join(path[:i+1])}")

        if idx is not None:
            while idx >= len(cur):
                cur.append({})
            if is_last:
                cur[idx] = value
            else:
                if not isinstance(cur[idx], (dict, list)):
                    cur[idx] = {}
                cur = cur[idx]
        else:
            if is_last:
                if isinstance(cur, dict):
                    cur[part] = value
                else:
                    raise KeyError(
                        f"Cannot set key on non-dict at {'.'.join(path[:i])}"
                    )
            else:
                if not isinstance(cur, dict):
                    raise KeyError(
                        f"Cannot descend into non-dict at {'.'.join(path[:i])}"
                    )
                nxt = cur.get(part)
                if not isinstance(nxt, (dict, list)):
                    nxt = {}
                    cur[part] = nxt
                cur = nxt


def walk_items(d: Any, base_key: str = "") -> Iterable[Tuple[str, Any]]:
    """
    Yield (dotted_path, value) for all leaves in a nested dict/list structure.
    """
    if isinstance(d, dict):
        for k, v in d.items():
            nk = f"{base_key}.{k}" if base_key else k
            yield from walk_items(v, nk)
    elif isinstance(d, list):
        for i, v in enumerate(d):
            nk = f"{base_key}.{i}" if base_key else str(i)
            yield from walk_items(v, nk)
    else:
        yield base_key, d
