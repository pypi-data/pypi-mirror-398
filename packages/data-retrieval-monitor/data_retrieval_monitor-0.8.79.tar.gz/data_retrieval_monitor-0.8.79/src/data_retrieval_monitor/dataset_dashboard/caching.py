# dataset_dashboard/caching.py
import typing as _t
from flask_caching import Cache
from .config import AppConfig

cache = Cache()

def configure_cache(flask_app, cfg: AppConfig) -> None:
    """
    Attach Flask-Caching to the Flask server using values from AppConfig.
    """
    # Base config
    flask_app.config.update(
        CACHE_TYPE=cfg.cache_type,
        CACHE_DEFAULT_TIMEOUT=cfg.cache_default_timeout,
    )

    # Backend-specific
    t = (cfg.cache_type or "").lower()
    if t.startswith("filesystem"):
        flask_app.config.update(
            CACHE_DIR=cfg.cache_dir,
            CACHE_THRESHOLD=cfg.cache_threshold,
        )
    elif t.startswith("redis"):
        flask_app.config.update(
            CACHE_REDIS_URL=cfg.cache_redis_url,
            CACHE_KEY_PREFIX=cfg.cache_key_prefix,
        )
    elif t.startswith("simple"):
        flask_app.config.setdefault("CACHE_THRESHOLD", cfg.cache_threshold)

    cache.init_app(flask_app)