# dataset_dashboard/fastpaths.py
"""
Memoized fast-path helpers backed by Flask-Caching.
Keys are small (tab version, filters, etc), and invalidation happens automatically
whenever the tab's version changes.

Setup:
- In app startup, call:  fastpaths.bind_store(host.store)
- Configure cache via config.py/env:
    export CACHE_TYPE=FileSystemCache
    export CACHE_DIR=/tmp/dataset_dashboard_cache
"""

from __future__ import annotations
from typing import Optional, Tuple

from .caching import cache
from .config import load_config, RUNTIME
from dataset_dashboard.components import compute


def bind_store(store_obj) -> None:
    """Bind the global store once at startup."""
    RUNTIME.fastpaths_store = store_obj


def _state():
    if RUNTIME.fastpaths_store is None:
        raise RuntimeError("fastpaths: store not bound. Call bind_store(host.store) during app init.")
    return RUNTIME.fastpaths_store.state()


# Pull default timeout from config
_DEFAULT_TIMEOUT = load_config().cache_default_timeout


@cache.memoize(timeout=_DEFAULT_TIMEOUT)
def aggregate_counts_cached(version: int, tab: str) -> dict:
    st = _state()
    return compute.aggregate_counts(st, tab)


@cache.memoize(timeout=_DEFAULT_TIMEOUT)
def filtered_stage_counts_cached(version: int, tab: str, owner_sel: Optional[str], stage: str) -> dict:
    st = _state()
    return compute.filtered_stage_counts(st, owner_sel, stage, tab)


@cache.memoize(timeout=_DEFAULT_TIMEOUT)
def filtered_sorted_entries_cached(
    version: int,
    tab: str,
    owner_sel: Optional[str],
    vis_stages: Tuple[str, ...],
    status_filter: Tuple[str, ...],
    sort_by: str,
) -> list:
    st = _state()
    return compute.filtered_sorted_entries(
        st,
        owner_sel,
        list(vis_stages or ()),
        list(status_filter or ()),
        tab,
        sort_by,
    )