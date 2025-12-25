from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Mapping, Optional
import hashlib
import json
import re

_slug_re = re.compile(r"[^a-z0-9]+")


def _slug(s: str, maxlen: int = 24) -> str:
    s = s.lower()
    s = _slug_re.sub("-", s).strip("-")
    return s[:maxlen] or "x"


def _stable_hash(obj: Any, n: int = 12) -> str:
    """Short, stable hex for arbitrary JSON-serializable objects."""
    b = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha1(b).hexdigest()[:n]


@dataclass(frozen=True)
class KeyBuilder:
    """
    Helper for building structured cache keys, e.g.:

      f40:v1:dev:tenant:acme:app:auth:feature:sessions:user:123:q=abc123
    """

    prefix: str = "f40"  # project / organization prefix
    version: str = "v1"  # schema/version for mass-busting
    env: str = "dev"  # environment (dev/stage/prod)
    tenant: Optional[str] = None
    app: Optional[str] = None
    feature: Optional[str] = None
    sep: str = ":"  # Redis-friendly

    def with_env(self, env: str) -> "KeyBuilder":
        return replace(self, env=_slug(env))

    def with_tenant(self, tenant_id: str) -> "KeyBuilder":
        return replace(self, tenant=_slug(tenant_id))

    def with_app(self, app_name: str) -> "KeyBuilder":
        return replace(self, app=_slug(app_name))

    def with_feature(self, feature: str) -> "KeyBuilder":
        return replace(self, feature=_slug(feature))

    def base(self) -> str:
        parts = [self.prefix, self.version, self.env]
        if self.tenant:
            parts += ["tenant", self.tenant]
        if self.app:
            parts += ["app", self.app]
        if self.feature:
            parts += ["feature", self.feature]
        return self.sep.join(parts)

    def key(self, *parts: str, params: Optional[Mapping[str, Any]] = None) -> str:
        """
        Build a full key. `parts` are short labels; `params` becomes a short hash.
        """
        head = self.base()
        tail = self.sep.join(_slug(p, 36) for p in parts if p)
        if params:
            qh = _stable_hash(params)
            tail = f"{tail}{self.sep}q={qh}" if tail else f"q={qh}"
        return f"{head}{self.sep}{tail}" if tail else head


def default_builder(
    env: str, tenant: Optional[str] = None, app: Optional[str] = None
) -> KeyBuilder:
    kb = KeyBuilder().with_env(env)
    if tenant:
        kb = kb.with_tenant(tenant)
    if app:
        kb = kb.with_app(app)
    return kb
