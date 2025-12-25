from __future__ import annotations

from typing import Any, Dict, Optional
import os

from .errors import CachePrefixError


def _find_env(cfg: Dict[str, Any]) -> Optional[str]:
    env = cfg.get("env") or cfg.get("environment")
    if env:
        return str(env)

    service = cfg.get("service") or cfg.get("app") or {}
    env = service.get("env") or service.get("environment")
    if env:
        return str(env)

    env = os.getenv("APP_ENV")
    if env:
        return env
    return None


def _find_service_name(cfg: Dict[str, Any]) -> Optional[str]:
    service = cfg.get("service") or cfg.get("app") or {}
    name = service.get("name") or service.get("service_name")
    if name:
        return str(name)

    name = cfg.get("service_name") or cfg.get("app_name")
    if name:
        return str(name)

    name = os.getenv("SERVICE_NAME")
    if name:
        return name
    return None


def _find_customer(cfg: Dict[str, Any]) -> str:
    cust = (
        cfg.get("customer")
        or cfg.get("customer_id")
        or cfg.get("tenant")
        or cfg.get("tenant_id")
    )
    if isinstance(cust, str) and cust:
        return cust

    service = cfg.get("service") or cfg.get("app") or {}
    cust = (
        service.get("customer")
        or service.get("customer_id")
        or service.get("tenant")
        or service.get("tenant_id")
    )
    if isinstance(cust, str) and cust:
        return cust

    cust = os.getenv("CUSTOMER_ID")
    if isinstance(cust, str) and cust:
        return cust

    return "shared"


def build_cache_prefix_from_config(
    cfg: Dict[str, Any],
    *,
    kind: str = "cache",
) -> str:
    env = _find_env(cfg)
    if not env:
        raise CachePrefixError(
            "Could not determine environment for cache prefix.\n"
            "Looked for 'env'/'environment' at top-level or under 'service'/'app', "
            "and APP_ENV env var."
        )

    service = _find_service_name(cfg)
    if not service:
        raise CachePrefixError(
            "Could not determine service name for cache prefix.\n"
            "Looked for 'service.name'/'service.service_name', 'service_name', 'app_name', "
            "and SERVICE_NAME env var."
        )

    customer = _find_customer(cfg)
    kind = kind or "cache"

    prefix = f"{env}:{customer}:{service}:{kind}:"
    if prefix.count(":") < 3:
        raise CachePrefixError(
            f"Computed cache prefix {prefix!r} looks unsafe. "
            "Expected format '<env>:<customer>:<service>:<kind>:'"
        )

    return prefix
