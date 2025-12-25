from __future__ import annotations

import logging
import os
import sys
import threading
from logging.handlers import RotatingFileHandler
from typing import Any, Dict, Optional, Tuple

from f40_toolkit.common import ContextFormatter
from .config import LoggingConfig, load_logging_config

_main_logger: Optional[logging.Logger] = None
_config: Optional[LoggingConfig] = None
_logger_cache: Dict[Tuple[str, str], logging.Logger] = {}
_lock = threading.Lock()


def configure_logging(
    *,
    config: Optional[LoggingConfig] = None,
    config_dict: Optional[Dict[str, Any]] = None,
    config_file: Optional[str] = None,
) -> None:
    """
    Configure the global logging setup for f40-toolkit.

    You can:
      - pass a LoggingConfig object directly,
      - OR pass a config_dict / config_file (JSON),
      - OR let it fall back to DEFAULT_CONFIG & env F40_LOGGING_CONFIG_FILE.
    """
    global _main_logger, _config, _logger_cache

    with _lock:
        _config = config or load_logging_config(
            config_dict=config_dict, config_file=config_file
        )

        # clear previous cache if reconfiguring
        _logger_cache = {}

        os.makedirs(_config.logs_path, exist_ok=True)

        # Base formatter; includes session_id but it's optional
        formatter = ContextFormatter(
            "%(asctime)s.%(msecs)03d | %(levelname)-8s | "
            "%(processName)s/%(threadName)s | %(name)s | "
            "%(funcName)s %(filename)s:%(lineno)d | session=%(session_id)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            defaults={"session_id": "-"},
        )

        # Base logger
        main_logger = logging.getLogger(_config.base_logger_name)
        main_logger.setLevel(logging.DEBUG)  # base; channels refine

        # Remove any old handlers if reconfiguring
        main_logger.handlers.clear()
        main_logger.propagate = False

        # Console handler
        if _config.console_enabled:
            stream_handler = logging.StreamHandler(sys.stdout)
            stream_handler.setLevel(_config.console_level.upper())
            stream_handler.setFormatter(formatter)
            main_logger.addHandler(stream_handler)

        # Optional main file handler
        file_handler = RotatingFileHandler(
            filename=os.path.join(_config.logs_path, _config.log_file_name),
            maxBytes=_config.rotate_max_bytes,
            backupCount=_config.rotate_backup_count,
        )
        file_handler.setFormatter(formatter)
        main_logger.addHandler(file_handler)

        _main_logger = main_logger


def _ensure_configured() -> None:
    if _config is None or _main_logger is None:
        # lazy default config if user didn't call configure_logging explicitly
        configure_logging()


def get_logger(name: str, *, channel: str = "default") -> logging.Logger:
    """
    Return a logger configured according to the given channel.

    Channels are defined in LoggingConfig.channels. Example config:

        "channels": {
            "default": {"level": "INFO", "file_per_logger": False, "subdir": null},
            "service": {"level": "DEBUG", "file_per_logger": True, "subdir": "services"}
        }

    - `file_per_logger` creates a dedicated rotating file for each logger.
    - `subdir` (optional) places logs under logs_path/subdir.
    """
    _ensure_configured()
    assert _config is not None and _main_logger is not None

    with _lock:
        key = (name, channel)
        if key in _logger_cache:
            return _logger_cache[key]

        channel_conf = _config.channels.get(
            channel, _config.channels.get("default", {})
        )
        level = channel_conf.get("level", "INFO").upper()
        file_per_logger = bool(channel_conf.get("file_per_logger", False))
        subdir = channel_conf.get("subdir")

        full_name = f"{_config.base_logger_name}.{name}"
        logger = logging.getLogger(full_name)
        logger.setLevel(getattr(logging, level, logging.INFO))
        logger.propagate = True  # inherit handlers from base

        if file_per_logger:
            # build a dedicated file handler
            base_path = _config.logs_path
            if subdir:
                base_path = os.path.join(base_path, subdir)
            os.makedirs(base_path, exist_ok=True)

            filename = os.path.join(base_path, f"{name}.log")
            # reuse formatter from base logger
            formatter = (
                _main_logger.handlers[0].formatter if _main_logger.handlers else None
            )

            fh = RotatingFileHandler(
                filename=filename,
                maxBytes=_config.rotate_max_bytes,
                backupCount=_config.rotate_backup_count,
            )
            if formatter is not None:
                fh.setFormatter(formatter)

            # avoid duplicates
            if not any(
                isinstance(h, RotatingFileHandler)
                and getattr(h, "baseFilename", None) == fh.baseFilename
                for h in logger.handlers
            ):
                logger.addHandler(fh)

        _logger_cache[key] = logger
        return logger
