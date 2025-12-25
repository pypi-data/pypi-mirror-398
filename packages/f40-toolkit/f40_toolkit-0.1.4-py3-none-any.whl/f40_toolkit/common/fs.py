from __future__ import annotations

import io
import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Dict

log = logging.getLogger("f40.common.fs")


def read_json_safe(path: str | os.PathLike[str]) -> Dict[str, Any]:
    """
    Read a JSON file and return a dict.

    - If the file does not exist, returns {}.
    - If the JSON is invalid or not an object, logs a warning and returns {}.
    """
    p = Path(path)
    try:
        with p.open("r", encoding="utf-8") as rf:
            obj: Any = json.load(rf)
        if isinstance(obj, dict):
            return obj
        log.warning(
            "read_json_safe: %s did not contain a JSON object (got %s)",
            p,
            type(obj).__name__,
        )
        return {}
    except FileNotFoundError:
        return {}
    except Exception as e:
        log.warning("read_json_safe: error reading %s: %s", p, e)
        return {}


def atomic_write_json(path: str | os.PathLike[str], data: Dict[str, Any]) -> None:
    """
    Atomically write JSON to `path`:

    - Writes to a temp file in the same directory.
    - fsyncs and then os.replace() over the target path.
    - Best-effort cleanup of temp file.

    Any exception from json.dump / I/O is propagated to the caller.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    fd, tmp_path = tempfile.mkstemp(prefix=".tmp_", dir=str(p.parent))
    try:
        with io.open(fd, "w", encoding="utf-8") as wf:
            json.dump(data, wf, separators=(",", ":"))
            wf.flush()
            os.fsync(wf.fileno())
        os.replace(tmp_path, p)  # atomic on POSIX/NTFS
    finally:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            # best-effort cleanup; ignore
            pass
