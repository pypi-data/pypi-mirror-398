from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


DEFAULT_CONFIG: Dict[str, Any] = {
    "base_logger_name": "f40",
    "logs_path": "./logs",
    "log_file_name": "app.log",
    "rotate": {"max_bytes": 10_000_000, "backup_count": 5},
    # per-channel defaults; you can define any channels you want
    "channels": {
        "default": {"level": "INFO", "file_per_logger": False, "subdir": None},
        "service": {"level": "DEBUG", "file_per_logger": True, "subdir": "services"},
    },
    "console": {
        "enabled": True,
        "level": "INFO",
    },
}


@dataclass
class LoggingConfig:
    base_logger_name: str = "f40"
    logs_path: str = "./logs"
    log_file_name: str = "app.log"
    rotate_max_bytes: int = 10_000_000
    rotate_backup_count: int = 5
    console_enabled: bool = True
    console_level: str = "INFO"
    channels: Dict[str, Dict[str, Any]] = field(default_factory=dict)


def _merge_dict(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            merged[k] = _merge_dict(base[k], v)
        else:
            merged[k] = v
    return merged


def load_logging_config(
    *, config_dict: Optional[Dict[str, Any]] = None, config_file: Optional[str] = None
) -> LoggingConfig:
    """
    Load logging config from (in order of precedence):

    1. config_dict passed explicitly
    2. JSON file (path passed explicitly OR via env F40_LOGGING_CONFIG_FILE)
    3. built-in DEFAULT_CONFIG
    """
    if config_dict is not None:
        raw = _merge_dict(DEFAULT_CONFIG, config_dict)
    else:
        path = config_file or os.getenv("F40_LOGGING_CONFIG_FILE")
        if path and os.path.isfile(path):
            with open(path, "r") as f:
                file_conf = json.load(f)
            raw = _merge_dict(DEFAULT_CONFIG, file_conf)
        else:
            raw = dict(DEFAULT_CONFIG)

    return LoggingConfig(
        base_logger_name=raw["base_logger_name"],
        logs_path=raw["logs_path"],
        log_file_name=raw["log_file_name"],
        rotate_max_bytes=raw["rotate"]["max_bytes"],
        rotate_backup_count=raw["rotate"]["backup_count"],
        console_enabled=raw["console"]["enabled"],
        console_level=raw["console"]["level"],
        channels=raw.get("channels", {}),
    )
