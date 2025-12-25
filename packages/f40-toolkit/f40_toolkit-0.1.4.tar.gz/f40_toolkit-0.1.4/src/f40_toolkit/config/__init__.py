# # src/f40_toolkit/config/__init__.py
from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Mapping, Optional, Sequence

from .loader import ConfigManager

__all__ = ["ConfigManager", "configure_global_config", "get_config"]

_global_config: Optional[ConfigManager] = None
_global_lock = threading.RLock()


def configure_global_config(
    *,
    env_prefix: Optional[str] = None,
    default_config_dir: Optional[Path] = None,
    canonical_keys: Optional[Mapping[str, Sequence[str]]] = None,
    logger: Optional[logging.Logger] = None,
) -> ConfigManager:
    """
    Initialize and reload the process-global ConfigManager.

    Typical usage in a service:

        from f40_toolkit.config import configure_global_config
        from .canonical_keys import CANONICAL_KEYS

        configure_global_config(canonical_keys=CANONICAL_KEYS)
    """
    global _global_config
    with _global_lock:
        cfg = ConfigManager(
            env_prefix=env_prefix,
            default_config_dir=default_config_dir,
            canonical_keys=canonical_keys,
            logger=logger,
        )
        cfg.reload()
        _global_config = cfg
        return cfg


def get_config() -> ConfigManager:
    """
    Return the process-global ConfigManager, creating it lazily if needed.
    Uses defaults (env_prefix from F40_CONFIG_PREFIX, cwd()/configs as root).
    """
    global _global_config
    with _global_lock:
        if _global_config is None:
            _global_config = ConfigManager()
            _global_config.reload()
        return _global_config
