# dataset_dashboard/config.py
"""
Central configuration for the dashboard.

Environment variables you can set (all optional):

App/UI
- APP_TITLE="Dataset Dashboard"
- REFRESH_MS=30000                      # UI auto-refresh in ms

Ingestion
- INGEST_PERIOD_SEC=300                 # auto-ingest every 5 minutes (default 300)

Store (state backend used by DashboardHost/StoreService)
- STORE_BACKEND=json                    # "json" (file-backed) or "memory"
- STORE_PATH=/tmp/dataset_dashboard_cache/store.json
- DEFAULT_OWNER=local

Caching (Flask-Caching)
- CACHE_TYPE=FileSystemCache            # "FileSystemCache" (default), "SimpleCache", or "RedisCache"
- CACHE_DIR=/tmp/dataset_dashboard_cache
- CACHE_DEFAULT_TIMEOUT=120
- CACHE_THRESHOLD=5000
- CACHE_KEY_PREFIX=dashdd:              # for Redis
- CACHE_REDIS_URL=redis://localhost:6379/0

Notes:
- FileSystemCache requires only the Python package `flask-caching` (no OS service).
- RedisCache is optional and requires a running Redis + `redis` Python package.
"""

from __future__ import annotations
from dataclasses import dataclass
from types import SimpleNamespace
import os
from pathlib import Path


def _default_cache_dir() -> str:
    return os.getenv("CACHE_DIR", "/tmp/dataset_dashboard_cache")


def _default_store_path() -> str:
    # put the store.json under the cache directory by default
    cache_dir = _default_cache_dir()
    Path(cache_dir).mkdir(parents=True, exist_ok=True)
    return str(Path(cache_dir) / "store.json")


@dataclass(frozen=True)
class AppConfig:
    # --- App/UI ---
    app_title: str = os.getenv("APP_TITLE", "Dataset Dashboard")
    refresh_ms: int = int(os.getenv("REFRESH_MS", "300000"))

    # --- Ingestion (default 5 minutes) ---
    ingest_period_sec: int = int(os.getenv("INGEST_PERIOD_SEC", "300"))

    # --- Store backend expected by DashboardHost/StoreService ---
    # "json" (persist to file) or "memory" (ephemeral)
    store_backend: str = os.getenv("STORE_BACKEND", "json")
    store_path: str = os.getenv("STORE_PATH", _default_store_path())
    default_owner: str = os.getenv("DEFAULT_OWNER", "local")
    log_root: str = os.getenv("LOG_ROOT", "/tmp/log_root")
     # width for KPI tiles (pixels)
    max_kpi_width: int = int(os.getenv("MAX_KPI_WIDTH", "720"))
    # show per-chunk clipboard buttons (useful when central selection is removed)
    clipboard_fallback_open: bool = os.getenv("CLIPBOARD_FALLBACK_OPEN", "true").lower() in ("1", "true", "yes")
    max_graph_width: int = int(os.getenv("MAX_GRAPH_WIDTH", "680"))
    max_left_width: int = int(os.getenv("MAX_LEFT_WIDTH", "360"))
    environment_label: str = "DEMO"
    # --- Cache (Flask-Caching) ---
    cache_type: str = os.getenv("CACHE_TYPE", "FileSystemCache")
    cache_dir: str = os.getenv("CACHE_DIR", _default_cache_dir())
    cache_default_timeout: int = int(os.getenv("CACHE_DEFAULT_TIMEOUT", "120"))
    cache_threshold: int = int(os.getenv("CACHE_THRESHOLD", "5000"))
    cache_key_prefix: str = os.getenv("CACHE_KEY_PREFIX", "dashdd:")
    cache_redis_url: str = os.getenv("CACHE_REDIS_URL", "redis://localhost:6379/0")



def load_config() -> AppConfig:
    return AppConfig()


# Process-wide runtime slots (used e.g. by compute.bind_store)
RUNTIME = SimpleNamespace(
    fastpaths_store=None,
)