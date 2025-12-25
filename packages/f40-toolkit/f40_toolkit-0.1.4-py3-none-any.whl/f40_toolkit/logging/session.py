from __future__ import annotations


from f40_toolkit.common import ContextLoggerAdapter
from .core import get_logger


def get_session_logger(
    name: str,
    session_id: str,
    *,
    channel: str = "default",
) -> ContextLoggerAdapter:
    """
    Convenience helper: get a logger that always logs with a session_id.
    """
    base = get_logger(name, channel=channel)
    return ContextLoggerAdapter(base, {"session_id": session_id})
