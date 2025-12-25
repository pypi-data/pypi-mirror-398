# qsg/app/dashboard/utils.py

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Tuple

import pytz
from qsg.core_logger import get_logger

_logger = get_logger(__name__)


def px(n: int) -> str:
    """Return CSS px string from an int."""
    return f"{int(n)}px"


def utc_now_iso() -> str:
    """UTC ISO8601 with timezone info."""
    return datetime.now(timezone.utc).isoformat()


def to_local_str(iso_str: str | None, tz_name: str) -> str:
    """
    Convert an ISO timestamp (with or without 'Z') to a local, human-readable string.

    Never raises – if parsing fails, returns the original string and logs a warning.
    """
    if not iso_str:
        return ""
    try:
        dt = datetime.fromisoformat(str(iso_str).replace("Z", "+00:00"))
        if not dt.tzinfo:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(pytz.timezone(tz_name)).strftime("%Y-%m-%d %H:%M:%S %Z")
    except Exception:
        _logger.warning(
            "Failed to parse or convert ISO string '%s' to timezone '%s'",
            iso_str,
            tz_name,
            exc_info=True,
        )
        return str(iso_str)


def _hex_to_rgb(h: str) -> Tuple[int, int, int]:
    """
    Convert a hex color string (#RRGGBB) to an (R, G, B) tuple.

    We keep this here so constants.py and other modules can share it.
    """
    h = h.lstrip("#")
    try:
        return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))
    except (ValueError, IndexError) as e:
        _logger.error("Failed to convert hex string '%s' to RGB: %s", h, e)
        raise


def get_bool(name: str, default: bool) -> bool:
    """Read a boolean environment variable in a robust way."""
    v = os.getenv(name)
    if v is None:
        _logger.debug(
            "Environment variable '%s' not set, using default value: %s",
            name,
            default,
        )
        return default
    val = str(v).strip().lower() in ("1", "true", "yes", "on")
    _logger.debug("Read env var '%s' as '%s', parsed as boolean: %s", name, v, val)
    return val


def get_int(name: str, default: int) -> int:
    """Read an integer environment variable in a robust way."""
    v = os.getenv(name)
    if v is None:
        _logger.debug(
            "Environment variable '%s' not set, using default value: %s",
            name,
            default,
        )
        return default
    try:
        val = int(v)
        _logger.debug("Read env var '%s' as '%s', parsed as integer: %s", name, v, val)
        return val
    except (ValueError, TypeError):
        _logger.warning(
            "Failed to parse environment variable '%s' with value '%s' as int, "
            "using default value: %s",
            name,
            v,
            default,
        )
        return default


def tab_version(store, tab: str) -> str:
    """
    Return a monotonic-ish version string for the tab to bust caches on updates.

    If anything goes wrong, returns "0" so cache lookups still work.
    """
    try:
        state = store.state()
        return state.get("tabs", {}).get(tab, {}).get("meta", {}).get("updated_at", "0")
    except Exception:
        return "0"