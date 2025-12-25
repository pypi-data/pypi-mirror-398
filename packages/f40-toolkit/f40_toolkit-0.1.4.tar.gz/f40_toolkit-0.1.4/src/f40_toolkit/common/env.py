from __future__ import annotations

import json
from typing import Any


def parse_env_value(raw: str) -> Any:
    s = raw.strip()
    low = s.lower()

    if low in ("false", "0", "no", "off"):
        return False
    if low in ("true", "1", "yes", "on"):
        return True
    if low in ("null", "none"):
        return None

    try:
        return json.loads(s)
    except Exception:
        return s
