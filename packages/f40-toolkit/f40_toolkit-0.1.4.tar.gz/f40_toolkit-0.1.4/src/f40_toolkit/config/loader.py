from __future__ import annotations

import copy
import json
import logging
import os
import threading
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from f40_toolkit.common import (
    deep_merge,
    parse_env_value,
    set_path,
    walk_items,
    mask_for_log,
)

try:
    import tomllib
except ImportError:  # pragma: no cover - for safety on older Pythons
    tomllib = None  # type: ignore[assignment]

try:
    import yaml as _yaml  # type: ignore
except ImportError:  # pragma: no cover
    _yaml = None


_DEFAULT_EXTS = (".toml", ".yaml", ".yml", ".json")


class ConfigManager:
    """
    Flexible configuration loader with:

      - Single-file mode (CONFIG_PATH + optional CONFIG_EXTRA)
      - Layered mode (base/shared/projects/project/env)
      - Env overrides with nested syntax (PREFIX_A__B__0__C=value)
      - Optional canonical keys for backwards compatibility

    The exact env prefix and canonical mapping are provided by the caller
    (or defaulted to F40_ and empty canonical_map).
    """

    def __init__(
        self,
        *,
        env_prefix: Optional[str] = None,
        default_config_dir: Optional[Path] = None,
        canonical_keys: Optional[Mapping[str, Sequence[str]]] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        # Prefix for env-based config values (e.g. F40_)
        self._env_prefix = env_prefix or os.getenv("F40_CONFIG_PREFIX", "F40_")

        # Derived env variable names
        self._config_path_env = f"{self._env_prefix}CONFIG_PATH"
        self._extra_paths_env = f"{self._env_prefix}CONFIG_EXTRA"
        self._config_dir_env = f"{self._env_prefix}CONFIG_DIR"
        self._project_env = f"{self._env_prefix}PROJECT"
        self._stage_env = f"{self._env_prefix}ENV"

        # Root config dir used in layered mode (if CONFIG_DIR env not set)
        self._default_config_dir = default_config_dir or (Path.cwd() / "configs")

        self._canonical_keys: Dict[str, Sequence[str]] = dict(canonical_keys or {})

        self._logger = logger or logging.getLogger("f40.config")

        self._lock = threading.RLock()
        self._config_data: Dict[str, Any] = {}
        self._loaded_files: List[str] = []

    # -------- public API --------

    def reload(self) -> None:
        """
        Reload configuration from disk + env overrides.
        Logs a masked snapshot and a change summary (added/changed/removed keys).
        """
        with self._lock:
            self._logger.info("Reloading configuration...")
            prev = copy.deepcopy(self._config_data)

            cfg_path = os.getenv(self._config_path_env, "").strip()
            if cfg_path:
                data, loaded = self._load_single_file_mode(cfg_path)
            else:
                data, loaded = self._load_layered_mode()

            data = self._apply_env_overrides(data)

            self._config_data = data
            self._loaded_files = loaded

            self._log_configuration_masked()
            self._log_diff(prev, data)

    def as_dict(self) -> Dict[str, Any]:
        with self._lock:
            return copy.deepcopy(self._config_data)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value using dot-notation ('a.b.c').
        """
        with self._lock:
            return self._get_nested_value(key.split("."), self._config_data, default)

    def loaded_files(self) -> List[str]:
        with self._lock:
            return list(self._loaded_files)

    def set_canonical_keys(self, mapping: Mapping[str, Sequence[str]]) -> None:
        """
        Replace the canonical key map used for get_canonical().
        """
        with self._lock:
            self._canonical_keys = dict(mapping)

    def get_canonical(self, canonical_path: str, default: Any = None) -> Any:
        """
        Resolve a canonical key via alias map (first non-None wins).

        Example mapping:

            canonical_keys = {
                "server.port": ["server.backend_port", "server_settings.port"],
                "security.restricted_access": [
                    "api.restricted_access",
                    "restricted_access",
                    "server_settings.restricted_access",
                ],
            }

        Then:

            cfg.get_canonical("server.port")
        """
        with self._lock:
            candidates = [canonical_path] + list(
                self._canonical_keys.get(canonical_path, [])
            )
            for p in candidates:
                val = self._get_nested_value(p.split("."), self._config_data, None)
                if val is not None:
                    return val
        return default

    # -------- internals: load modes --------

    def _load_single_file_mode(self, cfg_path: str) -> Tuple[Dict[str, Any], List[str]]:
        """
        Legacy/monolithic mode: exact file + optional extra files from CONFIG_EXTRA.
        """
        path = Path(cfg_path)
        data = self._load_file_required(path)
        loaded = [str(path.resolve())]

        extra_raw = os.getenv(self._extra_paths_env, "").strip()
        if extra_raw:
            for p in [s for s in extra_raw.split(";") if s]:
                q = Path(p)
                if q.is_file():
                    extra = self._load_file_required(q)
                    data = deep_merge(data, extra)
                    loaded.append(str(q.resolve()))
                else:
                    self._logger.warning(f"Extra config file not found: {p}")

        return data, loaded

    def _load_layered_mode(self) -> Tuple[Dict[str, Any], List[str]]:
        """
        Layered load: base, shared, project/common, project/env + extras.

        Layout (customizable via CONFIG_DIR, PROJECT, ENV):

            <root>/base/default.*
            <root>/base/logging.*
            <root>/base/tracing.*
            <root>/shared/endpoints_permissions.*
            <root>/projects/<PROJECT>/common.*
            <root>/projects/<PROJECT>/<ENV>.*

        Plus any extra files from CONFIG_EXTRA, appended last.
        """
        root = Path(os.getenv(self._config_dir_env) or self._default_config_dir)
        project = os.getenv(self._project_env, "default").strip() or "default"
        stage = os.getenv(self._stage_env, "dev").strip() or "dev"

        candidates = [
            root / "base" / "default",
            root / "base" / "logging",
            root / "base" / "tracing",
            root / "shared" / "endpoints_permissions",
            root / "projects" / project / "common",
            root / "projects" / project / stage,
        ]

        files: List[Path] = []
        for p in candidates:
            chosen = self._first_existing_with_exts(p)
            if chosen:
                files.append(chosen)

        extra_raw = os.getenv(self._extra_paths_env, "").strip()
        if extra_raw:
            for p in [s for s in extra_raw.split(";") if s]:
                q = Path(p)
                if q.exists():
                    files.append(q)
                else:
                    self._logger.warning(f"Extra config file not found: {p}")

        data: Dict[str, Any] = {}
        loaded: List[str] = []
        for f in files:
            try:
                part = self._load_file_required(f)
                data = deep_merge(data, part)
                loaded.append(str(f.resolve()))
            except Exception as e:
                self._logger.critical(f"Error loading config file {f}: {e}")
                raise

        if not loaded:
            self._logger.warning(
                f"No layered config files found under {root} for project={project}, env={stage}"
            )

        return data, loaded

    # -------- file helpers --------

    def _first_existing_with_exts(self, stem: Path) -> Optional[Path]:
        """
        Return the first existing path among stem + supported extensions.
        """
        if stem.suffix:  # already has an extension
            return stem if stem.exists() else None
        for ext in _DEFAULT_EXTS:
            p = stem.with_suffix(ext)
            if p.exists():
                return p
        return None

    def _load_file_required(self, path: Path) -> Dict[str, Any]:
        if not path.is_file():
            raise FileNotFoundError(f"Config file {path} not found.")
        sfx = path.suffix.lower()
        text = path.read_text(encoding="utf-8")
        try:
            if sfx == ".json":
                return json.loads(text)
            if sfx == ".toml":
                if not tomllib:
                    raise RuntimeError("tomllib not available to read TOML")
                return tomllib.loads(text)
            if sfx in (".yaml", ".yml"):
                if not _yaml:
                    raise RuntimeError("pyyaml not available to read YAML")
                return _yaml.safe_load(text) or {}
        except Exception as e:
            self._logger.critical(f"Error parsing config file {path}: {e}")
            raise
        raise ValueError(f"Unsupported config format for {path}")

    # -------- env overrides --------

    def _apply_env_overrides(self, data: dict) -> dict:
        """
        Apply deep overrides from environment variables.

        Patterns:
          - top-level: PREFIX_FOO=value  (if 'foo' is a top-level key)
          - nested:    PREFIX_A__B__0__C=value  (lists supported via numeric parts)
        """
        self._logger.info("Applying environment overrides...")
        result = copy.deepcopy(data)

        # 1) top-level overrides only if key already exists
        for top_key in list(result.keys()):
            env_key = f"{self._env_prefix}{top_key.upper()}"
            if env_key in os.environ:
                val = parse_env_value(os.environ[env_key])
                self._logger.info(f"Override top-level '{top_key}' via {env_key}")
                result[top_key] = val

        # 2) nested overrides with __
        for env, raw in os.environ.items():
            if not env.startswith(self._env_prefix):
                continue
            if env in (
                self._config_path_env,
                self._extra_paths_env,
                self._config_dir_env,
                self._project_env,
                self._stage_env,
            ):
                continue
            suffix = env[len(self._env_prefix) :]
            if "__" not in suffix:
                continue
            parts = [p for p in suffix.split("__") if p]
            if not parts:
                continue
            path = [p.lower() for p in parts]
            try:
                val = parse_env_value(raw)
                set_path(result, path, val)
                self._logger.info(f"Override '{'.'.join(path)}' from env {env}")
            except Exception as e:
                self._logger.warning(f"Failed to apply env override {env}: {e}")

        return result

    # -------- logging & utils --------

    def _get_nested_value(self, keys: List[str], cfg: dict, default: Any) -> Any:
        cur: Any = cfg
        for k in keys:
            if isinstance(cur, dict) and k in cur:
                cur = cur[k]
            else:
                self._logger.debug(
                    f"Config key '{'.'.join(keys)}' not found; default={default!r}"
                )
                return default
        return cur

    def _log_configuration_masked(self) -> None:
        masked = mask_for_log(self._config_data)
        self._logger.info("Loaded configuration (masked):")

        def _recurse(d: dict, prefix: str = "") -> None:
            for k, v in d.items():
                fk = f"{prefix}.{k}" if prefix else k
                if isinstance(v, dict):
                    _recurse(v, fk)
                else:
                    self._logger.info(f"{fk}: {v}")

        _recurse(masked)

    def _log_diff(self, old: dict, new: dict) -> None:
        old_flat = dict(walk_items(old))
        new_flat = dict(walk_items(new))
        changes: List[str] = []

        for k, v in new_flat.items():
            if k not in old_flat:
                changes.append(f"+ {k}")
            elif old_flat[k] != v:
                changes.append(f"~ {k}")
        for k in old_flat.keys() - new_flat.keys():
            changes.append(f"- {k}")

        if changes:
            self._logger.info(
                "Config changes since last load:\n  " + "\n  ".join(changes)
            )
        else:
            self._logger.info("No config changes since last load.")
