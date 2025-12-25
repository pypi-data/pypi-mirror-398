from __future__ import annotations

import logging
from typing import Any, Dict, Optional


class ContextFormatter(logging.Formatter):
    """
    Formatter that safely injects default values for missing attributes.

    Example: ensure every record has session_id and request_id fields, so
    format strings with %(session_id)s won't crash if those aren't set.
    """

    def __init__(
        self,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = None,
        style: str = "%",
        *,
        defaults: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(fmt=fmt, datefmt=datefmt, style=style)
        self._defaults = defaults or {}

    def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
        for key, value in self._defaults.items():
            if not hasattr(record, key):
                setattr(record, key, value)
        return super().format(record)


class ContextLoggerAdapter(logging.LoggerAdapter):
    """
    LoggerAdapter that permanently injects a context dict into all log records.

    Example:

        base = logging.getLogger("my.service")
        log = ContextLoggerAdapter(base, {"session_id": "abc123", "request_id": "rq-1"})
        log.info("Hello")  # record has session_id & request_id
    """

    def process(self, msg: Any, kwargs: Dict[str, Any]):
        extra = kwargs.get("extra", {})
        extra.update(self.extra)
        kwargs["extra"] = extra
        return msg, kwargs
