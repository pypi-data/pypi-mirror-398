# f40-toolkit

Shared configuration, logging, caching, and common utilities used across 40F services.

This repository is structured as a standard Python package (`src/` layout) and is intended to be consumed by multiple internal projects. The documentation is designed to be usable directly from the repository (Bitbucket renders Markdown), and can optionally be served locally as a browsable site.

## Requirements

- Python **3.12+** (`requires-python = ">=3.12"`)

## Installation

Core package (minimal dependencies):

```bash
pip install f40-toolkit
```

Optional features (extras):

```bash
# Cache extras (memory/file backends only; no additional dependencies)
pip install f40-toolkit[cache]

# Cache + Redis backend (pulls redis>=5)
pip install f40-toolkit[cache-redis]

# YAML support for config loading (pulls pyyaml>=6)
pip install f40-toolkit[config]

# Convenience install of all optional features
pip install f40-toolkit[all]
```

## What’s included

- `f40_toolkit.cache` — Cache manager + backends (memory, file, redis), key builder, health check, and basic observability hooks.
- `f40_toolkit.config` — Configuration loading helpers (including optional YAML support).
- `f40_toolkit.logging` — Structured logging configuration and session helpers.
- `f40_toolkit.common` — Small reusable utilities (env, dict helpers, redaction, filesystem helpers, etc.).

## Quickstart

### Cache (recommended entry point)

Create a cache from a simple config dict:

```python
from f40_toolkit.cache import create_cache_from_config, InvalidCacheValue

cfg = {
    "env": "prod",
    "service": {"name": "billing"},
    "customer": "acme",
    "cache": {
        "backend": "memory",          # "file" | "memory" | "redis"
        "default_timeout": 300,       # seconds
        "serializer": "json",         # currently: "json"
        # For file backend only:
        # "path": ".cache",
        # For redis backend only:
        # "redis": {"url": "redis://localhost:6379/0"}
    },
}

cache = create_cache_from_config(cfg)

cache.set("example", {"ok": True}, timeout=60)

try:
    value = cache.get("example")
except InvalidCacheValue:
    value = None

print(value)
```

Memoization helper:

```python
def expensive(a: int, b: int) -> int:
    return a + b

value = cache.get_or_set(
    key="sum:1:2",
    func=expensive,
    f_args=[1, 2],
    timeout=120,
)
print(value)
```

Redis backend (optional):

```python
# pip install f40-toolkit[cache-redis]
from f40_toolkit.cache import create_cache_from_config

cfg = {
    "env": "prod",
    "service": {"name": "billing"},
    "customer": "acme",
    "cache": {
        "backend": "redis",
        "default_timeout": 300,
        "serializer": "json",
        "redis": {
            "url": "redis://localhost:6379/0",
            # Optional explicit prefix override:
            # "prefix": "prod:acme:billing:cache:",
        },
    },
}

cache = create_cache_from_config(cfg)
```

## Local documentation (no hosting required)

Markdown docs can be read directly in Bitbucket once committed.

If you also want a locally served documentation site (recommended for larger docs sets), use **MkDocs**:

1. Add a `docs/` directory with Markdown files (and optionally a `mkdocs.yml` at repo root).
2. Install docs tooling and run a local server:

```bash
pip install -e .[docs]
mkdocs serve
```

Then open the local URL printed by `mkdocs serve` in a browser.

> Note: The `docs` extra is not yet defined in `pyproject.toml` in this repository. If you want MkDocs support, add an extra such as:
>
> ```toml
> [project.optional-dependencies]
> docs = ["mkdocs", "mkdocs-material", "mkdocstrings[python]", "mkdocs-autorefs"]
> ```

## Development

```bash
pip install -e .[dev]
pytest
ruff check .
mypy src
```

Build and check distribution artifacts:

```bash
python -m build
twine check dist/*
```

## License

MIT. See `LICENSE`.
