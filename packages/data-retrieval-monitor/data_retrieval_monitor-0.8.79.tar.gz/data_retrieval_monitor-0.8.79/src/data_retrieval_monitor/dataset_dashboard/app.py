# dataset_dashboard/app.py
"""
Run the dashboard OR clear its cache (same file).

Usage:
  export CACHE_TYPE=FileSystemCache
  export CACHE_DIR=/tmp/dataset_dashboard_cache
  # optional:
  # export CACHE_DEFAULT_TIMEOUT=120
  # export CACHE_THRESHOLD=5000
  # export INGEST_PERIOD_SEC=300

  # clear cache then start:
  python -m dataset_dashboard.app --clear-cache

  # or just start:
  python -m dataset_dashboard.app
"""

from __future__ import annotations

import os
import sys
import shutil
import argparse
import atexit

from dash import Dash
import dash_bootstrap_components as dbc

from .services.injector import InjectorService
from .config import load_config
from .dashboard import DashboardHost
from .inject import register_callbacks, register_ingest_routes
from .library import seed_all_tabs

# central caching (configured via config.py)
from .caching import cache, configure_cache

# we moved fastpaths into components/compute.py
from dataset_dashboard.components import compute as compute_mod


# ---------------------------
# Cache clear (uses cfg)
# ---------------------------

def clear_cache(cfg) -> None:
    """
    Clear persistent cache (FileSystemCache or RedisCache).
    SimpleCache has nothing persistent to clear.
    """
    ctype = (cfg.cache_type or "FileSystemCache").lower()

    if ctype.startswith("filesystem"):
        cache_dir = cfg.cache_dir
        if os.path.isdir(cache_dir):
            try:
                shutil.rmtree(cache_dir)
                print(f"[cache] Cleared FileSystemCache at {cache_dir}")
            except Exception as e:
                print(f"[cache] Failed to clear {cache_dir}: {e}", file=sys.stderr)
        else:
            print(f"[cache] Nothing to clear (no dir): {cache_dir}")
        return

    if ctype.startswith("redis"):
        try:
            import redis  # optional
        except Exception:
            print("[cache] Redis library not installed; skipping clear.", file=sys.stderr)
            return
        try:
            r = redis.Redis.from_url(cfg.cache_redis_url)
            pattern = f"{cfg.cache_key_prefix}*"
            keys = r.keys(pattern)
            if not keys:
                print(f"[cache] No Redis keys with prefix '{cfg.cache_key_prefix}' at {cfg.cache_redis_url}")
                return
            pipe = r.pipeline()
            for k in keys:
                pipe.delete(k)
            pipe.execute()
            print(f"[cache] Cleared {len(keys)} Redis keys at {cfg.cache_redis_url} (prefix '{cfg.cache_key_prefix}')")
        except Exception as e:
            print(f"[cache] Failed to clear Redis keys: {e}", file=sys.stderr)
        return

    if ctype.startswith("simple"):
        print("[cache] SimpleCache has no persistent data; nothing to clear.")
        return

    print(f"[cache] Unrecognized CACHE_TYPE='{cfg.cache_type}'. Nothing cleared.")


# ---------------------------
# CLI / lifecycle
# ---------------------------

def _parse_cli(argv):
    p = argparse.ArgumentParser(description="Run the dataset dashboard or clear its cache.")
    p.add_argument("--host", default=None, help="Bind host (default 127.0.0.1)")
    p.add_argument("--port", default=None, type=int, help="Bind port (default 8090)")
    p.add_argument("--no-seed", action="store_true", help="Do not seed demo data")
    p.add_argument("--seed-count", type=int, default=100, help="How many demo datasets to seed")
    p.add_argument("--clear-cache", action="store_true", help="Clear cache before starting the server")
    return p.parse_args(argv)


def _stop_injector(server):
    inj = getattr(server, "injector_service", None)
    if inj:
        try:
            inj.stop()
        except Exception:
            pass


def create_app(do_seed: bool = True, seed_count: int = 10):
    cfg = load_config()

    app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY], title=cfg.app_title)
    app.config.suppress_callback_exceptions = True

    # Flask-Caching from config.py
    configure_cache(app.server, cfg)

    # Host + layout
    host = DashboardHost(app, cfg)
    app.layout = host.layout

    # Bind store once for cached helpers now living in components/compute.py
    compute_mod.bind_store(host.store)

    # Routes + callbacks
    register_ingest_routes(app.server, host)
    register_callbacks(app, cfg, host)
    seed_count=200
    # Seed demo data
    if do_seed and (seed_count or 0) > 0:
        seed_all_tabs(host, num_per_tab=int(seed_count))

    # Auto-ingestion background service (default 5 minutes; see config.py)
    try:
        # Avoid double-start under Werkzeug reloader
        should_start = (os.environ.get("WERKZEUG_RUN_MAIN") == "true") or not app.debug
        if should_start:
            period = int(getattr(cfg, "ingest_period_sec", 300) or 300)
            injector = InjectorService(cfg=cfg, store=host.store, period_sec=period)
            injector.start()
            app.server.injector_service = injector
    except Exception as _e:
        print(f"[InjectorService] failed to start: {_e}")

    return app, app.server, cfg


def main():
    args = _parse_cli(sys.argv[1:])
    cfg = load_config()

    # Optional clear via flag or env
    if args.clear_cache or os.getenv("CLEAR_CACHE") == "1":
        clear_cache(cfg)

    app, server, _ = create_app(do_seed=not args.no_seed, seed_count=args.seed_count)

    # Stop injector cleanly on exit
    atexit.register(_stop_injector, server)

    host = args.host or "127.0.0.1"
    port = int(args.port or 8020)
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    main()